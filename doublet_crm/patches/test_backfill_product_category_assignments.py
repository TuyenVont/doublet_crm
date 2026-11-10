import frappe
from frappe.tests.utils import FrappeTestCase

from doublet_crm.patches.backfill_product_category_assignments import execute


class TestBackfillProductCategoryAssignments(FrappeTestCase):
    def setUp(self):
        self.suffix = frappe.generate_hash(length=10)
        self.category = frappe.get_doc(
            {
                "doctype": "DoubleT Product Category",
                "category_name": f"Migration Category {self.suffix}",
            }
        ).insert()
        self.other_category = frappe.get_doc(
            {
                "doctype": "DoubleT Product Category",
                "category_name": f"Migration Other Category {self.suffix}",
            }
        ).insert()
        self.product = frappe.get_doc(
            {
                "doctype": "DoubleT Product",
                "product_name": f"Migration Product {self.suffix}",
                "sku": f"MIGRATION-{self.suffix}",
                "category": self.category.name,
                "price": 125,
                "is_active": 0,
            }
        ).insert()
        frappe.db.delete(
            "DoubleT Product Category Assignment",
            {"parent": self.product.name, "parenttype": "DoubleT Product", "parentfield": "categories"},
        )

    def assignments(self):
        return frappe.get_all(
            "DoubleT Product Category Assignment",
            filters={"parent": self.product.name, "parenttype": "DoubleT Product", "parentfield": "categories"},
            pluck="category",
            order_by="category",
        )

    def test_backfills_legacy_category_without_changing_product_fields(self):
        before = frappe.db.get_value(
            "DoubleT Product",
            self.product.name,
            ("name", "sku", "category", "price", "is_active", "product_kind"),
            as_dict=True,
        )

        execute()
        execute()

        after = frappe.db.get_value(
            "DoubleT Product",
            self.product.name,
            ("name", "sku", "category", "price", "is_active", "product_kind"),
            as_dict=True,
        )
        self.assertEqual(after, before)
        self.assertEqual(self.assignments(), [self.category.name])

    def test_backfills_missing_legacy_category_in_a_partially_populated_table(self):
        frappe.get_doc(
            {
                "doctype": "DoubleT Product Category Assignment",
                "parent": self.product.name,
                "parenttype": "DoubleT Product",
                "parentfield": "categories",
                "category": self.other_category.name,
            }
        ).db_insert()

        execute()
        execute()

        self.assertEqual(
            self.assignments(),
            sorted([self.category.name, self.other_category.name]),
        )
