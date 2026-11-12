from decimal import Decimal

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate

from doublet_crm.pricing import get_product_price, resolve_product_price


class TestPricing(FrappeTestCase):
    def setUp(self):
        self.tag = frappe.generate_hash(length=10)
        self.company = frappe.get_doc(
            {"doctype": "DoubleT Company", "company_name": f"Pricing Company {self.tag}"}
        ).insert()
        self.contact = frappe.get_doc(
            {
                "doctype": "DoubleT Contact",
                "first_name": f"Pricing Contact {self.tag}",
                "company": self.company.name,
            }
        ).insert()
        self.category = frappe.get_doc(
            {
                "doctype": "DoubleT Product Category",
                "category_name": f"Pricing Category {self.tag}",
            }
        ).insert()
        self.product = self.make_product("Standard", price=101)
        self.template = self.make_product("Template", product_kind="Template")
        self.variant = self.make_product(
            "Variant",
            product_kind="Variant",
            variant_of=self.template.name,
            variant_attributes=[{"attribute_name": "Size", "attribute_value": "Large"}],
            price=175,
        )
        self.retail = self.make_price_list("Retail", [(self.product, 90), (self.variant, 150)])
        self.wholesale = self.make_price_list("Wholesale", [(self.product, 80)])
        frappe.db.set_single_value(
            "DoubleT Pricing Settings", "default_price_list", self.retail.name
        )

    def make_product(self, label, **values):
        return frappe.get_doc(
            {
                "doctype": "DoubleT Product",
                "product_name": f"Pricing {label} {self.tag}",
                "sku": f"PRICING-{label.upper()}-{self.tag}",
                "category": self.category.name,
                "price": 100,
                **values,
            }
        ).insert()

    def make_price_list(self, label, prices):
        return frappe.get_doc(
            {
                "doctype": "DoubleT Price List",
                "price_list_name": f"Pricing {label} {self.tag}",
                "items": [{"product": product.name, "price": price} for product, price in prices],
            }
        ).insert()

    def quotation(self, **values):
        return frappe.get_doc(
            {
                "doctype": "DoubleT Quotation",
                "customer_type": "COMPANY",
                "company": self.company.name,
                "contact": self.contact.name,
                "quotation_date": nowdate(),
                "valid_until": nowdate(),
                "items": [{"product": self.product.name, "quantity": 1}],
                **values,
            }
        )

    def resolve(self, product=None, **values):
        return resolve_product_price(
            product or self.product,
            "COMPANY",
            company=self.company.name,
            contact=self.contact.name,
            **values,
        )

    def test_price_list_precedence_and_customer_fallback(self):
        self.company.price_list = self.wholesale.name
        self.company.save()
        self.contact.price_list = self.retail.name
        self.contact.save()

        self.assertEqual(self.resolve(price_list=self.retail.name)["price"], 90)
        self.assertEqual(self.resolve()["price"], 80)
        self.company.price_list = None
        self.company.save()
        self.assertEqual(self.resolve()["price"], 90)
        self.contact.price_list = None
        self.contact.save()
        self.assertEqual(self.resolve()["price"], 90)

    def test_personal_contact_price_list_and_inactive_list_are_rejected(self):
        self.contact.price_list = self.wholesale.name
        self.contact.save()
        personal = resolve_product_price(
            self.product,
            "PERSONAL",
            contact=self.contact.name,
        )
        self.assertEqual(personal["price"], 80)
        self.wholesale.is_active = 0
        self.wholesale.save()
        with self.assertRaises(frappe.ValidationError):
            resolve_product_price(
                self.product,
                "PERSONAL",
                contact=self.contact.name,
            )

    def test_missing_item_uses_product_price_and_variant_uses_exact_item_price(self):
        self.company.price_list = self.wholesale.name
        self.company.save()
        self.assertEqual(self.resolve()["price"], 80)
        self.assertEqual(self.resolve(self.variant)["price"], 175)
        self.assertEqual(self.resolve(self.variant, price_list=self.retail.name)["price"], 150)

    def test_templates_and_inactive_products_are_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            self.resolve(self.template)
        self.variant.is_active = 0
        self.variant.save()
        with self.assertRaises(frappe.ValidationError):
            self.resolve(self.variant)

    def test_manual_unit_price_is_preserved(self):
        quote = self.quotation(
            price_list=self.wholesale.name,
            items=[{"product": self.product.name, "quantity": 1, "unit_price": 77}],
        ).insert()
        self.assertEqual(quote.items[0].unit_price, 77)

    def test_new_quotation_item_uses_resolved_price(self):
        quote = self.quotation(price_list=self.wholesale.name).insert()
        self.assertEqual(quote.items[0].unit_price, 80)

    def test_percentage_and_amount_discounts(self):
        quote = self.quotation(
            items=[
                {
                    "product": self.product.name,
                    "quantity": 2,
                    "unit_price": 101,
                    "discount_type": "Percentage",
                    "discount_percent": 10,
                },
                {
                    "product": self.product.name,
                    "quantity": 1,
                    "unit_price": 101,
                    "discount_type": "Amount",
                    "discount_amount": 25,
                },
            ]
        ).insert()
        self.assertEqual((quote.items[0].discount_amount, quote.items[0].line_total), (20, 182))
        self.assertEqual((quote.items[1].discount_percent, quote.items[1].line_total), (0, 76))
        self.assertEqual((quote.subtotal, quote.total_discount, quote.grand_total), (303, 45, 258))

    def test_rejects_invalid_discounts_and_rounds_consistently(self):
        invalid_items = (
            {"discount_type": "Amount", "discount_amount": 102},
            {"discount_type": "Amount", "discount_percent": 1, "discount_amount": 1},
            {"discount_type": "Unknown", "discount_percent": 0},
            {"discount_type": "Percentage", "discount_percent": 101},
        )
        for values in invalid_items:
            with self.subTest(values=values), self.assertRaises(frappe.ValidationError):
                self.quotation(
                    items=[{"product": self.product.name, "quantity": 1, "unit_price": 101, **values}]
                ).insert()
        quote = self.quotation(
            items=[
                {
                    "product": self.product.name,
                    "quantity": 1,
                    "unit_price": 101,
                    "discount_type": "Percentage",
                    "discount_percent": 50,
                }
            ]
        ).insert()
        self.assertEqual((quote.total_discount, quote.grand_total), (51, 50))

    def test_non_draft_quote_preserves_totals_and_discount_snapshot(self):
        quote = self.quotation(
            items=[
                {
                    "product": self.product.name,
                    "quantity": 1,
                    "unit_price": 101,
                    "discount_type": "Amount",
                    "discount_amount": 25,
                }
            ]
        ).insert()
        quote.status = "Sent"
        quote.save()
        snapshot = (quote.subtotal, quote.total_discount, quote.grand_total, quote.items[0].unit_price)
        self.product.price = 999
        self.product.save()
        quote.reload()
        quote.save()
        self.assertEqual(
            (quote.subtotal, quote.total_discount, quote.grand_total, quote.items[0].unit_price),
            snapshot,
        )
        quote.items[0].discount_amount = 26
        with self.assertRaises(frappe.ValidationError):
            quote.save()

    def test_pricing_api_denies_guest_access(self):
        try:
            frappe.set_user("Guest")
            with self.assertRaises(frappe.PermissionError):
                get_product_price(
                    self.product.name,
                    "COMPANY",
                    company=self.company.name,
                    contact=self.contact.name,
                )
        finally:
            frappe.set_user("Administrator")

    def test_pricing_api_applies_selected_price_list_and_customer_context(self):
        retail = get_product_price(
            self.product.name,
            "COMPANY",
            company=self.company.name,
            contact=self.contact.name,
            price_list=self.retail.name,
        )
        wholesale = get_product_price(
            self.product.name,
            "COMPANY",
            company=self.company.name,
            contact=self.contact.name,
            price_list=self.wholesale.name,
        )
        self.assertEqual((Decimal(retail["price"]), retail["source"]), (Decimal("90"), "price_list"))
        self.assertEqual((Decimal(wholesale["price"]), wholesale["source"]), (Decimal("80"), "price_list"))

        self.company.price_list = self.wholesale.name
        self.company.save()
        customer_price = get_product_price(
            self.product.name,
            "COMPANY",
            company=self.company.name,
            contact=self.contact.name,
        )
        self.assertEqual(
            (Decimal(customer_price["price"]), customer_price["price_list"]),
            (Decimal("80"), self.wholesale.name),
        )
