import frappe
from frappe import _
from frappe.model.document import Document

ALLOWED_REFERENCES = {
    "DoubleT Lead", "DoubleT Deal", "DoubleT Contact", "DoubleT Company"
}


class DoubleTTask(Document):
    def validate(self):
        if self.reference_doctype or self.reference_docname:
            if not self.reference_doctype or not self.reference_docname:
                frappe.throw(_("Both related record type and record are required"))
            if self.reference_doctype not in ALLOWED_REFERENCES:
                frappe.throw(_("Unsupported related record type"))
            if not frappe.db.exists(self.reference_doctype, self.reference_docname):
                frappe.throw(_("Related record does not exist"))
            if not frappe.has_permission(self.reference_doctype, "read", self.reference_docname):
                frappe.throw(_("Not permitted to access related record"), frappe.PermissionError)
