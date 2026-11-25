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
	@patch("doublet_crm.smart_insights._stage_map", return_value={})
	@patch("doublet_crm.smart_insights.frappe.get_list")
	@patch("doublet_crm.smart_insights.frappe.has_permission", return_value=True)
	def test_exact_alert_boundaries_and_closed_records(self, _permission, get_list, _stages):
		open_deal = row(name="D-OPEN", deal_title="Open", deal_owner="owner@example.com", amount=100, stage="Open", modified="2026-11-18", expected_close_date="2026-11-25", won_on=None, lost_on=None)
		closed_deal = row(name="D-WON", deal_title="Won", deal_owner="owner@example.com", amount=100, stage="Won", modified="2026-10-01", expected_close_date="2026-11-01", won_on="2026-11-02", lost_on=None)
		quotation = row(name="Q-1", deal="D-OPEN", status="Sent", valid_until="2026-11-28", grand_total=100, modified="2026-11-20")
		task = row(name="T-1", title="Past due", status="Todo", priority="High", due_date="2026-11-24", assigned_to="owner@example.com", reference_doctype="DoubleT Deal", reference_docname="D-OPEN")
		get_list.side_effect = [[open_deal, closed_deal], [quotation], [task], [task], [], []]

		result = build_smart_insights("2026-11-25")

		self.assertEqual({item["type"] for item in result["alerts"]}, {"stale_deal", "quotation_expiry", "overdue_task"})
		self.assertEqual(next(item for item in result["alerts"] if item["type"] == "stale_deal")["days"], 7)
		self.assertEqual(next(item for item in result["alerts"] if item["type"] == "quotation_expiry")["days"], 3)
		self.assertNotIn("D-WON", {item["source_id"] for item in result["alerts"]})
		self.assertEqual([item["deal"] for item in result["health"]], ["D-OPEN"])

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
		result = build_smart_insights("2026-11-25")
		alert = next(item for item in result["alerts"] if item["source_id"] == "Q-STANDALONE")
		self.assertFalse(alert["follow_up"]["available"])

	@patch("doublet_crm.smart_insights._stage_map", return_value={})
	@patch("doublet_crm.smart_insights.frappe.get_list")
	@patch("doublet_crm.smart_insights.frappe.has_permission")
	def test_restricted_sources_are_not_queried_and_stay_unknown(self, has_permission, get_list, _stages):
		has_permission.side_effect = lambda doctype, _ptype: doctype == "DoubleT Deal"
		get_list.return_value = [row(name="D-1", deal_title="Deal", deal_owner=None, amount=1, stage="Open", modified="2026-11-25", expected_close_date=None, won_on=None, lost_on=None)]
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
		data = {"order_drilldown": [{"name": "O-1", "total": 10, "status": "Confirmed"}], "won_deals": [{"name": "D-1", "amount": 99}]}
		with patch("doublet_crm.report_tools._permitted_fields", return_value=({"name", "status"}, {"name", "status", "total"})):
			rows = _export_rows("sales-performance", data, {"DoubleT Order": True, "DoubleT Deal": False})
		self.assertEqual(rows, [{"section": "orders", "name": "O-1", "status": "Confirmed"}])

	@patch("doublet_crm.report_tools.frappe.has_permission", return_value=True)
	def test_export_reruns_report_and_emits_complete_bom_csv(self, _permission):
		def report_method(**filters):
			self.assertEqual(filters["salesperson"], "owner@example.com")
			return {"order_drilldown": [
				{"name": "O-1", "deal_label": "Khách hàng Đà Nẵng", "total": 10},
				{"name": "O-2", "deal_label": "=HYPERLINK('bad')", "total": 20},
			]}
		config = {"label": "Sales Performance", "sources": ("DoubleT Order", "DoubleT Deal"), "method": report_method, "filters": {"start_date", "end_date", "salesperson"}}
		with patch.dict(REPORTS, {"sales-performance": config}), patch("doublet_crm.report_tools._permitted_fields", return_value=({"name", "total", "deal_title"}, {"name", "total", "deal_title"})):
			result = export_report("sales-performance", {"start_date": "2026-11-01", "end_date": "2026-11-25", "salesperson": "owner@example.com"})
		self.assertEqual(result["row_count"], 2)
		self.assertTrue(result["content"].startswith("\ufeff"))
		self.assertIn("Khách hàng Đà Nẵng", result["content"])
		self.assertIn("'=HYPERLINK", result["content"])
