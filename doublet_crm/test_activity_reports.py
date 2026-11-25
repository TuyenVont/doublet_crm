from datetime import datetime
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from doublet_crm.reports import get_activity_contact_center


def row(**values):
	return frappe._dict(values)


class TestActivityContactCenterReport(FrappeTestCase):
	def _source_rows(self, doctype):
		return {
			"DoubleT Call Log": [
				row(name="CALL-A", agent="a@example.com", assigned_to=None, call_type="Incoming", duration=30, status="Missed", start_time="2026-11-10 09:00:00", from_number="1", to_number="2"),
				row(name="CALL-B", agent="b@example.com", assigned_to=None, call_type="Outgoing", duration=90, status="Completed", start_time="2026-11-11 09:00:00", from_number="2", to_number="3"),
			],
			"DoubleT Task": [
				row(name="TASK-A", title="A", status="Todo", priority="High", due_date="2026-11-24 11:59:59", assigned_to="a@example.com", reference_doctype=None, reference_docname=None, creation="2026-11-10 10:00:00"),
				row(name="TASK-B", title="B", status="Done", priority="Low", due_date="2026-11-24 12:00:00", assigned_to="b@example.com", reference_doctype=None, reference_docname=None, creation="2026-11-11 10:00:00"),
			],
			"Communication": [
				row(name="MAIL-IN", subject="In", sender="x@example.com", recipients="a@example.com", sent_or_received="Received", creation="2026-11-10 08:00:00"),
				row(name="MAIL-OUT", subject="Out", sender="a@example.com", recipients="x@example.com", sent_or_received="Sent", creation="2026-11-11 08:00:00"),
			],
			"DoubleT Conversation": [row(name="CONV-1", source="zalo_oa", oa_id="oa", external_user_id="user", lead=None, creation="2026-11-10 07:00:00")],
			"DoubleT Message": [
				row(name="MSG-REAL", conversation="CONV-1", source="zalo_oa", direction="inbound", content="Real", sent_at="2026-11-10 07:01:00", is_simulated=0),
				row(name="MSG-MOCK", conversation="CONV-1", source="zalo_oa", direction="outbound", content="Mock", sent_at="2026-11-11 07:01:00", is_simulated=1),
			],
		}[doctype]

	@patch("doublet_crm.reports.now_datetime", return_value=datetime(2026, 11, 24, 12, 0, 0))
	@patch("doublet_crm.reports.frappe.get_list")
	@patch("doublet_crm.reports.frappe.has_permission", return_value=True)
	def test_metrics_employee_filter_and_drilldown_use_exact_source_rows(self, _permission, get_list, _now):
		get_list.side_effect = lambda doctype, **_kwargs: self._source_rows(doctype)

		result = get_activity_contact_center("2026-11-01", "2026-11-30", "a@example.com")

		self.assertEqual(result["employees"], [
			{"value": "a@example.com", "label": "a@example.com"},
			{"value": "b@example.com", "label": "b@example.com"},
		])
		self.assertEqual((result["sources"]["calls"]["total"], result["sources"]["calls"]["missed"], result["sources"]["calls"]["duration_seconds"]), (1, 1, 30))
		self.assertEqual([item.name for item in result["sources"]["calls"]["rows"]], ["CALL-A"])
		self.assertEqual((result["sources"]["tasks"]["total"], result["sources"]["tasks"]["pending"], result["sources"]["tasks"]["overdue"]), (1, 1, 1))
		self.assertEqual((result["sources"]["email"]["incoming"], result["sources"]["email"]["outgoing"]), (1, 1))
		self.assertEqual((result["sources"]["zalo"]["message_count"], result["sources"]["zalo"]["real_message_count"], result["sources"]["zalo"]["simulated_message_count"]), (2, 1, 1))

	@patch("doublet_crm.reports.now_datetime", return_value=datetime(2026, 11, 24, 12, 0, 0))
	@patch("doublet_crm.reports.frappe.get_list")
	@patch("doublet_crm.reports.frappe.has_permission", return_value=True)
	def test_queries_use_verified_date_and_email_schema_filters(self, _permission, get_list, _now):
		get_list.side_effect = lambda doctype, **_kwargs: self._source_rows(doctype)

		get_activity_contact_center("2026-11-01", "2026-11-30")

		calls, tasks, email, conversations, messages = get_list.call_args_list
		self.assertEqual(calls.kwargs["filters"][:2], [["start_time", ">=", "2026-11-01 00:00:00"], ["start_time", "<", "2026-12-01 00:00:00"]])
		self.assertEqual(tasks.kwargs["filters"][:2], [["creation", ">=", "2026-11-01 00:00:00"], ["creation", "<", "2026-12-01 00:00:00"]])
		self.assertIn(["communication_medium", "=", "Email"], email.kwargs["filters"])
		self.assertIn(["communication_type", "=", "Communication"], email.kwargs["filters"])
		self.assertIn(["reference_doctype", "in", ("DoubleT Lead", "DoubleT Deal", "DoubleT Contact", "DoubleT Company", "DoubleT Quotation", "DoubleT Order")], email.kwargs["filters"])
		self.assertEqual(conversations.kwargs["filters"][0][0], "creation")
		self.assertEqual(messages.kwargs["filters"][0][0], "sent_at")

	@patch("doublet_crm.reports.now_datetime", return_value=datetime(2026, 11, 24, 12, 0, 0))
	@patch("doublet_crm.reports.frappe.get_list")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_sources_are_independently_unavailable_and_links_are_not_exposed(self, has_permission, get_list, _now):
		allowed = {"DoubleT Call Log": False, "DoubleT Task": True, "Communication": False, "DoubleT Conversation": False, "DoubleT Message": True}
		has_permission.side_effect = lambda doctype, _ptype: allowed[doctype]
		get_list.side_effect = lambda doctype, **_kwargs: self._source_rows(doctype)

		result = get_activity_contact_center("2026-11-01", "2026-11-30")

		self.assertIsNone(result["sources"]["calls"]["total"])
		self.assertIsNone(result["sources"]["email"]["incoming"])
		self.assertIsNone(result["sources"]["zalo"]["conversation_count"])
		self.assertEqual(result["sources"]["tasks"]["total"], 2)
		self.assertEqual(result["sources"]["zalo"]["message_count"], 2)
		self.assertTrue(all(item.conversation is None for item in result["sources"]["zalo"]["messages"]))
		self.assertEqual([call.args[0] for call in get_list.call_args_list], ["DoubleT Task", "DoubleT Message"])

	@patch("doublet_crm.reports.now_datetime", return_value=datetime(2026, 11, 24, 12, 0, 0))
	@patch("doublet_crm.reports.frappe.get_list")
	@patch("doublet_crm.reports.frappe.has_permission", return_value=True)
	def test_overdue_boundary_is_strict_and_only_pending_statuses_count(self, _permission, get_list, _now):
		rows = self._source_rows("DoubleT Task") + [
			row(name="BOUNDARY", title="Boundary", status="In Progress", priority="Low", due_date="2026-11-24 12:00:00", assigned_to="a@example.com", reference_doctype=None, reference_docname=None, creation="2026-11-12 10:00:00"),
			row(name="CANCELED", title="Canceled", status="Canceled", priority="Low", due_date="2026-11-01 00:00:00", assigned_to="a@example.com", reference_doctype=None, reference_docname=None, creation="2026-11-12 11:00:00"),
		]
		get_list.side_effect = lambda doctype, **_kwargs: rows if doctype == "DoubleT Task" else self._source_rows(doctype)

		result = get_activity_contact_center("2026-11-01", "2026-11-30")

		self.assertEqual(result["sources"]["tasks"]["pending"], 2)
		self.assertEqual(result["sources"]["tasks"]["overdue"], 1)

	@patch("doublet_crm.reports.now_datetime", return_value=datetime(2026, 11, 24, 12, 0, 0))
	@patch("doublet_crm.reports.frappe.get_list")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_inbox_link_requires_record_level_conversation_permission(self, has_permission, get_list, _now):
		def permission(doctype, _ptype, doc=None):
			return not (doctype == "DoubleT Conversation" and doc == "CONV-1")
		has_permission.side_effect = permission
		get_list.side_effect = lambda doctype, **_kwargs: self._source_rows(doctype)

		result = get_activity_contact_center("2026-11-01", "2026-11-30")

		self.assertTrue(result["permissions"]["zalo_conversations"])
		self.assertTrue(all(message.conversation is None for message in result["sources"]["zalo"]["messages"]))

	@patch("doublet_crm.reports.now_datetime", return_value=datetime(2026, 11, 24, 12, 0, 0))
	@patch("doublet_crm.reports.frappe.get_list", return_value=[])
	@patch("doublet_crm.reports.frappe.has_permission", return_value=True)
	def test_selected_employee_is_preserved_when_new_range_has_zero_activity(self, _permission, _get_list, _now):
		result = get_activity_contact_center("2026-12-01", "2026-12-31", "a@example.com")

		self.assertEqual(result["employees"], [{"value": "a@example.com", "label": "a@example.com"}])
		self.assertEqual(result["sources"]["calls"]["total"], 0)
		self.assertEqual(result["sources"]["tasks"]["total"], 0)

	@patch("doublet_crm.reports.now_datetime", return_value=datetime(2026, 11, 24, 12, 0, 0))
	@patch("doublet_crm.reports.frappe.get_list")
	@patch("doublet_crm.reports.frappe.has_permission", return_value=True)
	def test_channel_filter_queries_only_the_selected_source(self, _permission, get_list, _now):
		get_list.side_effect = lambda doctype, **_kwargs: self._source_rows(doctype)
		result = get_activity_contact_center("2026-11-01", "2026-11-30", channel="Call")
		activity_doctypes = {"DoubleT Call Log", "DoubleT Task", "Communication", "DoubleT Conversation", "DoubleT Message"}
		self.assertEqual([call.args[0] for call in get_list.call_args_list if call.args[0] in activity_doctypes], ["DoubleT Call Log"])
		self.assertEqual(result["filters"]["channel"], "Call")
		self.assertTrue(result["sources"]["calls"]["selected"])
		self.assertFalse(result["sources"]["tasks"]["selected"])
		self.assertIsNone(result["sources"]["tasks"]["total"])

	def test_invalid_channel_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			get_activity_contact_center("2026-11-01", "2026-11-30", channel="SMS")

