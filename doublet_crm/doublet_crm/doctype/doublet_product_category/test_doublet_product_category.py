import frappe
from frappe.tests.utils import FrappeTestCase


class TestDoubleTProductCategory(FrappeTestCase):
	def test_creates_category(self):
		name = f"Category Test {frappe.generate_hash(length=10)}"
		category = frappe.get_doc({
			"doctype": "DoubleT Product Category",
			"category_name": name,
		}).insert()
		self.assertEqual(category.name, name)

	def test_rejects_duplicate_category_name(self):
		name = f"Category Test {frappe.generate_hash(length=10)}"
		frappe.get_doc({
			"doctype": "DoubleT Product Category",
			"category_name": name,
		}).insert()
		with self.assertRaises(frappe.DuplicateEntryError):
			frappe.get_doc({
				"doctype": "DoubleT Product Category",
				"category_name": name,
			}).insert()
