import frappe
import json
from pathlib import Path
from unittest.mock import patch

from frappe.permissions import get_role_permissions
from frappe.tests.utils import FrappeTestCase


class TestDoubleTProduct(FrappeTestCase):
	def setUp(self):
		self.suffix = frappe.generate_hash(length=10)
		self.category = frappe.get_doc({
			"doctype": "DoubleT Product Category",
			"category_name": f"Product Test Category {self.suffix}",
		}).insert()
		self.other_category = frappe.get_doc({
			"doctype": "DoubleT Product Category",
			"category_name": f"Other Product Test Category {self.suffix}",
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

	def make_template(self, **values):
		return self.make_product(
			product_name=f"Template {self.suffix}",
			sku=f"TEMPLATE-{self.suffix}",
			product_kind="Template",
			**values,
		)

	def make_variant(self, template, **values):
		return self.make_product(
			product_name=f"Variant {self.suffix}",
			sku=f"VARIANT-{self.suffix}",
			product_kind="Variant",
			variant_of=template.name,
			variant_attributes=[{"attribute_name": "Color", "attribute_value": "Red"}],
			**values,
		)

	def test_create_valid_product(self):
		product = self.make_product().insert()
		self.assertEqual(product.name, product.sku)
		self.assertEqual(product.category, self.category.name)
		self.assertEqual(product.product_kind, "Standard")
		self.assertEqual([row.category for row in product.categories], [self.category.name])

	def test_allows_multiple_category_assignments(self):
		product = self.make_product(categories=[
			{"category": self.category.name},
			{"category": self.other_category.name},
		]).insert()
		self.assertEqual(
			{row.category for row in product.categories},
			{self.category.name, self.other_category.name},
		)

	def test_rejects_duplicate_category_assignments(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_product(categories=[
				{"category": self.other_category.name},
				{"category": self.other_category.name},
			]).insert()

	def test_template_activity_is_preserved_and_cannot_have_variant_details(self):
		template = self.make_template().insert()
		self.assertEqual(template.is_active, 1)
		self.assertFalse(template.is_sellable())
		inactive_template = self.make_template(
			product_name=f"Inactive Template {self.suffix}",
			sku=f"INACTIVE-TEMPLATE-{self.suffix}",
			is_active=0,
		).insert()
		self.assertEqual(inactive_template.is_active, 0)
		self.assertFalse(inactive_template.is_sellable())
		with self.assertRaises(frappe.ValidationError):
			self.make_template(
				sku=f"INVALID-TEMPLATE-{self.suffix}",
				variant_attributes=[{"attribute_name": "Color", "attribute_value": "Red"}],
			).insert()

	def test_creates_variant_for_template(self):
		template = self.make_template().insert()
		variant = self.make_variant(template).insert()
		self.assertEqual(variant.variant_of, template.name)
		self.assertTrue(variant.variant_signature)
		self.assertRegex(variant.variant_key, r"^[0-9a-f]{64}$")
		self.assertTrue(variant.is_sellable())

	def test_variant_activity_is_independent_of_template_activity(self):
		template = self.make_template(is_active=0).insert()
		variant = self.make_variant(template).insert()
		self.assertEqual(template.is_active, 0)
		self.assertEqual(variant.is_active, 1)
		self.assertTrue(variant.is_sellable())
		variant.is_active = 0
		variant.save()
		self.assertFalse(variant.is_sellable())

	def test_rejects_duplicate_variant_combination(self):
		template = self.make_template().insert()
		self.make_variant(template).insert()
		with self.assertRaises(frappe.DuplicateEntryError):
			self.make_variant(
				template,
				product_name=f"Second variant {self.suffix}",
				sku=f"VARIANT-SECOND-{self.suffix}",
			).insert()

	def test_rejects_invalid_variant_parent_and_attributes(self):
		standard = self.make_product(sku=f"STANDARD-{self.suffix}").insert()
		with self.assertRaises(frappe.ValidationError):
			self.make_variant(standard).insert()
		with self.assertRaises(frappe.ValidationError):
			self.make_product(
				product_kind="Variant",
				variant_of=f"Missing Template {self.suffix}",
				variant_attributes=[{"attribute_name": "Color", "attribute_value": "Red"}],
			).insert()
		template = self.make_template(sku=f"TEMPLATE-ATTR-{self.suffix}").insert()
		with self.assertRaises(frappe.ValidationError):
			self.make_variant(template, sku=f"VARIANT-EMPTY-{self.suffix}", variant_attributes=[]).insert()
		with self.assertRaises(frappe.ValidationError):
			self.make_variant(
				template,
				sku=f"VARIANT-DUPLICATE-ATTR-{self.suffix}",
				variant_attributes=[
					{"attribute_name": "Color", "attribute_value": "Red"},
					{"attribute_name": "color", "attribute_value": "Blue"},
				],
			).insert()

	def test_variant_parent_and_attributes_are_immutable(self):
		template = self.make_template().insert()
		variant = self.make_variant(template).insert()
		other_template = self.make_template(
			product_name=f"Other Template {self.suffix}",
			sku=f"OTHER-TEMPLATE-{self.suffix}",
		).insert()
		variant.variant_of = other_template.name
		with self.assertRaises(frappe.ValidationError):
			variant.save()
		variant = frappe.get_doc("DoubleT Product", variant.name)
		variant.variant_attributes[0].attribute_value = "Blue"
		with self.assertRaises(frappe.ValidationError):
			variant.save()

	def test_standard_active_status_is_preserved(self):
		product = self.make_product(is_active=0).insert()
		self.assertEqual(product.is_active, 0)

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

	def test_product_and_category_source_role_permissions(self):
		base = Path(__file__).resolve().parent.parent
		for folder, doctype in (
			("doublet_product", "DoubleT Product"),
			("doublet_product_category", "DoubleT Product Category"),
		):
			with (base / folder / f"{folder}.json").open(encoding="utf-8") as source:
				metadata = json.load(source)
			meta = frappe._dict(name=doctype, permissions=[frappe._dict(row) for row in metadata["permissions"]])
			for role, expected in (
				("System Manager", (1, 1, 1, 1)),
				("Sales Manager", (1, 1, 1, 1)),
				("Sales User", (1, 1, 1, 0)),
				("Guest", (0, 0, 0, 0)),
			):
				with self.subTest(doctype=doctype, role=role), patch("frappe.get_roles", return_value=[role]):
					permissions = get_role_permissions(meta, user="permission-test@example.invalid", debug=True)
					self.assertEqual(tuple(permissions[key] for key in ("read", "create", "write", "delete")), expected)
