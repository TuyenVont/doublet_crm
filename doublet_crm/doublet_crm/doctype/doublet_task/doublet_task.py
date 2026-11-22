import frappe
from frappe import _
from frappe.model.document import Document

ALLOWED_REFERENCES = {
    "DoubleT Lead", "DoubleT Deal", "DoubleT Contact", "DoubleT Company"
}


class DoubleTTask(Document):
    def validate(self):
        self.validate_callback()
        if self.reference_doctype or self.reference_docname:
            if not self.reference_doctype or not self.reference_docname:
                frappe.throw(_("Both related record type and record are required"))
            if self.reference_doctype not in ALLOWED_REFERENCES:
                frappe.throw(_("Unsupported related record type"))
            if not frappe.db.exists(self.reference_doctype, self.reference_docname):
                frappe.throw(_("Related record does not exist"))
            if not frappe.has_permission(self.reference_doctype, "read", self.reference_docname):
                frappe.throw(_("Not permitted to access related record"), frappe.PermissionError)

    def validate_callback(self):
        self.callback_call_log = self.callback_call_log or None
        if self.flags.call_case_workflow:
            return
        previous = self.get_doc_before_save()
        if (
            self.callback_call_log or self.callback_result or self.callback_notes
            or (previous and previous.callback_call_log)
        ):
            frappe.throw(_("Update callback tasks from Contact Center."))

    def validate_share(self, share):
        if self.callback_call_log and (share.read or share.write or share.submit or share.share):
            frappe.throw(_("Callback task access follows the call assignment."), frappe.PermissionError)

    def on_trash(self):
        if self.callback_call_log:
            frappe.throw(_("Callback tasks are part of the call history."))


def revoke_callback_task_shares():
    """Revoke old callback grants without removing share metadata or touching ordinary tasks."""
    task = frappe.qb.DocType("DoubleT Task")
    docshare = frappe.qb.DocType("DocShare")
    callbacks = frappe.qb.from_(task).select(task.name).where(task.callback_call_log != "")
    (
        frappe.qb.update(docshare)
        .set(docshare.read, 0)
        .set(docshare.write, 0)
        .set(docshare.submit, 0)
        .set(docshare.share, 0)
        .where(docshare.share_doctype == "DoubleT Task")
        .where(docshare.share_name.isin(callbacks))
    ).run()
