import frappe
from frappe import _
from frappe.model.document import Document

ALLOWED_REFERENCES = {
	"DoubleT Lead",
	"DoubleT Deal",
	"DoubleT Contact",
	"DoubleT Company",
}


class DoubleTNote(Document):
	def validate(self):
		if self.reference_doctype not in ALLOWED_REFERENCES:
			frappe.throw(_("Unsupported related record type"), frappe.ValidationError)
		if not frappe.db.exists(self.reference_doctype, self.reference_name):
			frappe.throw(_("Related record does not exist"), frappe.DoesNotExistError)
		if not frappe.has_permission(self.reference_doctype, "read", self.reference_name):
			frappe.throw(_("Not permitted to access related record"), frappe.PermissionError)
