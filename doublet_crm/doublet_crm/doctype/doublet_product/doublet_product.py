
import hashlib
import json

import frappe
from frappe import _
from frappe.model.naming import make_autoname
from frappe.model.document import Document
from frappe.utils import flt


SKU_NAMING_SERIES = "PRD-.#####"
PRODUCT_KINDS = {"Standard", "Template", "Variant"}


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
        self.product_kind = self.product_kind or "Standard"

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

        self.validate_categories()
        self.validate_product_kind()

        if not self.is_new():
            old_sku = frappe.db.get_value(
                self.doctype, self.name, "sku"
            )

            if old_sku and self.sku != old_sku:
                frappe.throw(
                    _("SKU cannot be changed after creation")
                )

    def validate_categories(self):
        """Keep the legacy primary category while maintaining the full category list."""
        categories = set()
        for row in self.categories:
            row.category = (row.category or "").strip()
            if not row.category:
                frappe.throw(_("A category assignment requires a category"))
            if row.category in categories:
                frappe.throw(_("A category can only be assigned once"))
            categories.add(row.category)

        if self.category and self.category not in categories:
            self.append("categories", {"category": self.category})

    def validate_product_kind(self):
        if self.product_kind not in PRODUCT_KINDS:
            frappe.throw(_("Product Kind must be Standard, Template, or Variant"))

        previous = self.get_doc_before_save()
        if previous and previous.product_kind == "Variant" and self.product_kind != "Variant":
            frappe.throw(_("Variant Product Kind cannot be changed after creation"))

        if self.product_kind == "Standard":
            if self.variant_of or self.variant_attributes:
                frappe.throw(_("Standard Products cannot have variant details"))
            self.variant_of = None
            self.variant_signature = None
            self.variant_key = None
            return

        if self.product_kind == "Template":
            if self.variant_of or self.variant_attributes:
                frappe.throw(_("Product Templates cannot have variant details"))
            self.variant_of = None
            self.variant_signature = None
            self.variant_key = None
            return

        self.validate_variant()

    def is_sellable(self):
        """Return whether this Product can be sold under Product V2 semantics.

        A Template is never sellable. A Variant's activity is independent of its
        Template's activity; the Variant itself is the item offered for sale.
        """
        return self.product_kind != "Template" and bool(self.is_active)

    def validate_variant(self):
        if not self.variant_of:
            frappe.throw(_("A Variant must reference a Product Template"))
        if self.variant_of == self.name:
            frappe.throw(_("A Variant cannot reference itself as its Template"))

        parent_kind = frappe.db.get_value("DoubleT Product", self.variant_of, "product_kind")
        if not parent_kind:
            frappe.throw(_("Variant Template {0} does not exist").format(self.variant_of))
        if parent_kind != "Template":
            frappe.throw(_("Variants must reference a Product Template"))

        signature = self.variant_attribute_signature()
        if not signature:
            frappe.throw(_("A Variant requires at least one attribute and value"))

        self.variant_signature = signature
        self.variant_key = hashlib.sha256(
            "{0}\x1f{1}".format(self.variant_of, signature).encode()
        ).hexdigest()

        duplicate = frappe.db.exists(self.doctype, {"variant_key": self.variant_key})
        if duplicate and (self.is_new() or duplicate != self.name):
            frappe.throw(
                _("A Variant with this Template and attribute combination already exists"),
                frappe.DuplicateEntryError,
            )

        previous = self.get_doc_before_save()
        if previous and (
            self.variant_of != previous.variant_of
            or signature != self.signature_for(previous.variant_attributes)
        ):
            frappe.throw(_("Variant Template and attributes cannot be changed after creation"))

    def variant_attribute_signature(self):
        return self.signature_for(self.variant_attributes)

    @staticmethod
    def signature_for(attributes):
        pairs = []
        attribute_names = set()
        for row in attributes:
            attribute_name = (row.attribute_name or "").strip()
            attribute_value = (row.attribute_value or "").strip()
            if not attribute_name or not attribute_value:
                frappe.throw(_("Each Variant Attribute requires a name and value"))
            normalized_name = attribute_name.casefold()
            if normalized_name in attribute_names:
                frappe.throw(_("A Variant Attribute can only be used once"))
            attribute_names.add(normalized_name)
            row.attribute_name = attribute_name
            row.attribute_value = attribute_value
            pairs.append((normalized_name, attribute_value))

        return json.dumps(sorted(pairs), separators=(",", ":"), ensure_ascii=False) if pairs else None
