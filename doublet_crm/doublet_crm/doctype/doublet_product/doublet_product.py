
import frappe
from frappe import _
from frappe.model.naming import make_autoname
from frappe.model.document import Document
from frappe.utils import flt


SKU_NAMING_SERIES = "PRD-.#####"


def get_next_sku():
    """Allocate an unused SKU through Frappe's row-locked naming series."""
    while True:
        sku = make_autoname(SKU_NAMING_SERIES)
        if not frappe.db.exists("DoubleT Product", {"sku": sku}):
            return sku


@frappe.whitelist()
def get_suggested_sku():
    """Return a server-generated SKU suggestion for an authorized creator."""
    frappe.has_permission("DoubleT Product", "create", throw=True)
    return get_next_sku()


class DoubleTProduct(Document):
    def autoname(self):
        self.sku = (self.sku or "").strip() or get_next_sku()
        self.name = self.sku

    def validate(self):
        self.product_name = (self.product_name or "").strip()
        self.sku = (self.sku or "").strip()

        if not self.product_name:
            frappe.throw(_("Product Name is required"))

        if not self.sku:
            frappe.throw(_("SKU is required"))

        existing_sku = frappe.db.exists(self.doctype, {"sku": self.sku})
        if existing_sku and (self.is_new() or existing_sku != self.name):
            frappe.throw(
                _("A Product with SKU {0} already exists").format(self.sku),
                frappe.DuplicateEntryError,
            )

        if flt(self.price) < 0:
            frappe.throw(_("Price cannot be negative"))

        if not self.is_new():
            old_sku = frappe.db.get_value(
                self.doctype, self.name, "sku"
            )

            if old_sku and self.sku != old_sku:
                frappe.throw(
                    _("SKU cannot be changed after creation")
                )
