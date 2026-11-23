from datetime import date
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from doublet_crm.reports import (
	BOOKED_ORDER_STATUSES,
	_summarize,
	_summarize_pipeline,
	get_pipeline_analytics,
	get_sales_performance,
)


def row(**values):
	return frappe._dict(values)


class TestSalesPerformanceReport(FrappeTestCase):
	def test_summary_uses_order_totals_without_double_counting(self):
		orders = [
			row(name="ORD-1", order_date=date(2026, 11, 1), total=100, deal="DEAL-1"),
			row(name="ORD-2", order_date=date(2026, 11, 1), total=50, deal=None),
			row(name="ORD-3", order_date=date(2026, 11, 2), total=150, deal="DEAL-2"),
		]
		deals = {
			"DEAL-1": row(name="DEAL-1", deal_owner="owner@example.com"),
			"DEAL-2": row(name="DEAL-2", deal_owner=None),
		}

		result = _summarize(orders, deals)

		self.assertEqual(result["booked_sales"], 300)
		self.assertEqual(result["order_count"], 3)
		self.assertEqual(result["average_order_value"], 100)
		self.assertEqual(result["trend"][0]["order_count"], 2)
		self.assertEqual(
			{item["assignment_state"] for item in result["by_salesperson"]},
			{"assigned", "unassigned"},
		)

	@patch("doublet_crm.reports.frappe.get_list")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_api_queries_only_booked_orders_in_the_applied_dates(self, has_permission, get_list):
		has_permission.side_effect = [True, True]
		get_list.side_effect = [
			[
				row(
					name="ORD-1",
					order_date=date(2026, 11, 3),
					status="Confirmed",
					total=125,
					currency="USD",
					deal="DEAL-1",
				)
			],
			[row(name="DEAL-1", deal_title="Real Deal", deal_owner="owner@example.com")],
		]

		result = get_sales_performance("2026-11-01", "2026-11-30")

		order_call = get_list.call_args_list[0]
		self.assertEqual(order_call.args[0], "DoubleT Order")
		self.assertIn(["order_date", "between", [date(2026, 11, 1), date(2026, 11, 30)]], order_call.kwargs["filters"])
		self.assertIn(["status", "in", BOOKED_ORDER_STATUSES], order_call.kwargs["filters"])
		self.assertEqual(result["booked_sales"], 125)
		self.assertEqual(result["recent_orders"][0]["deal"], "DEAL-1")
		self.assertIn("not paid revenue", result["business_definition"])

	@patch("doublet_crm.reports.frappe.get_list")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_salesperson_filter_uses_readable_deal_ownership_consistently(self, has_permission, get_list):
		has_permission.side_effect = [True, True]
		get_list.side_effect = [
			["DEAL-1"],
			[
				row(name="ORD-1", order_date=date(2026, 11, 3), status="Confirmed", total=125, currency="USD", deal="DEAL-1"),
				row(name="ORD-2", order_date=date(2026, 11, 4), status="Completed", total=75, currency="USD", deal="DEAL-2"),
			],
			[
				row(name="DEAL-1", deal_title="Mine", deal_owner="owner@example.com"),
				row(name="DEAL-2", deal_title="Theirs", deal_owner="other@example.com"),
			],
		]

		result = get_sales_performance("2026-11-01", "2026-11-30", "owner@example.com")

		self.assertEqual(result["order_count"], 1)
		self.assertEqual(result["booked_sales"], 125)
		self.assertEqual([item["name"] for item in result["recent_orders"]], ["ORD-1"])
		self.assertEqual(result["by_salesperson"][0]["salesperson"], "owner@example.com")

	@patch("doublet_crm.reports.frappe.has_permission")
	def test_order_permission_is_required_before_any_query(self, has_permission):
		has_permission.side_effect = frappe.PermissionError
		with self.assertRaises(frappe.PermissionError):
			get_sales_performance("2026-11-01", "2026-11-30")

	@patch("doublet_crm.reports.frappe.get_list")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_unreadable_deals_do_not_expose_deal_ids(self, has_permission, get_list):
		has_permission.side_effect = [True, False]
		get_list.return_value = [
			row(
				name="ORD-1",
				order_date=date(2026, 11, 3),
				status="Confirmed",
				total=125,
				currency="USD",
				deal="DEAL-RESTRICTED",
			)
		]

		result = get_sales_performance("2026-11-01", "2026-11-30")

		self.assertEqual(get_list.call_count, 1)
		self.assertFalse(result["permissions"]["deals"])
		self.assertIsNone(result["recent_orders"][0]["deal"])
		self.assertTrue(result["recent_orders"][0]["deal_restricted"])
		self.assertEqual(result["by_salesperson"][0]["assignment_state"], "restricted")

	def test_reversed_date_range_is_rejected(self):
		with patch("doublet_crm.reports.frappe.has_permission", return_value=True):
			with self.assertRaises(frappe.ValidationError):
				get_sales_performance("2026-11-30", "2026-11-01")


class TestPipelineAnalyticsReport(FrappeTestCase):
	def test_summary_groups_deal_count_and_value_by_stage_and_lifecycle(self):
		deals = [
			row(name="DEAL-1", stage="Prospecting", amount=100, won_on=None, lost_on=None),
			row(name="DEAL-2", stage="Won", amount=250, won_on="2026-11-02", lost_on=None),
			row(name="DEAL-3", stage="Lost", amount=75, won_on=None, lost_on="2026-11-03"),
		]
		stages = {
			"Prospecting": row(stage_name="Prospecting", stage_type="OPEN", color="#0000ff", sort_order=1),
			"Won": row(stage_name="Won", stage_type="WON", color="#00ff00", sort_order=2),
			"Lost": row(stage_name="Lost", stage_type="LOST", color="#ff0000", sort_order=3),
		}

		result = _summarize_pipeline(deals, stages)

		self.assertEqual(result["deal_count"], 3)
		self.assertEqual(result["total_deal_value"], 425)
		self.assertEqual(result["open_pipeline_value"], 100)
		self.assertEqual(result["lifecycle"]["WON"], {"deal_count": 1, "deal_value": 250})
		self.assertEqual([stage["stage_type"] for stage in result["by_stage"]], ["OPEN", "WON", "LOST"])

	@patch("doublet_crm.reports.frappe.get_list")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_api_uses_permission_scoped_creation_range_and_stage_metadata(self, has_permission, get_list):
		has_permission.side_effect = [True, True]
		get_list.side_effect = [
			[
				row(
					name="DEAL-1",
					deal_title="Real Pipeline Deal",
					amount=125,
					deal_owner="owner@example.com",
					stage="Qualified",
					creation="2026-11-03 09:00:00",
					expected_close_date=date(2026, 12, 1),
					won_on=None,
					lost_on=None,
				)
			],
			[row(name="Qualified", stage_name="Qualified", stage_type="OPEN", color="#0000ff", sort_order=2)],
		]

		result = get_pipeline_analytics("2026-11-01", "2026-11-30")

		deal_call = get_list.call_args_list[0]
		self.assertEqual(deal_call.args[0], "DoubleT Deal")
		self.assertIn(["creation", ">=", "2026-11-01 00:00:00"], deal_call.kwargs["filters"])
		self.assertIn(["creation", "<", "2026-12-01 00:00:00"], deal_call.kwargs["filters"])
		self.assertEqual(get_list.call_args_list[1].args[0], "DoubleT Deal Stage")
		self.assertEqual(result["open_pipeline_value"], 125)
		self.assertEqual(result["by_stage"][0]["label"], "Qualified")
		self.assertIn("not realized or paid revenue", result["business_definition"])

	@patch("doublet_crm.reports.frappe.get_list")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_salesperson_filter_updates_all_pipeline_results(self, has_permission, get_list):
		has_permission.side_effect = [True, True]
		get_list.side_effect = [
			["DEAL-1"],
			[
				row(name="DEAL-1", deal_title="Mine", amount=100, deal_owner="owner@example.com", stage="Open", creation="2026-11-03", expected_close_date=None, won_on=None, lost_on=None),
				row(name="DEAL-2", deal_title="Other", amount=200, deal_owner="other@example.com", stage="Won", creation="2026-11-04", expected_close_date=None, won_on="2026-11-05", lost_on=None),
			],
			[row(name="Open", stage_name="Open", stage_type="OPEN", color=None, sort_order=1)],
		]

		result = get_pipeline_analytics("2026-11-01", "2026-11-30", "owner@example.com")

		self.assertEqual(result["deal_count"], 1)
		self.assertEqual(result["total_deal_value"], 100)
		self.assertEqual(result["lifecycle"]["WON"]["deal_count"], 0)
		self.assertEqual([deal["name"] for deal in result["recent_deals"]], ["DEAL-1"])
		self.assertEqual({option["value"] for option in result["salespeople"]}, {"owner@example.com", "other@example.com"})

	@patch("doublet_crm.reports.frappe.get_list")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_restricted_stage_metadata_uses_deal_lifecycle_fields(self, has_permission, get_list):
		has_permission.side_effect = [True, False]
		get_list.return_value = [
			row(name="DEAL-1", deal_title="Closed Deal", amount=150, deal_owner=None, stage="Private Won Stage", creation="2026-11-03", expected_close_date=None, won_on="2026-11-04", lost_on=None)
		]

		result = get_pipeline_analytics("2026-11-01", "2026-11-30")

		self.assertEqual(get_list.call_count, 1)
		self.assertFalse(result["permissions"]["stages"])
		self.assertEqual(result["by_stage"][0]["stage_type"], "WON")
		self.assertEqual(result["recent_deals"][0]["stage"], "Private Won Stage")

	@patch("doublet_crm.reports.frappe.has_permission")
	def test_deal_permission_is_required_before_pipeline_query(self, has_permission):
		has_permission.side_effect = frappe.PermissionError
		with self.assertRaises(frappe.PermissionError):
			get_pipeline_analytics("2026-11-01", "2026-11-30")
