from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from doublet_crm.api import add_activity_comment, get_activities, get_linked_notes, get_notes


class TestDoubleTNote(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		unique = frappe.generate_hash(length=10)
		self.lead = frappe.get_doc({
			"doctype": "DoubleT Lead",
			"first_name": f"Note Lead {unique}",
		}).insert()
		self.other_lead = frappe.get_doc({
			"doctype": "DoubleT Lead",
			"first_name": f"Other Note Lead {unique}",
		}).insert()
		self.contact = frappe.get_doc({
			"doctype": "DoubleT Contact",
			"first_name": f"Note Contact {unique}",
		}).insert()
		self.company = frappe.get_doc({
			"doctype": "DoubleT Company",
			"company_name": f"Note Company {unique}",
		}).insert()
		self.stage = frappe.get_doc({
			"doctype": "DoubleT Deal Stage",
			"stage_name": f"Note Stage {unique}",
			"stage_type": "OPEN",
			"sort_order": 999,
			"enabled": 1,
		}).insert()
		self.deal = frappe.get_doc({
			"doctype": "DoubleT Deal",
			"deal_title": f"Note Deal {unique}",
			"deal_type": "PERSONAL",
			"contact": self.contact.name,
			"stage": self.stage.name,
		}).insert()

	def tearDown(self):
		frappe.set_user("Administrator")

	def make_note(self, reference_doctype="DoubleT Lead", reference_name=None, **values):
		return frappe.get_doc({
			"doctype": "DoubleT Note",
			"title": "Test note",
			"content": "Original content",
			"reference_doctype": reference_doctype,
			"reference_name": reference_name or self.lead.name,
			**values,
		}).insert()

	def test_timeline_is_scoped_to_lead_and_deal(self):
		lead_note = self.make_note()
		deal_note = self.make_note(reference_doctype="DoubleT Deal", reference_name=self.deal.name)
		for doctype, name, content in (
			("DoubleT Lead", self.lead.name, "Lead timeline comment"),
			("DoubleT Deal", self.deal.name, "Deal timeline comment"),
		):
			frappe.get_doc({"doctype": "Comment", "comment_type": "Comment",
				"reference_doctype": doctype, "reference_name": name, "content": content}).insert()

		lead = get_activities("DoubleT Lead", self.lead.name)
		deal = get_activities("DoubleT Deal", self.deal.name)
		self.assertEqual(len(lead), 5)
		self.assertEqual({row.name for row in lead[2]}, {lead_note.name})
		self.assertEqual({row.name for row in deal[2]}, {deal_note.name})
		self.assertTrue(any(row.activity_type == "comment" and row.content == "Lead timeline comment" for row in lead[0]))
		self.assertFalse(any(row.get("content") == "Deal timeline comment" for row in lead[0]))

	def test_timeline_rejects_other_doctypes_and_missing_records(self):
		with self.assertRaises(frappe.ValidationError):
			get_activities("User", "Administrator")
		with self.assertRaises(frappe.DoesNotExistError):
			get_activities("DoubleT Lead", "missing-record")
		with patch("doublet_crm.api.frappe.has_permission", return_value=False):
			with self.assertRaises(frappe.PermissionError):
				get_activities("DoubleT Lead", self.lead.name)

	def test_timeline_maps_linked_call_without_leaking_other_record(self):
		call = frappe.get_doc({
			"doctype": "DoubleT Call Log", "agent": "Administrator",
			"call_type": "Outgoing", "status": "Completed",
			"start_time": frappe.utils.now_datetime(),
			"reference_doctype": "DoubleT Deal", "reference_name": self.deal.name,
		}).insert()
		deal_calls = get_activities("DoubleT Deal", self.deal.name)[1]
		lead_calls = get_activities("DoubleT Lead", self.lead.name)[1]
		self.assertIn(call.name, {row.name for row in deal_calls})
		self.assertNotIn(call.name, {row.name for row in lead_calls})
		self.assertEqual(next(row for row in deal_calls if row.name == call.name).type, "Outgoing")

	def test_comment_endpoint_checks_record_permission(self):
		name = add_activity_comment("DoubleT Lead", self.lead.name, "Scoped comment")
		self.assertIn(name, {row.name for row in get_activities("DoubleT Lead", self.lead.name)[0]})
		with patch("doublet_crm.api.frappe.has_permission", return_value=False):
			with self.assertRaises(frappe.PermissionError):
				add_activity_comment("DoubleT Lead", self.lead.name, "Denied")

	def test_crud_and_reload_persistence(self):
		note = self.make_note()
		note.reload()
		self.assertEqual(note.content, "Original content")

		note.title = "Updated note"
		note.content = "Persisted content"
		note.save()

		reloaded = frappe.get_doc("DoubleT Note", note.name)
		self.assertEqual(reloaded.title, "Updated note")
		self.assertEqual(reloaded.content, "Persisted content")
		reloaded.delete()
		self.assertFalse(frappe.db.exists("DoubleT Note", note.name))

	def test_all_supported_reference_types(self):
		references = {
			"DoubleT Lead": self.lead.name,
			"DoubleT Deal": self.deal.name,
			"DoubleT Contact": self.contact.name,
			"DoubleT Company": self.company.name,
		}
		for doctype, name in references.items():
			with self.subTest(doctype=doctype):
				note = self.make_note(reference_doctype=doctype, reference_name=name)
				note.reload()
				self.assertEqual(note.reference_doctype, doctype)
				self.assertEqual(note.reference_name, name)

	def test_linked_notes_are_isolated_by_record(self):
		first = self.make_note(title="First lead note")
		second = self.make_note(reference_name=self.other_lead.name, title="Second lead note")

		first_results = get_linked_notes("DoubleT Lead", self.lead.name)
		second_results = get_linked_notes("DoubleT Lead", self.other_lead.name)

		self.assertEqual({row.name for row in first_results}, {first.name})
		self.assertEqual({row.name for row in second_results}, {second.name})

	def test_linked_notes_paginate_without_changing_legacy_response(self):
		notes = [self.make_note(title=f"Linked page {index}") for index in range(22)]

		first = get_linked_notes(
			"DoubleT Lead",
			self.lead.name,
			limit_start=0,
			limit_page_length=20,
			include_pagination=1,
		)
		second = get_linked_notes(
			"DoubleT Lead",
			self.lead.name,
			limit_start=20,
			limit_page_length=20,
			include_pagination=1,
		)
		first_names = {row.name for row in first["notes"]}
		second_names = {row.name for row in second["notes"]}

		self.assertEqual(len(first_names), 20)
		self.assertEqual(len(second_names), 2)
		self.assertFalse(first_names & second_names)
		self.assertEqual(first_names | second_names, {note.name for note in notes})
		self.assertTrue(first["has_more"])
		self.assertFalse(second["has_more"])
		self.assertIsInstance(get_linked_notes("DoubleT Lead", self.lead.name), list)

	def test_central_listing_search_and_reference_filter(self):
		lead_note = self.make_note(title="Searchable lead note")
		content_marker = frappe.generate_hash(length=10)
		content_note = self.make_note(title="Content search note", content=f"Body {content_marker}")
		company_note = self.make_note(
			reference_doctype="DoubleT Company",
			reference_name=self.company.name,
			title="Company note",
		)

		self.assertIn(lead_note.name, {row.name for row in get_notes(search="Searchable")})
		self.assertNotIn(company_note.name, {row.name for row in get_notes(search="Searchable")})
		self.assertIn(content_note.name, {row.name for row in get_notes(search=content_marker)})
		self.assertIn(lead_note.name, {row.name for row in get_notes(search=self.lead.name)})
		self.assertIn(
			company_note.name,
			{row.name for row in get_notes(reference_doctype="DoubleT Company")},
		)
		self.assertNotIn(
			lead_note.name,
			{row.name for row in get_notes(reference_doctype="DoubleT Company")},
		)

	def test_central_listing_paginates_with_stable_order(self):
		marker = frappe.generate_hash(length=10)
		notes = [self.make_note(title=f"Paged {marker} {index}") for index in range(5)]
		modified = "2026-01-01 12:00:00"
		for note in notes:
			frappe.db.set_value("DoubleT Note", note.name, "modified", modified, update_modified=False)

		expected = sorted((note.name for note in notes), reverse=True)
		first = get_notes(search=marker, limit_start=0, limit_page_length=2, include_pagination=1)
		second = get_notes(search=marker, limit_start=2, limit_page_length=2, include_pagination=1)
		third = get_notes(search=marker, limit_start=4, limit_page_length=2, include_pagination=1)

		self.assertEqual([row.name for row in first["notes"]], expected[:2])
		self.assertEqual([row.name for row in second["notes"]], expected[2:4])
		self.assertEqual([row.name for row in third["notes"]], expected[4:])
		self.assertTrue(first["has_more"])
		self.assertTrue(second["has_more"])
		self.assertFalse(third["has_more"])

	def test_central_listing_combines_search_and_reference_filter(self):
		marker = frappe.generate_hash(length=10)
		lead_note = self.make_note(title=f"Combined {marker}")
		company_note = self.make_note(
			reference_doctype="DoubleT Company",
			reference_name=self.company.name,
			title=f"Combined {marker}",
		)
		self.make_note(
			reference_doctype="DoubleT Company",
			reference_name=self.company.name,
			title="Different company note",
		)

		result = get_notes(
			search=marker,
			reference_doctype="DoubleT Company",
			limit_page_length=20,
			include_pagination=1,
		)
		self.assertEqual([row.name for row in result["notes"]], [company_note.name])
		self.assertNotIn(lead_note.name, {row.name for row in result["notes"]})

	def test_inaccessible_references_do_not_shrink_accessible_page(self):
		marker = frappe.generate_hash(length=10)
		first = self.make_note(title=f"Visible {marker} one")
		second = self.make_note(title=f"Visible {marker} two")
		inaccessible = self.make_note(
			reference_name=self.other_lead.name,
			title=f"Hidden {marker}",
		)
		real_has_permission = frappe.has_permission

		def has_permission(doctype, *args, **kwargs):
			docname = kwargs.get("doc")
			if doctype == "DoubleT Lead" and docname == self.other_lead.name:
				return False
			return real_has_permission(doctype, *args, **kwargs)

		with (
			patch("doublet_crm.api.frappe.has_permission", side_effect=has_permission),
			patch("doublet_crm.api.NOTE_SCAN_PAGE_LENGTH", 2),
		):
			result = get_notes(
				search=marker,
				limit_start=0,
				limit_page_length=2,
				include_pagination=1,
			)

		self.assertEqual({row.name for row in result["notes"]}, {first.name, second.name})
		self.assertNotIn(inaccessible.name, {row.name for row in result["notes"]})
		self.assertFalse(result["has_more"])

	def test_central_listing_legacy_response_remains_a_list(self):
		marker = frappe.generate_hash(length=10)
		note = self.make_note(title=f"Legacy {marker}")

		result = get_notes(search=marker, reference_doctype="DoubleT Lead")

		self.assertIsInstance(result, list)
		self.assertEqual([row.name for row in result], [note.name])

	def test_permissions(self):
		note = self.make_note()
		self.assertTrue(frappe.has_permission("DoubleT Note", "read", note.name))
		self.assertTrue(frappe.has_permission("DoubleT Note", "write", note.name))
		self.assertTrue(frappe.has_permission("DoubleT Note", "delete", note.name))

		frappe.set_user("Guest")
		self.assertFalse(frappe.has_permission("DoubleT Note", "read", note.name))
		self.assertFalse(frappe.has_permission("DoubleT Note", "create"))
		with self.assertRaises(frappe.PermissionError):
			get_linked_notes("DoubleT Lead", self.lead.name)
		with self.assertRaises(frappe.PermissionError):
			get_notes()
		with self.assertRaises(frappe.PermissionError):
			self.make_note(title="Forbidden note")

	def test_unsupported_reference_type_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_note(reference_doctype="User", reference_name="Administrator")
