import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date, get_datetime

ALLOWED_REFERENCES = {
    "DoubleT Lead", "DoubleT Deal", "DoubleT Contact", "DoubleT Company"
}
REMINDER_OFFSETS = {
    "15 Minutes Before": 15,
    "30 Minutes Before": 30,
    "1 Hour Before": 60,
    "1 Day Before": 1440,
}


class DoubleTTask(Document):
    def validate(self):
        self.validate_callback()
        self.validate_reminder()
        if self.reference_doctype or self.reference_docname:
            if not self.reference_doctype or not self.reference_docname:
                frappe.throw(_("Both related record type and record are required"))
            if self.reference_doctype not in ALLOWED_REFERENCES:
                frappe.throw(_("Unsupported related record type"))
            if not frappe.db.exists(self.reference_doctype, self.reference_docname):
                frappe.throw(_("Related record does not exist"))
            if not frappe.has_permission(self.reference_doctype, "read", self.reference_docname):
                frappe.throw(_("Not permitted to access related record"), frappe.PermissionError)

    def validate_reminder(self):
        reminder_type = self.get("reminder_type") or ("Custom" if self.reminder_at else "No Reminder")
        if reminder_type == "No Reminder":
            self.reminder_type = reminder_type
            self.reminder_at = None
            self.reminder_sent_at = None
        elif reminder_type == "Custom":
            self.reminder_type = reminder_type
            if not self.reminder_at:
                frappe.throw(_("Select a custom reminder date and time."))
        elif reminder_type in REMINDER_OFFSETS:
            if not self.due_date:
                frappe.throw(_("Set a due date before adding a reminder."))
            self.reminder_type = reminder_type
            self.reminder_at = add_to_date(get_datetime(self.due_date), minutes=-REMINDER_OFFSETS[reminder_type], as_datetime=True)
        else:
            frappe.throw(_("Invalid reminder option."), frappe.ValidationError)
        if self.reminder_at and not self.due_date:
            frappe.throw(_("Set a due date before adding a reminder."))
        if self.reminder_at and get_datetime(self.reminder_at) > get_datetime(self.due_date):
            frappe.throw(_("Reminder time cannot be after the due date."))
        previous = self.get_doc_before_save()
        if previous and any(self.has_value_changed(field) for field in ("reminder_type", "reminder_at", "due_date", "assigned_to", "status")):
            self.reminder_sent_at = None

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
