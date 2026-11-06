import frappe
from frappe.tests.utils import FrappeTestCase


class TestDoubleTProduct(FrappeTestCase):
	def setUp(self):
		self.suffix = frappe.generate_hash(length=10)
		self.category = frappe.get_doc({
			"doctype": "DoubleT Product Category",
			"category_name": f"Product Test Category {self.suffix}",
		}).insert()

	def make_product(self, **values):
		return frappe.get_doc({
			"doctype": "DoubleT Product",
			"product_name": f"Product {self.suffix}",
			"sku": f"TEST-{self.suffix}",
			"category": self.category.name,
			"price": 100,
			**values,
		})

	def test_create_valid_product(self):
		product = self.make_product().insert()
		self.assertEqual(product.name, product.sku)
		self.assertEqual(product.category, self.category.name)

	def test_generates_sku_when_omitted(self):
		product = frappe.get_doc({
			"doctype": "DoubleT Product",
			"product_name": f"Automatic SKU {self.suffix}",
			"category": self.category.name,
			"price": 100,
		}).insert()
		self.assertRegex(product.sku, r"^PRD-\d{5}$")
		self.assertEqual(product.name, product.sku)

	def test_generates_sku_when_empty(self):
		product = self.make_product(sku="").insert()
		self.assertRegex(product.sku, r"^PRD-\d{5}$")

	def test_automatic_skus_are_sequential_and_unique(self):
		first = self.make_product(sku="", product_name="First automatic product").insert()
		second = self.make_product(sku="", product_name="Second automatic product").insert()
		self.assertNotEqual(first.sku, second.sku)
		self.assertEqual(int(second.sku.removeprefix("PRD-")), int(first.sku.removeprefix("PRD-")) + 1)

	def test_allows_manual_sku(self):
		product = self.make_product(sku=f"MANUAL-{self.suffix}").insert()
		self.assertEqual(product.sku, f"MANUAL-{self.suffix}")

	def test_rejects_duplicate_sku(self):
		self.make_product().insert()
		with self.assertRaises(frappe.DuplicateEntryError):
			self.make_product(product_name="Another product").insert()

	def test_rejects_negative_price(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_product(price=-1).insert()

	def test_rejects_missing_product_name(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_product(product_name=" ").insert()

	def test_rejects_nonexistent_category(self):
		with self.assertRaises(frappe.LinkValidationError):
			self.make_product(category=f"Missing Category {self.suffix}").insert()

	def test_rejects_sku_change_after_creation(self):
		product = self.make_product().insert()
		product.sku = f"CHANGED-{self.suffix}"
		with self.assertRaises(frappe.ValidationError):
			product.save()

	def test_allows_zero_price(self):
		product = self.make_product(price=0).insert()
		self.assertEqual(product.price, 0)

	def test_product_links_to_category(self):
		product = self.make_product().insert()
		reloaded = frappe.get_doc("DoubleT Product", product.name)
		self.assertEqual(reloaded.category, self.category.name)
