import frappe
from frappe.tests.utils import FrappeTestCase


class TestDoubleTPriceList(FrappeTestCase):
    def setUp(self):
        self.suffix = frappe.generate_hash(length=10)
        self.category = frappe.get_doc(
            {
                "doctype": "DoubleT Product Category",
                "category_name": f"Price List Category {self.suffix}",
            }
        ).insert()
        self.standard = self.make_product("Standard")
        self.template = self.make_product("Template", product_kind="Template")
        self.variant = self.make_product(
            "Variant",
            product_kind="Variant",
            variant_of=self.template.name,
            variant_attributes=[
                {"attribute_name": "Color", "attribute_value": "Red"}
            ],
        )

    def make_product(self, label, **values):
        product = frappe.get_doc(
            {
                "doctype": "DoubleT Product",
                "product_name": f"{label} Price List Product {self.suffix}",
                "sku": f"PRICE-LIST-{label.upper()}-{self.suffix}",
                "category": self.category.name,
                "price": 100,
                **values,
            }
        )
        return product.insert()

    def make_price_list(self, **values):
        return frappe.get_doc(
            {
                "doctype": "DoubleT Price List",
                "price_list_name": f"Price List {self.suffix}",
                **values,
            }
        )

    def test_allows_standard_and_variant_products(self):
        price_list = self.make_price_list(
            items=[
                {"product": self.standard.name, "price": 90},
                {"product": self.variant.name, "price": 110},
            ]
        ).insert()
        self.assertEqual([row.product for row in price_list.items], [self.standard.name, self.variant.name])

    def test_rejects_duplicate_products_and_negative_prices(self):
        with self.assertRaises(frappe.ValidationError):
            self.make_price_list(
                items=[
                    {"product": self.standard.name, "price": 100},
                    {"product": self.standard.name, "price": 90},
                ]
            ).insert()
        with self.assertRaises(frappe.ValidationError):
            self.make_price_list(items=[{"product": self.standard.name, "price": -1}]).insert()

    def test_rejects_template_products(self):
        with self.assertRaises(frappe.ValidationError):
            self.make_price_list(items=[{"product": self.template.name, "price": 100}]).insert()

    def test_price_list_name_is_unique(self):
        self.make_price_list().insert()
        with self.assertRaises(frappe.DuplicateEntryError):
            self.make_price_list().insert()
