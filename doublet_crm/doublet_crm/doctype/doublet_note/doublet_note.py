import frappe
from frappe import _
from frappe.model.document import Document

from doublet_crm.permissions import can_use_call_summary

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

		source = self.get("source_call_log") or None
		previous = self.get_doc_before_save()
		if previous:
			if source != (previous.get("source_call_log") or None) or (
				source and (self.reference_doctype, self.reference_name)
				!= (previous.reference_doctype, previous.reference_name)
			):
				frappe.throw(_("The source call and customer of a call note cannot be changed."))
		elif source:
			call = frappe.get_doc("DoubleT Call Log", source)
			call.check_permission("read")
			if not can_use_call_summary(call):
				frappe.throw(_("Not permitted to use this call's AI assistant."), frappe.PermissionError)
			if (self.reference_doctype, self.reference_name) != (call.reference_doctype, call.reference_name):
				frappe.throw(_("Select the customer linked to the source call."))
