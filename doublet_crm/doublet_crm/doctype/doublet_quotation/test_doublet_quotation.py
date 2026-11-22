import frappe
from decimal import Decimal
from unittest.mock import patch
from frappe.permissions import get_role_permissions
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate


class TestDoubleTQuotation(FrappeTestCase):
	def setUp(self):
		self.tag = frappe.generate_hash(length=10)
		self.company = frappe.get_doc({"doctype": "DoubleT Company", "company_name": f"Quote Company {self.tag}"}).insert()
		self.contact = frappe.get_doc({"doctype": "DoubleT Contact", "first_name": f"Quote Contact {self.tag}", "company": self.company.name}).insert()
		self.category = frappe.get_doc({"doctype": "DoubleT Product Category", "category_name": f"Quote Category {self.tag}"}).insert()
		self.product = frappe.get_doc({"doctype": "DoubleT Product", "product_name": f"Quote Product {self.tag}", "sku": f"QUOTE-{self.tag}", "category": self.category.name, "price": 101}).insert()

	def quotation(self, **values):
		return frappe.get_doc({"doctype": "DoubleT Quotation", "customer_type": "COMPANY", "company": self.company.name,
			"contact": self.contact.name, "quotation_date": nowdate(), "valid_until": nowdate(),
			"items": [{"product": self.product.name, "quantity": 2, "unit_price": 101, "discount_percent": 10}], **values})

	def make_product(self, label, **values):
		return frappe.get_doc({
			"doctype": "DoubleT Product",
			"product_name": f"{label} {self.tag}",
			"sku": f"{label.upper().replace(' ', '-')}-{self.tag}",
			"category": self.category.name,
			"price": 101,
			**values,
		}).insert()

	def test_direct_snapshot_override_and_totals(self):
		quote = self.quotation().insert()
		self.assertTrue(quote.name.startswith("QUO-"))
		self.assertEqual(
			(quote.subtotal, quote.total_discount, quote.grand_total),
			(Decimal("202.00"), Decimal("20.20"), Decimal("181.80")),
		)
		self.assertEqual((quote.items[0].sku, quote.items[0].product_name), (self.product.sku, self.product.product_name))
		self.product.product_name = "Changed"
		self.product.price = 200
		self.product.save()
		quote.notes = "Changed notes"
		quote.save()
		self.assertEqual(quote.items[0].product_name, f"Quote Product {self.tag}")
		self.assertEqual(quote.items[0].unit_price, 101)

	def test_linked_deal_and_customer_consistency(self):
		stage = frappe.get_doc({"doctype": "DoubleT Deal Stage", "stage_name": f"Quote Stage {self.tag}", "stage_type": "OPEN", "sort_order": 1}).insert()
		deal = frappe.get_doc({"doctype": "DoubleT Deal", "deal_title": f"Quote Deal {self.tag}", "deal_type": "COMPANY", "company": self.company.name, "contact": self.contact.name, "stage": stage.name}).insert()
		self.quotation(deal=deal.name).insert()
		with self.assertRaises(frappe.ValidationError):
			self.quotation(deal=deal.name, contact=None).insert()
		with self.assertRaises(frappe.ValidationError):
			self.quotation(customer_type="PERSONAL").insert()

	def test_rounding(self):
		quote = self.quotation(items=[{"product": self.product.name, "quantity": 1, "unit_price": 101, "discount_percent": 50}]).insert()
		self.assertEqual(
			(quote.subtotal, quote.total_discount, quote.grand_total),
			(Decimal("101.00"), Decimal("50.50"), Decimal("50.50")),
		)

	def test_usd_cents_for_amount_and_percentage_discounts(self):
		amount_quote = self.quotation(items=[{
			"product": self.product.name,
			"quantity": 2,
			"unit_price": 19.99,
			"discount_type": "Amount",
			"discount_percent": 0,
			"discount_amount": 5,
		}]).insert()
		self.assertEqual(
			(amount_quote.subtotal, amount_quote.total_discount, amount_quote.grand_total),
			(Decimal("39.98"), Decimal("5.00"), Decimal("34.98")),
		)
		percentage_quote = self.quotation(items=[{
			"product": self.product.name,
			"quantity": 2,
			"unit_price": 19.99,
			"discount_type": "Percentage",
			"discount_percent": 10,
		}]).insert()
		self.assertEqual(
			(percentage_quote.subtotal, percentage_quote.total_discount, percentage_quote.grand_total),
			(Decimal("39.98"), Decimal("4.00"), Decimal("35.98")),
		)

	def test_pdf_html_uses_usd_cents_and_sent_totals_remain_historical(self):
		from doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_pdf import quotation_html

		quote = self.quotation(items=[{
			"product": self.product.name,
			"quantity": 2,
			"unit_price": 19.99,
			"discount_type": "Amount",
			"discount_percent": 0,
			"discount_amount": 5,
		}]).insert()
		totals = (quote.subtotal, quote.total_discount, quote.grand_total)
		html = quotation_html(quote.name)
		for text in ("Unit Price", "(USD)", "$19.99", "$5.00", "$34.98"):
			self.assertIn(text, html)

		quote.status = "Sent"
		quote.save()
		quote.reload()
		self.assertEqual(
			tuple(Decimal(str(value)) for value in (quote.subtotal, quote.total_discount, quote.grand_total)),
			totals,
		)
		self.assertIn("$34.98", quotation_html(quote.name))

	def test_default_price_from_product(self):
		quote = self.quotation(items=[{"product": self.product.name, "quantity": 1}]).insert()
		self.assertEqual(quote.items[0].unit_price, 101)

	def test_active_standard_product_can_be_added(self):
		quote = self.quotation(items=[{"product": self.product.name, "quantity": 1}]).insert()
		self.assertEqual(quote.items[0].product, self.product.name)
		self.assertEqual(quote.items[0].unit_price, self.product.price)

	def test_active_variant_can_be_added_when_template_is_inactive(self):
		template = self.make_product("Quote Template", product_kind="Template", is_active=0)
		variant = self.make_product(
			"Quote Variant",
			product_kind="Variant",
			variant_of=template.name,
			variant_attributes=[{"attribute_name": "Color", "attribute_value": "Red"}],
			price=175,
		)
		quote = self.quotation(items=[{"product": variant.name, "quantity": 1}]).insert()
		self.assertEqual((quote.items[0].product, quote.items[0].unit_price), (variant.name, 175))

	def test_active_template_cannot_be_added(self):
		template = self.make_product("Active Template", product_kind="Template", is_active=1)
		with self.assertRaises(frappe.ValidationError):
			self.quotation(items=[{"product": template.name, "quantity": 1}]).insert()

	def test_inactive_standard_and_variant_cannot_be_added(self):
		inactive_standard = self.make_product("Inactive Standard", is_active=0)
		template = self.make_product("Variant Template", product_kind="Template", is_active=1)
		inactive_variant = self.make_product(
			"Inactive Variant",
			product_kind="Variant",
			variant_of=template.name,
			variant_attributes=[{"attribute_name": "Color", "attribute_value": "Blue"}],
			is_active=0,
		)
		for product in (inactive_standard, inactive_variant):
			with self.subTest(product=product.name), self.assertRaises(frappe.ValidationError):
				self.quotation(items=[{"product": product.name, "quantity": 1}]).insert()

	def test_variant_snapshot_is_preserved_when_its_price_changes(self):
		template = self.make_product("Snapshot Template", product_kind="Template")
		variant = self.make_product(
			"Snapshot Variant",
			product_kind="Variant",
			variant_of=template.name,
			variant_attributes=[{"attribute_name": "Size", "attribute_value": "Large"}],
			price=175,
		)
		quote = self.quotation(items=[{"product": variant.name, "quantity": 1}]).insert()
		variant.product_name = "Changed Variant"
		variant.price = 250
		variant.save()
		quote.notes = "Keep snapshot"
		quote.save()
		self.assertEqual((quote.items[0].product_name, quote.items[0].unit_price), (f"Snapshot Variant {self.tag}", 175))

	def test_accepted_multi_item_snapshot_survives_product_and_price_list_changes(self):
		second_product = self.make_product("Snapshot Second", price=29.95)
		price_list = frappe.get_doc({
			"doctype": "DoubleT Price List",
			"price_list_name": f"Snapshot Price List {self.tag}",
			"items": [
				{"product": self.product.name, "price": 19.99},
				{"product": second_product.name, "price": 8.50},
			],
		}).insert()
		quote = self.quotation(
			price_list=price_list.name,
			items=[
				{
					"product": self.product.name,
					"quantity": 2,
					"discount_type": "Percentage",
					"discount_percent": 10,
				},
				{
					"product": second_product.name,
					"quantity": 3,
					"discount_type": "Amount",
					"discount_amount": 2.55,
				},
			],
		).insert()

		def number(value):
			return Decimal(str(value)).quantize(Decimal("0.01"))

		def snapshot(document):
			return {
				"items": tuple(
					(
						row.product,
						row.product_name,
						row.sku,
						number(row.quantity),
						number(row.unit_price),
						row.discount_type,
						number(row.discount_percent),
						number(row.discount_amount),
						number(row.line_total),
					)
					for row in document.items
				),
				"subtotal": number(document.subtotal),
				"total_discount": number(document.total_discount),
				"grand_total": number(document.grand_total),
			}

		before = snapshot(quote)
		self.assertEqual(
			(before["subtotal"], before["total_discount"], before["grand_total"]),
			(Decimal("65.48"), Decimal("6.55"), Decimal("58.93")),
		)
		self.assertEqual(
			tuple((row[4], row[7], row[8]) for row in before["items"]),
			(
				(Decimal("19.99"), Decimal("4.00"), Decimal("35.98")),
				(Decimal("8.50"), Decimal("2.55"), Decimal("22.95")),
			),
		)

		quote.status = "Sent"
		quote.save()
		quote.status = "Accepted"
		quote.save()

		self.product.price = 999
		self.product.save()
		second_product.price = 888
		second_product.save()
		price_list.items[0].price = 199.99
		price_list.items[1].price = 88.50
		price_list.save()

		quote.reload()
		self.assertEqual(quote.status, "Accepted")
		self.assertEqual(snapshot(quote), before)

		for field, value in (
			("product", second_product.name),
			("product_name", "Tampered Product"),
			("sku", "TAMPERED-SKU"),
			("quantity", 99),
			("unit_price", 0.01),
			("discount_type", "Amount"),
			("discount_percent", 50),
			("discount_amount", 0.01),
			("line_total", 0.01),
		):
			with self.subTest(field=field):
				quote.reload()
				setattr(quote.items[0], field, value)
				with self.assertRaises(frappe.ValidationError):
					quote.save()

		quote.reload()
		quote.price_list = None
		with self.assertRaises(frappe.ValidationError):
			quote.save()
		quote.reload()
		quote.status = "Rejected"
		with self.assertRaises(frappe.ValidationError):
			quote.save()

	def test_personal_and_company_contact_validation(self):
		self.quotation(customer_type="PERSONAL", company=None).insert()
		other = frappe.get_doc({"doctype": "DoubleT Contact", "first_name": f"Other {self.tag}"}).insert()
		with self.assertRaises(frappe.ValidationError):
			self.quotation(contact=other.name).insert()

	def test_unlinking_deal_allows_customer_change_without_repricing_saved_items(self):
		stage = frappe.get_doc({"doctype": "DoubleT Deal Stage", "stage_name": f"Switch Stage {self.tag}", "stage_type": "OPEN", "sort_order": 1}).insert()
		deal = frappe.get_doc({"doctype": "DoubleT Deal", "deal_title": f"Switch Deal {self.tag}", "deal_type": "COMPANY", "company": self.company.name, "contact": self.contact.name, "stage": stage.name}).insert()
		quote = self.quotation(
			deal=deal.name,
			items=[{"product": self.product.name, "quantity": 1, "unit_price": 77}],
		).insert()
		other_company = frappe.get_doc({"doctype": "DoubleT Company", "company_name": f"Other Company {self.tag}"}).insert()
		other_contact = frappe.get_doc({"doctype": "DoubleT Contact", "first_name": f"Other Contact {self.tag}", "company": other_company.name}).insert()

		quote.deal = None
		quote.company = other_company.name
		quote.contact = other_contact.name
		quote.save()
		quote.reload()

		self.assertEqual((quote.deal, quote.company, quote.contact), (None, other_company.name, other_contact.name))
		self.assertEqual(quote.items[0].unit_price, 77)

	def test_draft_delete_and_rejected_transition(self):
		draft = self.quotation().insert()
		draft.delete()
		quote = self.quotation().insert()
		quote.status = "Sent"
		quote.save()
		quote.status = "Rejected"
		quote.save()
		self.assertEqual(quote.status, "Rejected")
		quote.status = "Accepted"
		with self.assertRaises(frappe.ValidationError):
			quote.save()

	def test_invalid_values(self):
		for field, value in (("quantity", 0), ("unit_price", -1), ("discount_percent", -1), ("discount_percent", 101)):
			item = {"product": self.product.name, "quantity": 1, "unit_price": 10, "discount_percent": 0, field: value}
			with self.subTest(field=field, value=value), self.assertRaises(frappe.ValidationError):
				self.quotation(items=[item]).insert()
		with self.assertRaises(frappe.ValidationError):
			self.quotation(quotation_date="2026-12-02", valid_until="2026-12-01").insert()
		with self.assertRaises(frappe.ValidationError):
			self.quotation(items=[]).insert()
		with self.assertRaises(frappe.LinkValidationError):
			self.quotation(items=[{"product": f"missing-{self.tag}", "quantity": 1}]).insert()

	def test_inactive_product(self):
		self.product.is_active = 0
		self.product.save()
		with self.assertRaises(frappe.ValidationError):
			self.quotation().insert()

	def test_status_lock_and_delete(self):
		quote = self.quotation().insert()
		quote.status = "Accepted"
		with self.assertRaises(frappe.ValidationError):
			quote.save()
		quote.reload()
		quote.status = "Sent"
		quote.save()
		quote.notes = "Not allowed"
		with self.assertRaises(frappe.ValidationError):
			quote.save()
		quote.reload()
		quote.items[0].quantity = 3
		with self.assertRaises(frappe.ValidationError):
			quote.save()
		quote.reload()
		quote.items[0].line_total = 1
		with self.assertRaises(frappe.ValidationError):
			quote.save()
		quote.reload()
		with self.assertRaises(frappe.ValidationError):
			quote.delete()
		quote.status = "Accepted"
		quote.save()
		self.assertEqual(quote.status, "Accepted")

	def test_live_role_permission_matrix(self):
		meta = frappe.get_meta("DoubleT Quotation")
		for role, expected in (("System Manager", (1, 1, 1, 1)), ("Sales Manager", (1, 1, 1, 1)), ("Sales User", (1, 1, 1, 0)), ("Guest", (0, 0, 0, 0))):
			with self.subTest(role=role), patch("frappe.get_roles", return_value=[role]):
				permissions = get_role_permissions(meta, user="quotation-test@example.invalid", debug=True)
				self.assertEqual(tuple(permissions[key] for key in ("read", "create", "write", "delete")), expected)

	def test_guest_denied(self):
		try:
			frappe.set_user("Guest")
			self.assertFalse(frappe.has_permission("DoubleT Quotation", "read"))
			self.assertFalse(frappe.has_permission("DoubleT Quotation", "create"))
		finally:
			frappe.set_user("Administrator")

	def test_sales_users_can_create_quotation_from_readable_deal(self):
		from frappe.client import get as client_get

		stage = frappe.get_doc({"doctype": "DoubleT Deal Stage", "stage_name": f"Permission Stage {self.tag}", "stage_type": "OPEN", "sort_order": 1}).insert()
		deal = frappe.get_doc({"doctype": "DoubleT Deal", "deal_title": f"Permission Deal {self.tag}", "deal_type": "COMPANY", "company": self.company.name, "contact": self.contact.name, "stage": stage.name, "amount": 12345}).insert()
		for role in ("Sales Manager", "Sales User"):
			user = frappe.get_doc({"doctype": "User", "email": f"quotation-{role.replace(' ', '-').lower()}-{self.tag}@example.invalid", "first_name": "Quotation Test", "enabled": 1, "send_welcome_email": 0, "roles": [{"role": role}]}).insert()
			try:
				frappe.set_user(user.name)
				for doctype, name in (("DoubleT Deal", deal.name), ("DoubleT Contact", self.contact.name), ("DoubleT Company", self.company.name)):
					self.assertTrue(frappe.has_permission(doctype, "read", name))
				deal_data = client_get("DoubleT Deal", deal.name)
				self.assertEqual(deal_data.get("contact"), self.contact.name)
				self.assertEqual(deal_data.get("company"), self.company.name)
				if role == "Sales User":
					self.assertEqual(deal_data.get("amount"), 12345)
					self.assertNotIn(1, frappe.get_meta("DoubleT Deal").get_permlevel_access("read"))
					self.assertFalse(frappe.has_permission("DoubleT Deal", "delete", deal.name))
				self.assertFalse(frappe.has_permission("DoubleT Contact", "write", self.contact.name))
				self.assertFalse(frappe.has_permission("DoubleT Contact", "delete", self.contact.name))
				contact = frappe.get_doc("DoubleT Contact", self.contact.name)
				contact.first_name = "Unauthorized update"
				with self.assertRaises(frappe.PermissionError):
					contact.save()
				with self.assertRaises(frappe.PermissionError):
					frappe.delete_doc("DoubleT Contact", self.contact.name)
				self.assertTrue(self.quotation(deal=deal.name).insert().name)
			finally:
				frappe.set_user("Administrator")
