import frappe
from frappe.tests.utils import FrappeTestCase

from doublet_crm.api import get_linked_notes, get_notes


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

	def test_central_listing_search_and_reference_filter(self):
		lead_note = self.make_note(title="Searchable lead note")
		company_note = self.make_note(
			reference_doctype="DoubleT Company",
			reference_name=self.company.name,
			title="Company note",
		)

		self.assertIn(lead_note.name, {row.name for row in get_notes(search="Searchable")})
		self.assertNotIn(company_note.name, {row.name for row in get_notes(search="Searchable")})
		self.assertIn(
			company_note.name,
			{row.name for row in get_notes(reference_doctype="DoubleT Company")},
		)
		self.assertNotIn(
			lead_note.name,
			{row.name for row in get_notes(reference_doctype="DoubleT Company")},
		)

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
