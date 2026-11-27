import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime


ACTIVE_STATUS = {
    "DoubleT Appointment": {"Scheduled"},
    "DoubleT Task": {"Backlog", "Todo", "In Progress"},
}
TITLE_FIELD = {"DoubleT Appointment": "title", "DoubleT Task": "title"}
BATCH_SIZE = 200


def _can_receive_reminder(doc, user):
    return bool(
        user
        and user != "Guest"
        and frappe.db.get_value("User", user, "enabled")
        and frappe.has_permission(doc.doctype, "read", doc=doc, user=user)
    )


def _notification_link(doc):
    if doc.doctype == "DoubleT Appointment":
        return f"/doublet-crm/appointments/{doc.name}"
    return "/doublet-crm/tasks"


def _due_reminder_batch(doctype, statuses, current, cursor=None):
    """Return a stable name-keyset page so invalid rows cannot starve later reminders."""
    filters = [
        ["reminder_at", "<=", current],
        ["reminder_sent_at", "is", "not set"],
        ["status", "in", tuple(statuses)],
    ]
    if cursor:
        filters.append(["name", ">", cursor])
    return frappe.get_all(
        doctype,
        filters=filters,
        pluck="name",
        order_by="name asc",
        limit_page_length=BATCH_SIZE,
    )


def send_due_reminders(now=None):
    """Create one in-app alert per due reminder; safe when scheduler runs overlap."""
    current = get_datetime(now or now_datetime())
    sent = []
    for doctype, statuses in ACTIVE_STATUS.items():
        cursor = None
        while True:
            rows = _due_reminder_batch(doctype, statuses, current, cursor)
            if not rows:
                break
            for name in rows:
                doc = frappe.get_doc(doctype, name, for_update=True)
                if (
                    doc.reminder_sent_at
                    or not doc.reminder_at
                    or get_datetime(doc.reminder_at) > current
                    or doc.status not in statuses
                    or not _can_receive_reminder(doc, doc.assigned_to)
                ):
                    continue
                label = doc.get(TITLE_FIELD[doctype]) or doc.name
                frappe.get_doc({
                    "doctype": "Notification Log",
                    "subject": _("Reminder: {0}").format(label),
                    "email_content": _("This sales activity is due or coming up."),
                    "for_user": doc.assigned_to,
                    "type": "Alert",
                    "document_type": doc.doctype,
                    "document_name": doc.name,
                    "from_user": "Administrator",
                    "link": _notification_link(doc),
                }).insert(ignore_permissions=True)
                doc.db_set("reminder_sent_at", current, update_modified=False)
                sent.append((doctype, name, doc.assigned_to))
            next_cursor = rows[-1]
            if len(rows) < BATCH_SIZE or next_cursor == cursor:
                break
            cursor = next_cursor
    return sent
