import frappe
from frappe import _
from frappe.model.document import Document


class DoubleTCallEvent(Document):
	def validate_share(self, share):
		frappe.throw(_("Call events follow the case assignment."), frappe.PermissionError)
