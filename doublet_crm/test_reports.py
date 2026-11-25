from datetime import date
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from doublet_crm.reports import (
	MISSING_LOST_REASON,
	_orders_for_period,
	_outcome_deals,
	_pipeline_period,
	_pipeline_rows,
	_previous_period,
	_sales_period,
	_summarize,
	_summarize_lost_reasons,
	_summarize_outcomes,
	_summarize_pipeline,
	get_pipeline_analytics,
	get_sales_performance,
)


def row(**values):
	return frappe._dict(values)


def deal(name, amount, owner=None, creation="2026-10-01 00:00:00", won_on=None, lost_on=None, lost_reason=None, stage="Open", expected_close_date=None, modified="2026-11-01 00:00:00"):
	return row(
		name=name, deal_title=name, amount=amount, deal_owner=owner, creation=creation,
		won_on=won_on, lost_on=lost_on, lost_reason=lost_reason, stage=stage,
		expected_close_date=expected_close_date, modified=modified,
	)


class TestSalesPerformanceReport(FrappeTestCase):
	def test_seeded_cross_month_outcomes_use_event_dates_and_exact_formulas(self):
		won = [
			deal("WON-1", 250, "a@example.com", "2026-10-01", won_on="2026-11-10"),
			deal("WON-2", 150, "a@example.com", "2026-11-01", won_on="2026-11-11"),
		]
		lost = [deal("LOST-1", 75, "b@example.com", "2026-09-01", lost_on="2026-11-12")]

		result = _summarize_outcomes(won, lost)

		self.assertEqual(result["won_count"], 2)
		self.assertEqual(result["lost_count"], 1)
		self.assertEqual(result["won_deal_value"], 400)
		self.assertEqual(result["win_rate"], 66.67)
		self.assertEqual(result["average_close_duration_days"], 25)
		self.assertEqual(result["close_duration_denominator"], 2)

	def test_invalid_won_duration_is_excluded_from_denominator(self):
		result = _summarize_outcomes(
			[deal("VALID", 100, creation="2026-11-01", won_on="2026-11-03"), deal("INVALID", 100, creation="2026-11-05", won_on="2026-11-03")],
			[],
		)
		self.assertEqual(result["average_close_duration_days"], 2)
		self.assertEqual(result["close_duration_denominator"], 1)

	def test_existing_booked_order_summary_stays_exact(self):
		orders = [
			row(name="ORD-1", order_date=date(2026, 11, 1), total=100, deal="DEAL-1"),
			row(name="ORD-2", order_date=date(2026, 11, 1), total=50, deal=None),
			row(name="ORD-3", order_date=date(2026, 11, 2), total=150, deal="DEAL-2"),
		]
		deals = {"DEAL-1": row(deal_owner="owner@example.com"), "DEAL-2": row(deal_owner=None)}
		result = _summarize(orders, deals)
		self.assertEqual((result["booked_sales"], result["order_count"], result["average_order_value"]), (300, 3, 100))
		self.assertEqual(result["trend"][0]["order_count"], 2)

	@patch("doublet_crm.reports.frappe.get_list")
	def test_order_and_outcome_queries_use_their_actual_event_date_filters(self, get_list):
		get_list.return_value = []
		_orders_for_period(date(2026, 11, 1), date(2026, 11, 30))
		_outcome_deals(date(2026, 11, 1), date(2026, 11, 30), "won_on")

		order_call, won_call = get_list.call_args_list
		self.assertIn(["order_date", "between", [date(2026, 11, 1), date(2026, 11, 30)]], order_call.kwargs["filters"])
		self.assertIn(["status", "in", ("Confirmed", "Completed")], order_call.kwargs["filters"])
		self.assertEqual(won_call.kwargs["filters"], [
			["won_on", ">=", "2026-11-01 00:00:00"],
			["won_on", "<", "2026-12-01 00:00:00"],
		])

	@patch("doublet_crm.reports._outcome_deals")
	@patch("doublet_crm.reports._deal_map")
	@patch("doublet_crm.reports._orders_for_period")
	def test_salesperson_filter_keeps_all_readable_owner_options(self, orders_for_period, deal_map, outcome_deals):
		orders_for_period.return_value = [
			row(name="O-A", order_date=date(2026, 11, 1), total=100, deal="D-A"),
			row(name="O-B", order_date=date(2026, 11, 2), total=200, deal="D-B"),
		]
		deal_map.return_value = {
			"D-A": row(name="D-A", deal_owner="a@example.com"),
			"D-B": row(name="D-B", deal_owner="b@example.com"),
		}
		outcome_deals.side_effect = [
			[deal("W-A", 50, "a@example.com", won_on="2026-11-03"), deal("W-C", 75, "c@example.com", won_on="2026-11-04")],
			[deal("L-B", 25, "b@example.com", lost_on="2026-11-05")],
		]

		orders, _deals, summary, won, lost, outcomes, owners = _sales_period(
			date(2026, 11, 1), date(2026, 11, 30), "a@example.com", True,
		)

		self.assertEqual([order.name for order in orders], ["O-A"])
		self.assertEqual([item.name for item in won], ["W-A"])
		self.assertEqual(lost, [])
		self.assertEqual(summary["booked_sales"], 100)
		self.assertEqual(outcomes["won_count"], 1)
		self.assertEqual(owners, {"a@example.com", "b@example.com", "c@example.com"})

	@patch("doublet_crm.reports._sales_period")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_api_keeps_order_and_outcome_drilldowns_permission_scoped(self, has_permission, sales_period):
		has_permission.side_effect = [True, True]
		order = row(name="ORD-1", order_date=date(2026, 11, 3), status="Confirmed", total=125, deal="DEAL-1")
		readable_deal = row(name="DEAL-1", deal_title="Readable", deal_owner="owner@example.com")
		won = [deal("WON-1", 200, "owner@example.com", won_on="2026-11-05")]
		order_summary = _summarize([order], {"DEAL-1": readable_deal})
		sales_period.return_value = ([order], {"DEAL-1": readable_deal}, order_summary, won, [], _summarize_outcomes(won, []), {"owner@example.com"})

		result = get_sales_performance("2026-11-01", "2026-11-30")

		self.assertEqual(result["recent_orders"][0]["deal"], "DEAL-1")
		self.assertEqual(result["won_deals"][0]["name"], "WON-1")
		self.assertEqual(result["employee_breakdown"][0]["won_count"], 1)
		self.assertFalse(result["capabilities"]["team_filter"]["supported"])
		self.assertIn("not paid revenue", result["business_definition"])

	@patch("doublet_crm.reports._sales_period")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_zero_denominators_and_equal_length_comparison(self, has_permission, sales_period):
		has_permission.side_effect = [True, True]
		empty_orders = _summarize([], {})
		empty_outcomes = _summarize_outcomes([], [])
		sales_period.return_value = ([], {}, empty_orders, [], [], empty_outcomes, set())

		result = get_sales_performance("2026-11-01", "2026-11-30", compare_previous=1)

		self.assertEqual(result["win_rate"], 0)
		self.assertIsNone(result["average_close_duration_days"])
		self.assertEqual((result["comparison"]["start_date"], result["comparison"]["end_date"]), ("2026-10-02", "2026-10-31"))
		self.assertEqual(result["comparison"]["metrics"]["won_count"]["change"], 0)

	def test_previous_period_is_inclusive_and_reversed_range_is_rejected(self):
		self.assertEqual(tuple(map(str, _previous_period(date(2026, 11, 1), date(2026, 11, 30)))), ("2026-10-02", "2026-10-31"))
		with patch("doublet_crm.reports.frappe.has_permission", return_value=True):
			with self.assertRaises(frappe.ValidationError):
				get_sales_performance("2026-11-30", "2026-11-01")

	@patch("doublet_crm.reports.frappe.has_permission", side_effect=frappe.PermissionError)
	def test_order_permission_is_required_before_queries(self, _has_permission):
		with self.assertRaises(frappe.PermissionError):
			get_sales_performance("2026-11-01", "2026-11-30")

	@patch("doublet_crm.reports.frappe.get_list")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_restricted_linked_deals_hide_links_and_mark_deal_metrics_unavailable(self, has_permission, get_list):
		has_permission.side_effect = [True, False]
		get_list.return_value = [
			row(name="ORD-1", order_date=date(2026, 11, 3), status="Confirmed", total=125, deal="RESTRICTED")
		]

		result = get_sales_performance("2026-11-01", "2026-11-30")

		self.assertEqual(get_list.call_count, 1)
		self.assertFalse(result["permissions"]["deals"])
		self.assertIsNone(result["won_count"])
		self.assertIsNone(result["win_rate"])
		self.assertIsNone(result["employee_breakdown"][0]["won_count"])
		self.assertIsNone(result["recent_orders"][0]["deal"])
		self.assertTrue(result["recent_orders"][0]["deal_restricted"])


class TestPipelineAnalyticsReport(FrappeTestCase):
	def test_current_stage_summary_remains_creation_cohort_based(self):
		deals = [
			deal("OPEN-1", 100, stage="Prospecting"),
			deal("WON-1", 250, stage="Won", won_on="2026-11-02"),
			deal("LOST-1", 75, stage="Lost", lost_on="2026-11-03"),
		]
		stages = {
			"Prospecting": row(stage_name="Prospecting", stage_type="OPEN", color="#00f", sort_order=1),
			"Won": row(stage_name="Won", stage_type="WON", color="#0f0", sort_order=2),
			"Lost": row(stage_name="Lost", stage_type="LOST", color="#f00", sort_order=3),
		}
		result = _summarize_pipeline(deals, stages)
		self.assertEqual((result["deal_count"], result["total_deal_value"], result["open_pipeline_value"]), (3, 425, 100))
		self.assertEqual(result["lifecycle"]["WON"], {"deal_count": 1, "deal_value": 250})

	def test_lost_reason_counts_values_missing_reason_and_shares_reconcile(self):
		deals = [
			deal("L1", 100, lost_on="2026-11-01", lost_reason="Budget"),
			deal("L2", 50, lost_on="2026-11-02", lost_reason=" Budget "),
			deal("L3", 50, lost_on="2026-11-03", lost_reason=""),
		]
		result = _summarize_lost_reasons(deals)
		budget = next(item for item in result if item["reason"] == "Budget")
		missing = next(item for item in result if item["reason"] == MISSING_LOST_REASON)
		self.assertEqual((budget["deal_count"], budget["deal_value"], budget["count_percentage"], budget["value_percentage"]), (2, 150, 66.67, 75))
		self.assertEqual((missing["deal_count"], missing["deal_value"]), (1, 50))
		self.assertAlmostEqual(sum(item["count_percentage"] for item in result), 100, places=1)
		self.assertEqual({deal_row["name"] for item in result for deal_row in item["deals"]}, {"L1", "L2", "L3"})

	@patch("doublet_crm.reports._pipeline_period")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_api_risk_and_lost_drilldowns_match_aggregates(self, has_permission, pipeline_period):
		has_permission.side_effect = [True, True]
		created = [deal("OPEN", 100)]
		lost = [deal("LOST", 75, lost_on="2026-11-10", lost_reason=None)]
		overdue = [deal("OVERDUE", 80, expected_close_date="2026-11-05")]
		stale = [deal("STALE", 90, modified="2026-09-01")]
		pipeline_period.return_value = {
			"created": created, "lost": lost, "overdue": overdue, "stale": stale,
			"as_of": date(2026, 11, 24), "stale_cutoff": date(2026, 10, 25), "stages": {},
			"owners": {"owner@example.com"}, "summary": _summarize_pipeline(created, {}),
		}

		result = get_pipeline_analytics("2026-11-01", "2026-11-30", compare_previous=1)

		self.assertEqual((result["lost_reason_count"], result["lost_reason_value"]), (1, 75))
		self.assertEqual((result["overdue_open_count"], result["overdue_open_value"]), (1, 80))
		self.assertEqual((result["stale_open_count"], result["stale_open_value"]), (1, 90))
		self.assertEqual(result["lost_reasons"][0]["deals"][0]["name"], "LOST")
		self.assertEqual(result["overdue_deals"][0]["name"], "OVERDUE")
		self.assertIn("on or before the 30-day cutoff date", result["business_definition"])
		self.assertIn("not historical stage snapshots", result["comparison"]["definition"])
		self.assertFalse(result["capabilities"]["team_filter"]["supported"])

	@patch("doublet_crm.reports._get_deals")
	@patch("doublet_crm.reports.nowdate", return_value="2026-11-24")
	def test_pipeline_queries_use_metric_dates_and_include_the_stale_cutoff_day(self, _nowdate, get_deals):
		get_deals.return_value = []

		_pipeline_rows(date(2026, 11, 1), date(2026, 11, 30))

		created_call, lost_call, overdue_call, stale_call = get_deals.call_args_list
		self.assertEqual(created_call.args[0], [
			["creation", ">=", "2026-11-01 00:00:00"],
			["creation", "<", "2026-12-01 00:00:00"],
		])
		self.assertEqual(lost_call.args[0], [
			["lost_on", ">=", "2026-11-01 00:00:00"],
			["lost_on", "<", "2026-12-01 00:00:00"],
		])
		self.assertIn(["expected_close_date", "between", [date(2026, 11, 1), date(2026, 11, 23)]], overdue_call.args[0])
		self.assertIn(["modified", "<=", "2026-10-25 23:59:59.999999"], stale_call.args[0])

	@patch("doublet_crm.reports._pipeline_rows")
	def test_pipeline_owner_options_include_risk_owners_before_selected_filter(self, pipeline_rows):
		pipeline_rows.return_value = (
			[deal("CREATED-A", 1, "a@example.com")],
			[deal("LOST-B", 2, "b@example.com", lost_on="2026-11-02")],
			[deal("OVERDUE-C", 3, "c@example.com", expected_close_date="2026-11-03")],
			[deal("STALE-D", 4, "d@example.com", modified="2026-09-01")],
			date(2026, 11, 24), date(2026, 10, 25),
		)

		period = _pipeline_period(date(2026, 11, 1), date(2026, 11, 30), "a@example.com", False)

		self.assertEqual(period["owners"], {"a@example.com", "b@example.com", "c@example.com", "d@example.com"})
		self.assertEqual([item.name for item in period["created"]], ["CREATED-A"])
		self.assertEqual(period["lost"], [])
		self.assertEqual(period["overdue"], [])
		self.assertEqual(period["stale"], [])

	@patch("doublet_crm.reports._pipeline_rows")
	def test_restricted_stage_metadata_uses_readable_deal_lifecycle_fields(self, pipeline_rows):
		pipeline_rows.return_value = (
			[deal("WON", 150, stage="Private Won Stage", won_on="2026-11-04")],
			[], [], [], date(2026, 11, 24), date(2026, 10, 25),
		)

		period = _pipeline_period(date(2026, 11, 1), date(2026, 11, 30), None, False)

		self.assertEqual(period["stages"], {})
		self.assertEqual(period["summary"]["lifecycle"]["WON"]["deal_count"], 1)
		self.assertEqual(period["summary"]["by_stage"][0]["label"], "Private Won Stage")

	@patch("doublet_crm.reports.frappe.has_permission", side_effect=frappe.PermissionError)
	def test_deal_permission_is_required_before_pipeline_queries(self, _has_permission):
		with self.assertRaises(frappe.PermissionError):
			get_pipeline_analytics("2026-11-01", "2026-11-30")


# ===== Customer Journey Report Tests (REP-06) =====

from doublet_crm.reports import (
	_journey_deals_from_leads,
	_journey_leads,
	_journey_orders_for_deals,
	_journey_orders_for_quotations,
	_journey_period,
	_journey_quotations_for_deals,
	_journey_row,
	_journey_comparison,
	_summarize_journey,
	get_customer_journey,
)


class TestCustomerJourneyReport(FrappeTestCase):
	def test_source_cohort_and_won_rates_use_unique_leads(self):
		leads = [
			row(name="LD-1", lead_name="One", lead_owner="a@example.com", source="Referral", creation="2026-11-01"),
			row(name="LD-2", lead_name="Two", lead_owner="a@example.com", source="Referral", creation="2026-11-02"),
		]
		deals = {"LD-1": [
			row(name="D-1", deal_title="One", amount=100, won_on="2026-11-20"),
			row(name="D-2", deal_title="Two", amount=200, won_on="2026-11-21"),
		]}
		result, contexts = _summarize_journey(leads, deals, {}, {}, {}, {"deals": True, "quotations": True, "orders": True})
		self.assertEqual(result["deal_count"], 1)
		self.assertEqual(result["won_lead_count"], 1)
		self.assertEqual(result["lead_to_won_rate"], 50)
		journey = _journey_row(*contexts[0], permissions={"deals": True, "quotations": True, "orders": True})
		self.assertEqual(journey["source"], "Referral")
		self.assertEqual({item["name"] for item in journey["deals"]}, {"D-1", "D-2"})

	@patch("doublet_crm.reports._journey_deals_from_leads", return_value={})
	@patch("doublet_crm.reports._journey_leads")
	def test_salesperson_filter_consistently_uses_lead_owner(self, journey_leads, deals_from_leads):
		journey_leads.return_value = [
			row(name="LD-A", lead_name="A", lead_owner="a@example.com", creation="2026-11-01"),
			row(name="LD-B", lead_name="B", lead_owner="b@example.com", creation="2026-11-02"),
		]
		result = _journey_period(date(2026, 11, 1), date(2026, 11, 30), "a@example.com", {"deals": True, "quotations": True, "orders": True})
		self.assertEqual([lead.name for lead in result["leads"]], ["LD-A"])
		self.assertEqual([lead.name for lead in deals_from_leads.call_args.args[0]], ["LD-A"])
		self.assertEqual(result["available_owners"], {"a@example.com", "b@example.com"})

	@patch("doublet_crm.reports.frappe.get_list", return_value=[])
	@patch("doublet_crm.reports.frappe.has_permission", return_value=True)
	def test_salesperson_validation_uses_readable_lead_owners(self, _permission, _get_list):
		with self.assertRaises(frappe.ValidationError):
			get_customer_journey("2026-11-01", "2026-11-30", "unknown@example.com")

	def test_funnel_counts_unique_leads_and_entity_totals_without_duplicate_orders(self):
		leads = [
			row(name="LD-1", lead_name="Lead 1", lead_owner="a@example.com", creation="2026-11-01"),
			row(name="LD-2", lead_name="Lead 2", lead_owner="a@example.com", creation="2026-11-02"),
		]
		deals = {"LD-1": [
			row(name="D-1", deal_title="One", amount=100),
			row(name="D-2", deal_title="Two", amount=200),
		]}
		quotations = {
			"D-1": [row(name="Q-1", deal="D-1", status="Sent", grand_total=120)],
			"D-2": [row(name="Q-2", deal="D-2", status="Accepted", grand_total=220)],
		}
		order = row(name="O-1", deal="D-1", quotation="Q-1", status="Confirmed", total=110)
		result, contexts = _summarize_journey(
			leads, deals, quotations, {"Q-1": [order]}, {"D-1": [order]},
			{"deals": True, "quotations": True, "orders": True},
		)
		self.assertEqual((result["lead_count"], result["deal_count"], result["quotation_count"], result["order_count"]), (2, 1, 1, 1))
		self.assertEqual(result["entity_totals"], {"leads": 2, "deals": 2, "quotations": 2, "booked_orders": 1})
		self.assertEqual(len(contexts[0][3]), 1)

	@patch("doublet_crm.reports._journey_deals_from_leads")
	@patch("doublet_crm.reports._journey_leads")
	def test_restricted_sources_are_unavailable_and_not_queried(self, journey_leads, deals_from_leads):
		journey_leads.return_value = [row(name="LD-1", lead_name="Lead", lead_owner=None, creation="2026-11-01")]
		result = _journey_period(date(2026, 11, 1), date(2026, 11, 30), None, {"deals": False, "quotations": False, "orders": False})
		deals_from_leads.assert_not_called()
		self.assertIsNone(result["summary"]["deal_count"])
		self.assertIsNone(result["summary"]["entity_totals"]["deals"])
		self.assertIsNone(result["journey_rows"][0]["has_deal"])

	def test_journey_leads_queries_by_creation_date(self):
		leads = [
			row(name="LD-1", lead_name="Lead 1", lead_owner="a@example.com", creation="2026-11-01 10:00:00", converted_deal=None),
			row(name="LD-2", lead_name="Lead 2", lead_owner="b@example.com", creation="2026-11-15 10:00:00", converted_deal="DEAL-1"),
		]
		with patch("doublet_crm.reports.frappe.get_list", return_value=leads) as get_list:
			result = _journey_leads(date(2026, 11, 1), date(2026, 11, 30))
			self.assertEqual(len(result), 2)
			self.assertEqual([l.name for l in result], ["LD-1", "LD-2"])
			self.assertEqual(get_list.call_args.kwargs["order_by"], "creation desc, name desc")
			self.assertEqual(get_list.call_args.kwargs["filters"][0], ["creation", ">=", "2026-11-01 00:00:00"])

	def test_journey_deals_from_leads_builds_lead_to_deal_map(self):
		leads = [
			row(name="LD-1", converted_deal="DEAL-1"),
			row(name="LD-2", converted_deal=None),
			row(name="LD-3", converted_deal=None),
		]
		deals = [
			row(name="DEAL-1", deal_title="D1", deal_owner="a@example.com", amount=100, creation="2026-11-02", source_lead="LD-1"),
			row(name="DEAL-2", deal_title="D2", deal_owner="b@example.com", amount=200, creation="2026-11-03", source_lead="LD-2"),
		]
		with patch("doublet_crm.reports.frappe.get_list", side_effect=[deals, [deals[0]]]):
			result = _journey_deals_from_leads(leads)
			self.assertIn("LD-1", result)
			self.assertEqual([deal.name for deal in result["LD-1"]], ["DEAL-1"])
			self.assertNotIn("LD-3", result)

	def test_journey_quotations_for_deals_groups_by_deal(self):
		quotations = [
			row(name="Q-1", deal="DEAL-1", status="Sent", grand_total=150, creation="2026-11-05"),
			row(name="Q-2", deal="DEAL-1", status="Accepted", grand_total=180, creation="2026-11-06"),
			row(name="Q-3", deal="DEAL-2", status="Draft", grand_total=50, creation="2026-11-07"),
		]
		with patch("doublet_crm.reports.frappe.get_list", return_value=quotations):
			result = _journey_quotations_for_deals(["DEAL-1", "DEAL-2"])
			self.assertEqual(len(result["DEAL-1"]), 2)
			self.assertEqual(len(result["DEAL-2"]), 1)

	def test_journey_orders_for_deals_filters_by_status(self):
		orders = [
			row(name="ORD-1", deal="DEAL-1", status="Confirmed", total=120, order_date="2026-11-10"),
			row(name="ORD-2", deal="DEAL-1", status="Draft", total=30, order_date="2026-11-11"),
			row(name="ORD-3", deal="DEAL-2", status="Completed", total=250, order_date="2026-11-12"),
		]
		with patch("doublet_crm.reports.frappe.get_list", return_value=orders):
			result = _journey_orders_for_deals(["DEAL-1", "DEAL-2"])
			self.assertEqual(len(result["DEAL-1"]), 2)
			self.assertEqual(len(result["DEAL-2"]), 1)

	def test_journey_row_stages_correctly(self):
		lead = row(name="LD-1", lead_name="Test Lead", lead_owner="a@example.com", creation="2026-11-01")
		deal = row(name="DEAL-1", deal_title="Deal 1", deal_owner="a@example.com", amount=500)
		# Stage: Lead only
		permissions = {"deals": True, "quotations": True, "orders": True}
		result = _journey_row(lead, [], [], [], permissions)
		self.assertEqual(result["stage"], "Lead")
		self.assertFalse(result["has_deal"])
		# Stage: Deal
		result = _journey_row(lead, [deal], [], [], permissions)
		self.assertEqual(result["stage"], "Deal")
		self.assertTrue(result["has_deal"])
		# Stage: Quotation
		quotations = [row(name="Q-1", deal="DEAL-1", status="Sent", grand_total=100)]
		result = _journey_row(lead, [deal], quotations, [], permissions)
		self.assertEqual(result["stage"], "Quotation Sent")
		# Stage: Quotation Accepted
		quotations = [row(name="Q-1", deal="DEAL-1", status="Accepted", grand_total=100)]
		result = _journey_row(lead, [deal], quotations, [], permissions)
		self.assertEqual(result["stage"], "Quotation Accepted")
		# Stage: Order
		orders = [row(name="O-1", deal="DEAL-1", status="Confirmed", total=120)]
		result = _journey_row(lead, [deal], [], orders, permissions)
		self.assertEqual(result["stage"], "Order")

	def test_summarize_journey_builds_funnel_with_unique_counts(self):
		leads = [
			row(name="LD-1", lead_name="Lead 1", lead_owner="a@example.com", creation="2026-11-01"),
			row(name="LD-2", lead_name="Lead 2", lead_owner="a@example.com", creation="2026-11-02"),
		]
		deals_for_leads = {
			"LD-1": [row(name="DEAL-1", deal_title="D1", deal_owner="a@example.com", amount=100)],
			"LD-2": [row(name="DEAL-2", deal_title="D2", deal_owner="a@example.com", amount=200)],
		}
		quotations = {"DEAL-1": [row(name="Q-1", deal="DEAL-1", status="Accepted", grand_total=150)]}
		orders_by_deal = {"DEAL-1": [row(name="O-1", deal="DEAL-1", status="Completed", total=120)]}
		result, _contexts = _summarize_journey(leads, deals_for_leads, quotations, {}, orders_by_deal, {"deals": True, "quotations": True, "orders": True})
		self.assertEqual(result["lead_count"], 2)
		self.assertEqual(result["deal_count"], 2)
		self.assertEqual(result["lead_to_deal_rate"], 100.0)
		self.assertEqual(result["entity_totals"]["deals"], 2)
		self.assertEqual(result["quotation_count"], 1)
		self.assertEqual(result["order_value"], 120)

	def test_journey_comparison_computes_changes(self):
		current = {"lead_count": 10, "deal_count": 5, "lead_value": 500, "lead_to_deal_rate": 50}
		previous = {"lead_count": 8, "deal_count": 2, "lead_value": 200, "lead_to_deal_rate": 25}
		result = _journey_comparison(current, previous)
		self.assertEqual(result["lead_count"]["change"], 2)
		self.assertEqual(result["deal_count"]["change"], 3)
		self.assertEqual(result["lead_value"]["change"], 300)
		self.assertEqual(result["lead_to_deal_rate"]["change"], 25)

	@patch("doublet_crm.reports._journey_period")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_api_returns_permission_scoped_data(self, has_permission, journey_period):
		has_permission.side_effect = [True, True, True, True]
		journey_period.return_value = {
			"leads": [],
			"deals": {},
			"quotations": {},
			"orders_by_deal": {},
			"available_owners": set(),
			"summary": {
				"lead_count": 0, "deal_count": 0, "quotation_count": 0, "order_count": 0,
				"lead_value": 0, "deal_value": 0, "quotation_value": 0, "order_value": 0,
				"lead_to_deal_rate": 0, "deal_to_order_rate": 0,
				"entity_totals": {"leads": 0, "deals": 0, "quotations": 0, "booked_orders": 0},
				"funnel": [{"stage": stage, "count": 0, "value": 0} for stage in ("Lead", "Deal", "Quotation", "Order")], "by_owner": [],
			},
			"journey_rows": [],
		}

		result = get_customer_journey("2026-11-01", "2026-11-30")

		self.assertTrue(result["permissions"]["leads"])
		self.assertTrue(result["permissions"]["deals"])
		self.assertIn("Lead", [s["stage"] for s in result["funnel"]])

	@patch("doublet_crm.reports.frappe.has_permission", side_effect=frappe.PermissionError)
	def test_lead_permission_is_required(self, _has_permission):
		with self.assertRaises(frappe.PermissionError):
			get_customer_journey("2026-11-01", "2026-11-30")


# ===== Quotation & Order Report Tests (REP-04) =====

from doublet_crm.reports import (
	_quotation_order_quotations,
	_quotation_order_deals,
	_quotation_order_orders,
	_quotation_order_conversion_orders,
	_summarize_quotations,
	_summarize_orders,
	_summarize_conversion,
	_quotation_order_period,
	_qo_comparison,
	get_quotation_order,
)


class TestQuotationOrderReport(FrappeTestCase):
	@patch("doublet_crm.reports._quotation_order_quotations")
	@patch("doublet_crm.reports._quotation_order_orders")
	def test_unreadable_quotation_source_is_unavailable_not_zero(self, order_rows, quotation_rows):
		order_rows.return_value = [row(name="O-1", deal=None, quotation=None, status="Completed", total=80, order_date="2026-11-10")]
		result = _quotation_order_period("2026-11-01", "2026-11-30", None, {"quotations": False, "orders": True, "deals": False})
		quotation_rows.assert_not_called()
		self.assertIsNone(result["quotation_summary"])
		self.assertIsNone(result["conversion"])
		self.assertEqual(result["order_summary"]["order_count"], 1)

	def test_orders_are_queried_independently_by_order_date_and_preserve_multiple_rows(self):
		orders = [
			row(name="O-1", deal="D-1", quotation="Q-1", status="Confirmed", total=10, order_date="2026-11-10"),
			row(name="O-2", deal="D-1", quotation="Q-1", status="Completed", total=20, order_date="2026-11-11"),
			row(name="O-3", deal=None, quotation=None, status="Draft", total=30, order_date="2026-11-12"),
		]
		with patch("doublet_crm.reports.frappe.get_list", return_value=orders) as get_list:
			result = _quotation_order_orders("2026-11-01", "2026-11-30")
		self.assertEqual([order.name for order in result], ["O-1", "O-2", "O-3"])
		self.assertEqual(get_list.call_args.kwargs["filters"], [["order_date", ">=", "2026-11-01"], ["order_date", "<=", "2026-11-30"]])

	def test_order_only_period_keeps_standalone_orders_visible(self):
		standalone = row(name="O-1", deal=None, quotation=None, status="Completed", total=80, order_date="2026-11-10")
		with patch("doublet_crm.reports._quotation_order_quotations", return_value=[]), \
			patch("doublet_crm.reports._quotation_order_orders", return_value=[standalone]), \
			patch("doublet_crm.reports._quotation_order_conversion_orders", return_value=[]):
			result = _quotation_order_period("2026-11-01", "2026-11-30", None, {"quotations": True, "orders": True, "deals": True})
		self.assertEqual(result["quotation_summary"]["quotation_count"], 0)
		self.assertEqual(result["order_summary"]["order_count"], 1)
		self.assertEqual(result["order_summary"]["booked_sales"], 80)

	def test_restricted_deal_links_are_not_returned(self):
		quotation = row(name="Q-1", deal="PRIVATE", status="Sent", grand_total=100, quotation_date="2026-11-05")
		order = row(name="O-1", deal="PRIVATE", quotation="Q-1", status="Confirmed", total=100, order_date="2026-11-06")
		q_row = _summarize_quotations([quotation], {})["by_status"][0]["quotations"][0]
		o_row = _summarize_orders([order], {})["by_status"][0]["orders"][0]
		self.assertIsNone(q_row["deal"])
		self.assertTrue(q_row["deal_restricted"])
		self.assertIsNone(o_row["deal"])
		self.assertTrue(o_row["deal_restricted"])

	def test_quotations_queried_by_quotation_date(self):
		quotations = [
			row(name="Q-1", deal="DEAL-1", status="Sent", grand_total=100, quotation_date="2026-11-05", creation="2026-11-01"),
			row(name="Q-2", deal="DEAL-1", status="Accepted", grand_total=200, quotation_date="2026-11-10", creation="2026-11-02"),
		]
		with patch("doublet_crm.reports.frappe.get_list", return_value=quotations) as get_list:
			result = _quotation_order_quotations("2026-11-01", "2026-11-30")
			self.assertEqual(len(result), 2)
			self.assertEqual([q.name for q in result], ["Q-1", "Q-2"])
			self.assertEqual(get_list.call_args.kwargs["filters"], [["quotation_date", ">=", "2026-11-01"], ["quotation_date", "<=", "2026-11-30"]])

	def test_summarize_quotations_groups_by_status(self):
		quotations = [
			row(name="Q-1", deal="DEAL-1", status="Draft", grand_total=50, quotation_date="2026-11-05"),
			row(name="Q-2", deal="DEAL-1", status="Sent", grand_total=100, quotation_date="2026-11-06"),
			row(name="Q-3", deal="DEAL-2", status="Accepted", grand_total=200, quotation_date="2026-11-07"),
			row(name="Q-4", deal="DEAL-2", status="Accepted", grand_total=150, quotation_date="2026-11-08"),
			row(name="Q-5", deal="DEAL-3", status="Rejected", grand_total=25, quotation_date="2026-11-09"),
		]
		deals = {"DEAL-1": row(deal_title="D1", deal_owner="a@example.com"), "DEAL-2": row(deal_title="D2", deal_owner="a@example.com"), "DEAL-3": row(deal_title="D3", deal_owner="b@example.com")}
		result = _summarize_quotations(quotations, deals)
		self.assertEqual(result["quotation_count"], 5)
		self.assertEqual(result["quotation_value"], 525)
		self.assertEqual(result["accepted_count"], 2)
		self.assertEqual(result["acceptance_rate"], 40.0)
		accepted = next(s for s in result["by_status"] if s["status"] == "Accepted")
		self.assertEqual(accepted["count"], 2)
		self.assertEqual(accepted["value"], 350)

	def test_summarize_orders_only_counts_booked(self):
		orders = [
			row(name="O-1", deal="DEAL-1", status="Draft", total=50, order_date="2026-11-05"),
			row(name="O-2", deal="DEAL-1", status="Confirmed", total=100, order_date="2026-11-06"),
			row(name="O-3", deal="DEAL-2", status="Completed", total=200, order_date="2026-11-07"),
			row(name="O-4", deal="DEAL-2", status="Cancelled", total=75, order_date="2026-11-08"),
		]
		deals = {"DEAL-1": row(deal_title="D1", deal_owner="a@example.com"), "DEAL-2": row(deal_title="D2", deal_owner="b@example.com")}
		result = _summarize_orders(orders, deals)
		self.assertEqual(result["order_count"], 4)
		self.assertEqual(result["booked_sales"], 300)
		self.assertEqual(result["booked_order_count"], 2)
		self.assertEqual(result["total_order_value"], 425)
		# Verify Cancelled has 0 booked value
		cancelled = next(s for s in result["by_status"] if s["status"] == "Cancelled")
		self.assertEqual(cancelled["booked_value"], 0)

	def test_conversion_uses_unique_quotation_to_booked_order_links(self):
		quotations = [
			row(name="Q-1", deal="DEAL-1", status="Accepted", grand_total=100),
			row(name="Q-2", deal="DEAL-2", status="Accepted", grand_total=200),
			row(name="Q-3", deal="DEAL-3", status="Sent", grand_total=50),
		]
		orders = [
			row(name="O-1", quotation="Q-1", deal="OTHER-DEAL", status="Confirmed", total=100),
			row(name="O-2", quotation="Q-2", deal="DEAL-2", status="Draft", total=200),
			row(name="O-3", quotation=None, deal="DEAL-3", status="Confirmed", total=50),
		]
		result = _summarize_conversion(quotations, orders)
		self.assertEqual(result["quotations_with_orders"], 1)
		self.assertEqual(result["quotation_value_converted"], 100)
		self.assertEqual(result["quotation_to_order_rate"], 33.33)
		self.assertEqual(result["accepted_quotation_count"], 2)
		self.assertEqual(result["accepted_quotations_with_orders"], 1)
		self.assertEqual(result["accepted_to_booked_order_rate"], 50)
		self.assertEqual(len(result["accepted_conversion_drilldown"][0]["orders"]), 1)

	def test_accepted_conversion_deduplicates_orders_and_excludes_standalone(self):
		quotations = [row(name="Q-1", status="Accepted", grand_total=100, quotation_date="2026-11-01")]
		orders = [
			row(name="O-1", quotation="Q-1", status="Confirmed", total=100, order_date="2026-12-01"),
			row(name="O-2", quotation="Q-1", status="Completed", total=100, order_date="2026-12-02"),
			row(name="O-3", quotation=None, status="Confirmed", total=100, order_date="2026-11-02"),
		]
		result = _summarize_conversion(quotations, orders)
		self.assertEqual(result["accepted_quotations_with_orders"], 1)
		self.assertEqual(result["accepted_to_booked_order_rate"], 100)
		self.assertEqual({item["name"] for item in result["accepted_conversion_drilldown"][0]["orders"]}, {"O-1", "O-2"})

	def test_quotation_order_period_filters_by_salesperson(self):
		quotations = [
			row(name="Q-1", deal="DEAL-1", status="Sent", grand_total=100, quotation_date="2026-11-05"),
			row(name="Q-2", deal="DEAL-2", status="Accepted", grand_total=200, quotation_date="2026-11-06"),
		]
		deals = {"DEAL-1": row(deal_title="D1", deal_owner="a@example.com"), "DEAL-2": row(deal_title="D2", deal_owner="b@example.com")}
		orders = [
			row(name="O-1", deal="DEAL-1", quotation="Q-1", status="Confirmed", total=100, order_date="2026-11-08"),
			row(name="O-2", deal=None, quotation=None, status="Completed", total=50, order_date="2026-11-09"),
		]
		with patch("doublet_crm.reports._quotation_order_quotations", return_value=quotations):
			with patch("doublet_crm.reports._quotation_order_deals", return_value=deals):
				with patch("doublet_crm.reports._quotation_order_orders", return_value=orders):
					with patch("doublet_crm.reports._quotation_order_conversion_orders", return_value=[orders[0]]):
						result = _quotation_order_period("2026-11-01", "2026-11-30", "a@example.com", {"quotations": True, "orders": True, "deals": True})
					# Should only include Q-1 (linked to DEAL-1 owned by a@example.com)
					self.assertEqual(result["quotation_summary"]["quotation_count"], 1)
					self.assertEqual(result["order_summary"]["order_count"], 1)
					self.assertEqual(result["available_owners"], {"a@example.com", "b@example.com"})

	def test_qo_comparison_computes_changes(self):
		current = {"quotation_count": 10, "quotation_value": 500, "accepted_count": 5, "acceptance_rate": 50, "booked_sales": 300}
		previous = {"quotation_count": 8, "quotation_value": 400, "accepted_count": 2, "acceptance_rate": 25, "booked_sales": 200}
		result = _qo_comparison(current, previous)
		self.assertEqual(result["quotation_count"]["change"], 2)
		self.assertEqual(result["quotation_value"]["change"], 100)
		self.assertEqual(result["accepted_count"]["change"], 3)
		self.assertEqual(result["acceptance_rate"]["change"], 25)
		self.assertEqual(result["booked_sales"]["change"], 100)

	@patch("doublet_crm.reports._quotation_order_period")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_api_returns_permission_scoped_data(self, has_permission, qo_period):
		has_permission.side_effect = [True, True, True]
		qo_period.return_value = {
			"quotations": [],
			"orders": [],
			"deals": {},
			"available_owners": set(),
			"quotation_summary": {"quotation_count": 0, "quotation_value": 0, "accepted_count": 0, "acceptance_rate": 0, "by_status": []},
			"order_summary": {"order_count": 0, "booked_sales": 0, "booked_order_count": 0, "by_status": []},
			"conversion": {"quotations_with_orders": 0, "quotation_to_order_rate": 0, "quotation_value_converted": 0},
		}
		result = get_quotation_order("2026-11-01", "2026-11-30")
		self.assertTrue(result["permissions"]["quotations"])
		self.assertTrue(result["permissions"]["deals"])
		self.assertTrue(result["permissions"]["orders"])
		self.assertIsNotNone(result["quotation_summary"])
		self.assertIn("Booked Sales includes only Confirmed/Completed", result["business_definition"])

	@patch("doublet_crm.reports.frappe.has_permission", side_effect=frappe.PermissionError)
	def test_quotation_permission_is_required(self, _has_permission):
		with self.assertRaises(frappe.PermissionError):
			get_quotation_order("2026-11-01", "2026-11-30")
