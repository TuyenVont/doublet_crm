from unittest.mock import patch

import frappe
from frappe.desk.doctype.dashboard_chart.dashboard_chart import get as get_chart
from frappe.tests.utils import FrappeTestCase

from doublet_crm.dashboard import (
	CARD_DEFINITIONS,
	CHART_DEFINITIONS,
	DASHBOARD_NAME,
	get_lost_deals,
	get_open_deals,
	get_won_deals,
	sync_dashboard,
)
from doublet_crm.doublet_crm.doctype.doublet_lead.doublet_lead import convert_lead


class TestDoubleTCRMDashboard(FrappeTestCase):
	def setUp(self):
		self.unique = frappe.generate_hash(length=10)

	def make_stage(self, stage_type):
		return frappe.get_doc({
			"doctype": "DoubleT Deal Stage",
			"stage_name": f"Dashboard-{stage_type}-{frappe.generate_hash(length=10)}",
			"sort_order": 1,
			"stage_type": stage_type,
		}).insert()

	def make_deal(self, stage, amount=0, lost_reason=None):
		return frappe.get_doc({
			"doctype": "DoubleT Deal",
			"deal_title": f"Dashboard Deal {frappe.generate_hash(length=10)}",
			"stage": stage.name,
			"amount": amount,
			"lost_reason": lost_reason,
		}).insert()

	def make_lead(self, **values):
		return frappe.get_doc({
			"doctype": "DoubleT Lead",
			"first_name": f"Dashboard-{frappe.generate_hash(length=10)}",
			**values,
		}).insert()

	def test_setup_creates_all_native_cards_and_charts_idempotently(self):
		dashboard = sync_dashboard()
		card_names = [f"DoubleT CRM - {label}" for label, _ in CARD_DEFINITIONS]
		chart_names = [f"DoubleT CRM - {label}" for label, _ in CHART_DEFINITIONS]

		self.assertEqual(dashboard.name, DASHBOARD_NAME)
		self.assertEqual([row.card for row in dashboard.cards], card_names)
		self.assertEqual([row.chart for row in dashboard.charts], chart_names)
		self.assertEqual(len(card_names), 8)
		self.assertEqual(len(chart_names), 4)
		self.assertEqual(frappe.get_doc("Number Card", card_names[-1]).aggregate_function_based_on, "amount")
		self.assertEqual(frappe.get_doc("Dashboard Chart", chart_names[-1]).based_on, "won_on")

		sync_dashboard()
		self.assertEqual(frappe.db.count("Dashboard", {"name": DASHBOARD_NAME}), 1)
		self.assertEqual(frappe.db.count("Number Card", {"name": ["in", card_names]}), 8)
		self.assertEqual(frappe.db.count("Dashboard Chart", {"name": ["in", chart_names]}), 4)

	def test_deal_state_cards_use_linked_stage_type(self):
		before = [get_open_deals()["value"], get_won_deals()["value"], get_lost_deals()["value"]]
		open_stage = self.make_stage("OPEN")
		won_stage = self.make_stage("WON")
		lost_stage = self.make_stage("LOST")
		self.make_deal(open_stage)
		self.make_deal(won_stage, amount=75)
		self.make_deal(lost_stage, lost_reason="No budget")

		self.assertEqual(get_open_deals()["value"], before[0] + 1)
		self.assertEqual(get_won_deals()["value"], before[1] + 1)
		self.assertEqual(get_lost_deals()["value"], before[2] + 1)

	def test_native_chart_data_uses_lead_status_and_won_amount(self):
		sync_dashboard()
		self.make_lead(status="QUALIFIED")
		won_stage = self.make_stage("WON")
		self.make_deal(won_stage, amount=125)

		status_data = get_chart(chart_name="DoubleT CRM - Lead Status Distribution", refresh=1)
		revenue_data = get_chart(chart_name="DoubleT CRM - Monthly Deal Revenue", refresh=1)
		self.assertIn("QUALIFIED", status_data["labels"])
		self.assertTrue(any(value >= 125 for value in revenue_data["datasets"][0]["values"]))

	def test_lead_status_change_appears_in_version_timeline(self):
		lead = self.make_lead()
		lead.status = "QUALIFIED"
		lead.save()

		versions = frappe.get_all(
			"Version",
			filters={"ref_doctype": "DoubleT Lead", "docname": lead.name},
			pluck="data",
		)
		self.assertTrue(any(
			change[0] == "status"
			for data in versions
			for change in frappe.parse_json(data).get("changed", [])
		))

	def test_deal_stage_change_appears_in_version_timeline(self):
		open_stage = self.make_stage("OPEN")
		won_stage = self.make_stage("WON")
		deal = self.make_deal(open_stage)
		deal.stage = won_stage.name
		deal.save()

		versions = frappe.get_all(
			"Version",
			filters={"ref_doctype": "DoubleT Deal", "docname": deal.name},
			pluck="data",
		)
		self.assertTrue(any(
			change[0] == "stage"
			for data in versions
			for change in frappe.parse_json(data).get("changed", [])
		))

	def test_lead_conversion_adds_timeline_comment(self):
		lead = self.make_lead()
		result = convert_lead(lead.name)
		comments = frappe.get_all(
			"Comment",
			filters={"reference_doctype": "DoubleT Lead", "reference_name": lead.name, "comment_type": "Info"},
			pluck="content",
		)
		self.assertTrue(any(result["contact"] in content and "Lead converted" in content for content in comments))

	def test_comment_failure_rolls_back_conversion(self):
		lead = self.make_lead()
		with patch(
			"doublet_crm.doublet_crm.doctype.doublet_lead.doublet_lead.DoubleTLead.add_comment",
			side_effect=RuntimeError("comment insert failed"),
		):
			with self.assertRaisesRegex(RuntimeError, "comment insert failed"):
				convert_lead(lead.name)

		lead.reload()
		self.assertEqual(lead.status, "NEW")
		self.assertFalse(lead.converted_contact)
		self.assertFalse(frappe.db.exists("DoubleT Contact", {"first_name": lead.first_name}))
