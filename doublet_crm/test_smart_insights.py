import json
from datetime import date
from unittest.mock import Mock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from doublet_crm.report_tools import REPORTS, _export_rows, _filters, _safe_cell, export_report, save_filter
from doublet_crm.dashboard import get_overview
from doublet_crm.smart_insights import (
	_health_score,
	build_smart_insights,
	create_follow_up_task,
	get_smart_insights,
)


def row(**values):
	return frappe._dict(values)


class TestSmartInsightsRules(FrappeTestCase):
	@patch("doublet_crm.smart_insights.stage_aging_for_deals", return_value={"rows": [], "history_available": False})
	@patch("doublet_crm.smart_insights._stage_map", return_value={})
	@patch("doublet_crm.smart_insights.frappe.get_list")
	@patch("doublet_crm.smart_insights.frappe.has_permission", return_value=True)
	def test_exact_alert_boundaries_and_closed_records(self, _permission, get_list, _stages, _aging):
		open_deal = row(name="D-OPEN", deal_title="Open", deal_owner="owner@example.com", amount=100, stage="Open", modified="2026-11-18", expected_close_date="2026-11-25", won_on=None, lost_on=None)
		closed_deal = row(name="D-WON", deal_title="Won", deal_owner="owner@example.com", amount=100, stage="Won", modified="2026-10-01", expected_close_date="2026-11-01", won_on="2026-11-02", lost_on=None)
		quotation = row(name="Q-1", deal="D-OPEN", status="Sent", valid_until="2026-11-28", grand_total=100, modified="2026-11-20")
		task = row(name="T-1", title="Past due", status="Todo", priority="High", due_date="2026-11-24", assigned_to="owner@example.com", reference_doctype="DoubleT Deal", reference_docname="D-OPEN")
		get_list.side_effect = [[open_deal, closed_deal], [quotation], [task], [task], [], []]

		with patch("doublet_crm.smart_insights.readable_stage_evidence_fields", return_value=[]):
			result = build_smart_insights("2026-11-25")

		self.assertEqual({item["type"] for item in result["alerts"]}, {"stale_deal", "quotation_expiry", "overdue_task"})
		self.assertEqual(next(item for item in result["alerts"] if item["type"] == "stale_deal")["days"], 7)
		self.assertEqual(next(item for item in result["alerts"] if item["type"] == "quotation_expiry")["days"], 3)
		self.assertNotIn("D-WON", {item["source_id"] for item in result["alerts"]})
		self.assertEqual([item["deal"] for item in result["health"]], ["D-OPEN"])

	@patch("doublet_crm.smart_insights.stage_aging_for_deals")
	@patch("doublet_crm.smart_insights._stage_map", return_value={})
	@patch("doublet_crm.smart_insights.frappe.get_list")
	@patch("doublet_crm.smart_insights.frappe.has_permission", return_value=True)
	def test_prolonged_stage_is_distinct_from_inactivity(self, _permission, get_list, _stages, stage_aging):
		open_deal = row(name="D-OPEN", deal_title="Open", deal_owner="owner@example.com", amount=100, stage="Qualified", creation="2026-10-01", modified="2026-11-25", expected_close_date=None, won_on=None, lost_on=None)
		get_list.side_effect = [[open_deal], [], [], [], [], []]
		stage_aging.return_value = {"history_available": True, "rows": [{
			"name": "D-OPEN", "deal_title": "Open", "deal_owner": "owner@example.com", "stage": "Qualified", "stage_label": "Qualified",
			"stage_entry_date": "2026-10-01", "stage_entry_actor": "agent@example.com", "days_in_stage": 55, "evidence_source": "deal_transition",
		}]}

		with patch("doublet_crm.smart_insights.readable_stage_evidence_fields", return_value=[]):
			result = build_smart_insights("2026-11-25")

		self.assertEqual([alert["type"] for alert in result["alerts"]], ["prolonged_stage"])
		self.assertNotIn("stale_deal", {alert["type"] for alert in result["alerts"]})
		self.assertEqual(result["thresholds"]["stage_aging_days"], 30)
		self.assertEqual(result["alerts"][0]["stage_entry_actor"], "agent@example.com")
		self.assertEqual(result["alerts"][0]["evidence_source"], "deal_transition")

	def test_health_unknown_inputs_are_excluded_not_scored_as_zero(self):
		deal = row(name="D-1", deal_title="Deal", deal_owner=None, amount=0, modified=None, expected_close_date=None)
		result = _health_score(deal, [], [], date(2026, 11, 25), {"tasks": False, "quotations": False})
		self.assertIsNone(result["score"])
		self.assertEqual(result["category"], "Unknown")
		self.assertEqual(result["coverage"]["known_weight"], 0)
		self.assertTrue(all(item["status"] == "Unknown" for item in result["factors"]))

	def test_health_prefers_trustworthy_linked_interaction_timestamp(self):
		deal = row(name="D-1", deal_title="Deal", deal_owner=None, amount=0, modified="2026-10-01", expected_close_date=None)
		result = _health_score(deal, [], [], date(2026, 11, 25), {"tasks": False, "quotations": False}, ["2026-11-24 10:00:00"])
		recency = next(item for item in result["factors"] if item["key"] == "update_recency")
		self.assertEqual(recency["points"], 25)
		self.assertIn("linked Call/Email interaction", recency["reason"])

	def test_health_does_not_claim_healthy_with_low_coverage(self):
		deal = row(name="D-1", deal_title="Deal", deal_owner=None, amount=0, modified="2026-11-24", expected_close_date=None)
		result = _health_score(deal, [], [], date(2026, 11, 25), {"tasks": False, "quotations": False})
		self.assertEqual(result["category"], "Insufficient Evidence")
		self.assertFalse(result["coverage"]["sufficient"])

	@patch("doublet_crm.smart_insights._stage_map", return_value={})
	@patch("doublet_crm.smart_insights.frappe.get_list")
	@patch("doublet_crm.smart_insights.frappe.has_permission", return_value=True)
	def test_standalone_sent_quotation_expiry_is_included(self, _permission, get_list, _stages):
		quotation = row(name="Q-STANDALONE", deal=None, status="Sent", valid_until="2026-11-28", grand_total=100, modified="2026-11-20")
		get_list.side_effect = lambda doctype, **_kwargs: [quotation] if doctype == "DoubleT Quotation" else []
		with patch("doublet_crm.smart_insights.readable_stage_evidence_fields", return_value=[]):
			result = build_smart_insights("2026-11-25")
		alert = next(item for item in result["alerts"] if item["source_id"] == "Q-STANDALONE")
		self.assertFalse(alert["follow_up"]["available"])

	@patch("doublet_crm.smart_insights.stage_aging_for_deals", return_value={"available": True, "history_available": False, "rows": []})
	@patch("doublet_crm.smart_insights._stage_map", return_value={})
	@patch("doublet_crm.smart_insights.frappe.get_list")
	@patch("doublet_crm.smart_insights.frappe.has_permission")
	def test_restricted_sources_are_not_queried_and_stay_unknown(self, has_permission, get_list, _stages, _aging):
		has_permission.side_effect = lambda doctype, _ptype: doctype == "DoubleT Deal"
		get_list.return_value = [row(name="D-1", deal_title="Deal", deal_owner=None, amount=1, stage="Open", modified="2026-11-25", expected_close_date=None, won_on=None, lost_on=None)]
		with patch("doublet_crm.smart_insights.readable_stage_evidence_fields", return_value=[]):
			result = build_smart_insights("2026-11-25")
		self.assertEqual(get_list.call_count, 1)
		self.assertFalse(result["permissions"]["tasks"])
		self.assertFalse(result["permissions"]["quotations"])
		unknown = {item["key"] for item in result["health"][0]["factors"] if item["status"] == "Unknown"}
		self.assertTrue({"expected_close", "overdue_tasks", "quotation"}.issubset(unknown))

	def test_guest_is_denied_before_source_queries(self):
		with patch.object(frappe, "session", frappe._dict(user="Guest")):
			with patch("doublet_crm.smart_insights.frappe.get_list") as get_list:
				with self.assertRaises(frappe.PermissionError):
					get_smart_insights("2026-11-25")
				get_list.assert_not_called()

	@patch("doublet_crm.smart_insights.build_smart_insights")
	@patch("doublet_crm.smart_insights._transaction_lock")
	@patch("doublet_crm.smart_insights._task_reference", return_value=("DoubleT Deal", "D-1"))
	@patch("doublet_crm.smart_insights.frappe.get_list")
	@patch("doublet_crm.smart_insights.frappe.has_permission", return_value=True)
	def test_follow_up_duplicate_is_returned_without_insert(self, _permission, get_list, _reference, transaction_lock, insights):
		insights.return_value = {"alerts": [{"type": "stale_deal", "source_doctype": "DoubleT Deal", "source_id": "D-1", "source_label": "Deal", "reason": "Stale", "severity": "warning"}]}
		get_list.return_value = ["Administrator"]
		release = Mock(); transaction_lock.return_value = release
		with patch("doublet_crm.smart_insights.frappe.db.get_value", return_value="T-EXISTING"):
			with patch("doublet_crm.smart_insights.frappe.get_doc") as get_doc:
				result = create_follow_up_task("stale_deal", "D-1", assigned_to="Administrator")
		self.assertTrue(result["duplicate"])
		self.assertEqual(result["task"], "T-EXISTING")
		release.assert_called_once()
		get_doc.assert_not_called()


class TestReportExportSafety(FrappeTestCase):
	@patch("doublet_crm.dashboard.frappe.log_error")
	@patch("doublet_crm.dashboard.build_smart_insights", side_effect=RuntimeError("insights unavailable"))
	@patch("doublet_crm.dashboard._can_read", return_value=False)
	def test_dashboard_survives_smart_insights_failure(self, _can_read, _insights, _log):
		result = get_overview()
		self.assertTrue(result["insights_error"])
		self.assertFalse(result["permissions"]["insights"])
		self.assertIn("kpis", result)

	def test_formula_injection_and_unicode_are_csv_safe(self):
		self.assertEqual(_safe_cell("=HYPERLINK('bad')"), "'=HYPERLINK('bad')")
		self.assertEqual(_safe_cell("  -10"), "'  -10")
		self.assertEqual(_safe_cell("Khách hàng Đà Nẵng"), "Khách hàng Đà Nẵng")

	def test_filter_allowlist_rejects_user_and_record_payloads(self):
		with self.assertRaises(frappe.ValidationError):
			_filters("sales-performance", {"user": "Administrator"})
		with self.assertRaises(frappe.ValidationError):
			_filters("sales-performance", {"records": [{"name": "SECRET"}]})
		self.assertEqual(_filters("sales-performance", {"start_date": "2026-11-01", "end_date": "2026-11-25", "compare_previous": True})["compare_previous"], 1)

	@patch("doublet_crm.report_tools.update_user_settings")
	@patch("doublet_crm.report_tools.get_user_settings", return_value="{}")
	def test_saved_filter_uses_installed_frappe_user_settings_contract(self, _get_settings, update_settings):
		items = save_filter("sales-performance", "My period", {"start_date": "2026-11-01", "end_date": "2026-11-25"})
		self.assertEqual(items[0]["name"], "My period")
		update_settings.assert_called_once_with("DoubleT CRM Reports", {"doublet_crm_saved_report_filters": {"sales-performance": items}})

	def test_export_rows_excludes_disallowed_sources_and_restricted_fields(self):
		data = {"order_drilldown": [{"name": "O-1", "total": 10, "status": "Confirmed", "deal": "D-SECRET", "deal_label": "Secret", "quotation": "Q-SECRET"}], "won_deals": [{"name": "D-1", "amount": 99}]}
		with patch("doublet_crm.report_tools._permitted_fields", return_value=({"name", "status"}, {"name", "status", "total", "deal", "quotation"})):
			rows = _export_rows("sales-performance", data, {"DoubleT Order": True, "DoubleT Deal": False})
		self.assertEqual(rows, [{"section": "orders", "name": "O-1", "status": "Confirmed"}])

	def test_journey_children_never_expose_restricted_parent_lead_id(self):
		data = {"journey_rows": [{
			"name": "L-SECRET", "lead_name": "Hidden Lead",
			"deals": [{"name": "D-1", "label": "Visible Deal", "won": False, "amount": 10}],
			"quotations": [{"name": "Q-1", "deal": "D-1", "status": "Sent", "grand_total": 10}],
			"orders": [{"name": "O-1", "deal": "D-1", "quotation": "Q-1", "status": "Confirmed", "total": 10, "link_type": "Quotation"}],
		}]}
		fields = {
			"DoubleT Deal": {"name", "deal_title", "won_on", "amount"},
			"DoubleT Quotation": {"name", "deal", "status", "grand_total"},
			"DoubleT Order": {"name", "deal", "quotation", "status", "total"},
		}
		with patch("doublet_crm.report_tools._permitted_fields", side_effect=lambda doctype: (fields[doctype], fields[doctype])):
			rows = _export_rows("customer-journey", data, {"DoubleT Lead": False, "DoubleT Deal": True, "DoubleT Quotation": True, "DoubleT Order": True})
		self.assertNotIn("L-SECRET", json.dumps(rows))
		self.assertEqual({item["section"] for item in rows}, {"journey_deals", "journey_quotations", "journey_orders"})
		self.assertTrue(all("parent" not in item for item in rows))

	def test_comparison_omits_only_metrics_with_restricted_field_dependencies(self):
		data = {"comparison": {"metrics": {
			"won_count": {"current": 2, "previous": 1, "change": 1},
			"won_deal_value": {"current": 900, "previous": 100, "change": 800},
			"order_count": {"current": 3, "previous": 2, "change": 1},
		}}}
		policies = {
			"DoubleT Deal": ({"name", "won_on", "lost_on", "creation"}, {"name", "won_on", "lost_on", "creation", "amount"}),
			"DoubleT Order": ({"name", "order_date", "status", "total"}, {"name", "order_date", "status", "total"}),
		}
		with patch("doublet_crm.report_tools._permitted_fields", side_effect=lambda doctype: policies[doctype]):
			rows = _export_rows("sales-performance", data, {"DoubleT Order": True, "DoubleT Deal": True})
		self.assertEqual({item["metric"] for item in rows}, {"won_count", "order_count"})

	def test_health_score_requires_every_source_field_dependency(self):
		data = {"health": [{"deal": "D-1", "deal_title": "Visible", "owner": "owner@example.com", "amount": 100, "score": 80, "category": "Healthy", "definition": "derived"}]}
		full = {
			"DoubleT Deal": {"name", "deal_title", "deal_owner", "amount", "modified", "expected_close_date", "won_on", "lost_on", "stage"},
			"DoubleT Deal Stage": {"name", "stage_type"},
			"DoubleT Task": {"name", "status", "due_date", "reference_docname"},
			"DoubleT Quotation": {"name", "status", "valid_until", "deal"},
			"DoubleT Call Log": {"name", "start_time", "reference_name"},
			"Communication": {"name", "creation", "reference_name"},
		}
		allowed = {doctype: True for doctype in full}
		with patch("doublet_crm.report_tools._permitted_fields", side_effect=lambda doctype: (full[doctype], full[doctype])):
			complete = _export_rows("smart-insights", data, allowed)
		self.assertEqual(complete[0]["score"], 80)

		restricted = {doctype: set(fields) for doctype, fields in full.items()}
		restricted["DoubleT Call Log"].remove("start_time")
		with patch("doublet_crm.report_tools._permitted_fields", side_effect=lambda doctype: (restricted[doctype], full[doctype])):
			limited = _export_rows("smart-insights", data, allowed)
		self.assertEqual(limited[0]["deal"], "D-1")
		self.assertNotIn("score", limited[0])
		self.assertNotIn("category", limited[0])

	def test_alert_row_is_omitted_when_rule_fields_are_restricted(self):
		data = {"alerts": [{
			"source_doctype": "DoubleT Quotation", "source_id": "Q-SECRET", "source_label": "Q-SECRET",
			"type": "quotation_expiry", "severity": "warning", "reason": "expires soon", "relevant_date": "2026-11-28", "days": 3,
		}]}
		all_fields = {"name", "status", "valid_until"}
		allowed = {"DoubleT Quotation": True}
		with patch("doublet_crm.report_tools._permitted_fields", return_value=({"name", "valid_until"}, all_fields)):
			rows = _export_rows("smart-insights", data, allowed)
		self.assertNotIn("Q-SECRET", json.dumps(rows))

	def test_dynamic_link_identifiers_require_target_export_permission(self):
		data = {"sources": {"tasks": {"selected": True, "rows": [{
			"name": "T-1", "title": "Visible Task", "status": "Todo",
			"reference_doctype": "DoubleT Deal", "reference_docname": "D-SECRET",
		}]}}}
		policies = {
			"DoubleT Task": ({"name", "title", "status", "reference_doctype", "reference_docname"}, {"name", "title", "status", "reference_doctype", "reference_docname"}),
			"DoubleT Deal": ({"name"}, {"name"}),
		}
		with patch("doublet_crm.report_tools._permitted_fields", side_effect=lambda doctype: policies[doctype]), patch("doublet_crm.report_tools.frappe.has_permission", return_value=True):
			restricted = _export_rows("activity-contact-center", data, {"DoubleT Task": True, "DoubleT Deal": False})
			complete = _export_rows("activity-contact-center", data, {"DoubleT Task": True, "DoubleT Deal": True})
		self.assertNotIn("D-SECRET", json.dumps(restricted))
		self.assertEqual(complete[0]["reference_docname"], "D-SECRET")

	def test_linked_identifier_requires_document_level_read_permission(self):
		data = {"order_drilldown": [{"name": "O-1", "deal": "D-RESTRICTED", "deal_label": "Hidden Deal", "total": 10}]}
		fields = {
			"DoubleT Order": ({"name", "deal", "total"}, {"name", "deal", "total"}),
			"DoubleT Deal": ({"name", "deal_title"}, {"name", "deal_title"}),
		}
		with patch("doublet_crm.report_tools._permitted_fields", side_effect=lambda doctype: fields[doctype]), patch("doublet_crm.report_tools.frappe.has_permission", return_value=False):
			rows = _export_rows("sales-performance", data, {"DoubleT Order": True, "DoubleT Deal": True})
		self.assertNotIn("D-RESTRICTED", json.dumps(rows))
		self.assertNotIn("Hidden Deal", json.dumps(rows))

	def test_forecast_export_omits_restricted_probability_but_keeps_permitted_values(self):
		data = {"forecast": {
			"probability_fields": {"deal": "probability", "stage": None},
			"months": [{"month": "2026-12", "deal_count": 1, "unweighted_value": 100, "weighted_value": 80, "weighted_deal_count": 1, "missing_probability_count": 0}],
			"deals": [{"name": "D-1", "deal_title": "Visible", "amount": 100, "expected_close_date": "2026-12-01", "stage": "Open", "probability": 80, "probability_source": "DoubleT Deal.probability", "weighted_value": 80}],
		}}
		all_fields = {"name", "deal_title", "amount", "expected_close_date", "stage", "probability"}
		with patch("doublet_crm.report_tools._permitted_fields", return_value=({"name", "deal_title", "amount", "expected_close_date", "stage"}, all_fields)):
			rows = _export_rows("pipeline-analytics", data, {"DoubleT Deal": True, "DoubleT Deal Stage": True})
		self.assertTrue(any("unweighted_value" in item for item in rows))
		self.assertTrue(all("weighted_value" not in item for item in rows))
		self.assertTrue(all("probability_source" not in item for item in rows))
		with patch("doublet_crm.report_tools._permitted_fields", return_value=(all_fields, all_fields)), patch("doublet_crm.report_tools.frappe.has_permission", return_value=True):
			complete = _export_rows("pipeline-analytics", data, {"DoubleT Deal": True, "DoubleT Deal Stage": True})
		self.assertTrue(any(item.get("weighted_value") == 80 for item in complete))
		self.assertTrue(any(item.get("probability") == 80 for item in complete))

	def test_customer_journey_owner_aliases_follow_metric_dependencies(self):
		data = {"by_owner": [{"owner": "owner@example.com", "label": "owner@example.com", "lead_count": 2, "deal_count": 1}]}
		policies = {
			"DoubleT Lead": ({"name", "lead_owner", "creation"}, {"name", "lead_owner", "creation"}),
			"DoubleT Deal": ({"name", "source_lead"}, {"name", "source_lead"}),
		}
		with patch("doublet_crm.report_tools._permitted_fields", side_effect=lambda doctype: policies[doctype]):
			rows = _export_rows("customer-journey", data, {"DoubleT Lead": True, "DoubleT Deal": False, "DoubleT Quotation": False, "DoubleT Order": False})
		self.assertEqual(rows[0]["owner"], "owner@example.com")
		self.assertEqual(rows[0]["lead_count"], 2)
		self.assertNotIn("deal_count", rows[0])

	def test_activity_email_export_sources_include_supported_sales_documents(self):
		self.assertIn("DoubleT Quotation", REPORTS["activity-contact-center"]["sources"])
		self.assertIn("DoubleT Order", REPORTS["activity-contact-center"]["sources"])

	def test_stage_aging_export_requires_authorized_version_evidence(self):
		data = {"stage_aging": {
			"available": True, "average_days_in_stage": 12, "known_count": 1, "unknown_count": 0,
			"buckets": [{"key": "8_14", "label": "8–14 days", "deal_count": 1}], "by_stage": [],
			"rows": [{"name": "D-1", "deal_title": "Visible", "deal_owner": "owner@example.com", "stage": "S-1", "stage_label": "Qualified", "stage_entry_date": "2026-11-13", "stage_entry_actor": "agent@example.com", "days_in_stage": 12, "evidence_source": "version", "history_status": "Known", "unknown_reason": None}],
		}}
		policies = {
			"DoubleT Deal": ({"name", "deal_title", "deal_owner", "stage", "creation"}, {"name", "deal_title", "deal_owner", "stage", "creation"}),
			"DoubleT Deal Stage": ({"name", "stage_name"}, {"name", "stage_name"}),
			"Version": ({"name", "owner", "ref_doctype", "docname", "creation", "data"}, {"name", "owner", "ref_doctype", "docname", "creation", "data"}),
		}
		with patch("doublet_crm.report_tools._permitted_fields", side_effect=lambda doctype: policies[doctype]), patch("doublet_crm.report_tools.frappe.has_permission", return_value=True):
			restricted = _export_rows("pipeline-analytics", data, {"DoubleT Deal": True, "DoubleT Deal Stage": True, "Version": False})
			complete = _export_rows("pipeline-analytics", data, {"DoubleT Deal": True, "DoubleT Deal Stage": True, "Version": True})
		self.assertNotIn("D-1", json.dumps(restricted))
		self.assertEqual(next(row for row in complete if row["section"] == "stage_aging_deals")["days_in_stage"], 12)

	def test_stage_aging_export_accepts_authorized_explicit_evidence_without_version_access(self):
		data = {"stage_aging": {
			"available": True, "average_days_in_stage": 12, "known_count": 1, "unknown_count": 0,
			"buckets": [], "by_stage": [],
			"rows": [{"name": "D-1", "deal_title": "Visible", "deal_owner": "owner@example.com", "stage": "S-1", "stage_entry_date": "2026-11-13", "stage_entry_actor": "agent@example.com", "days_in_stage": 12, "evidence_source": "deal_transition", "history_status": "Known", "unknown_reason": None}],
		}}
		policies = {
			"DoubleT Deal": ({"name", "deal_title", "deal_owner", "stage", "stage_entered_on", "stage_entered_by"}, {"name", "deal_title", "deal_owner", "stage", "stage_entered_on", "stage_entered_by"}),
			"DoubleT Deal Stage": ({"name", "stage_name"}, {"name", "stage_name"}),
		}
		with patch("doublet_crm.report_tools._permitted_fields", side_effect=lambda doctype: policies[doctype]), patch("doublet_crm.report_tools.frappe.has_permission", return_value=True):
			rows = _export_rows("pipeline-analytics", data, {"DoubleT Deal": True, "DoubleT Deal Stage": True, "Version": False})
		self.assertEqual(next(row for row in rows if row["section"] == "stage_aging_deals")["stage_entry_actor"], "agent@example.com")

	@patch("doublet_crm.report_tools.frappe.has_permission", return_value=True)
	def test_export_reruns_report_and_emits_complete_bom_csv(self, _permission):
		def report_method(**filters):
			self.assertEqual(filters["salesperson"], "owner@example.com")
			return {"order_drilldown": [
				{"name": "O-1", "deal": "D-1", "deal_label": "Khách hàng Đà Nẵng", "total": 10},
				{"name": "O-2", "deal": "D-2", "deal_label": "=HYPERLINK('bad')", "total": 20},
			]}
		config = {"label": "Sales Performance", "sources": ("DoubleT Order", "DoubleT Deal"), "method": report_method, "filters": {"start_date", "end_date", "salesperson"}}
		with patch.dict(REPORTS, {"sales-performance": config}), patch("doublet_crm.report_tools._permitted_fields", return_value=({"name", "total", "deal", "deal_title"}, {"name", "total", "deal", "deal_title"})):
			result = export_report("sales-performance", {"start_date": "2026-11-01", "end_date": "2026-11-25", "salesperson": "owner@example.com"})
		self.assertEqual(result["row_count"], 2)
		self.assertTrue(result["content"].startswith("\ufeff"))
		self.assertIn("Khách hàng Đà Nẵng", result["content"])
		self.assertIn("'=HYPERLINK", result["content"])
