import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


SELLABLE_PRODUCT_KINDS = {"Standard", "Variant"}


class DoubleTPriceList(Document):
    def autoname(self):
        self.price_list_name = (self.price_list_name or "").strip()
        self.name = self.price_list_name

    def validate(self):
        self.price_list_name = (self.price_list_name or "").strip()
        if not self.price_list_name:
            frappe.throw(_("Price List Name is required"))

        self.validate_default()
        self.validate_items()

    def validate_default(self):
        if not self.is_default:
            return

        existing_default = frappe.db.get_value(
            self.doctype,
            {"is_default": 1},
            "name",
        )
        if existing_default and existing_default != self.name:
            frappe.throw(_("Only one Price List can be the default"))

    def validate_items(self):
        products = set()
        for row in self.items:
            if row.product in products:
                frappe.throw(_("A Product can only appear once in a Price List"))
            products.add(row.product)

            if flt(row.price) < 0:
                frappe.throw(_("Price List Item price cannot be negative"))

            product_kind = frappe.db.get_value(
                "DoubleT Product", row.product, "product_kind"
            )
            # Products created before Product V2 are Standard by definition.
            product_kind = product_kind or "Standard"
            if product_kind not in SELLABLE_PRODUCT_KINDS:
                frappe.throw(_("Product Templates cannot be added to a Price List"))
