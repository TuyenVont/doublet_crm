import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date, cint, get_datetime, now_datetime


ALLOWED_REFERENCES = {
    "DoubleT Lead", "DoubleT Deal", "DoubleT Contact", "DoubleT Company",
}
STATUSES = {"Scheduled", "Completed", "Cancelled"}
REFERENCE_TITLE_FIELDS = {
    "DoubleT Lead": "first_name",
    "DoubleT Deal": "deal_title",
    "DoubleT Contact": "first_name",
    "DoubleT Company": "company_name",
}
REMINDER_OFFSETS = {
    "15 Minutes Before": 15,
    "30 Minutes Before": 30,
    "1 Hour Before": 60,
    "1 Day Before": 1440,
}


class DoubleTAppointment(Document):
    def validate(self):
        self.title = (self.title or "").strip()
        if not self.title:
            frappe.throw(_("Title is required."))
        if self.status not in STATUSES:
            frappe.throw(_("Invalid appointment status."))
        if get_datetime(self.ends_on) < get_datetime(self.starts_on):
            frappe.throw(_("End time cannot be before start time."))
        self._set_reminder_from_type()
        if self.reminder_at and get_datetime(self.reminder_at) > get_datetime(self.starts_on):
            frappe.throw(_("Reminder time cannot be after the appointment start time."))
        self._validate_assignee()
        self._validate_reference()
        self._reset_changed_reminder()

    def _validate_assignee(self):
        enabled = frappe.db.get_value("User", self.assigned_to, "enabled")
        if not enabled or self.assigned_to == "Guest":
            frappe.throw(_("Select an enabled system user as the assignee."))

    def _validate_reference(self):
        if not self.reference_doctype and not self.reference_docname:
            return
        if not self.reference_doctype or not self.reference_docname:
            frappe.throw(_("Both related record type and record are required."))
        if self.reference_doctype not in ALLOWED_REFERENCES:
            frappe.throw(_("Unsupported related record type."))
        reference = frappe.get_doc(self.reference_doctype, self.reference_docname)
        reference.check_permission("read")

    def _reset_changed_reminder(self):
        previous = self.get_doc_before_save()
        if not previous:
            return
        reminder_fields = ("reminder_type", "reminder_at", "starts_on", "assigned_to", "status")
        if any(self.has_value_changed(field) for field in reminder_fields):
            self.reminder_sent_at = None

    def _set_reminder_from_type(self):
        reminder_type = self.get("reminder_type") or ("Custom" if self.reminder_at else "No Reminder")
        if reminder_type == "No Reminder":
            self.reminder_type = reminder_type
            self.reminder_at = None
            self.reminder_sent_at = None
            return
        if reminder_type == "Custom":
            if not self.reminder_at:
                frappe.throw(_("Select a custom reminder date and time."))
            self.reminder_type = reminder_type
            return
        if reminder_type not in REMINDER_OFFSETS:
            frappe.throw(_("Invalid reminder option."), frappe.ValidationError)
        self.reminder_type = reminder_type
        self.reminder_at = add_to_date(get_datetime(self.starts_on), minutes=-REMINDER_OFFSETS[reminder_type], as_datetime=True)


def _reference_labels(rows):
    labels = {}
    for doctype, title_field in REFERENCE_TITLE_FIELDS.items():
        names = {row.reference_docname for row in rows if row.reference_doctype == doctype and row.reference_docname}
        if not names or not frappe.has_permission(doctype, "read"):
            continue
        readable = frappe.get_list(
            doctype,
            filters={"name": ["in", list(names)]},
            fields=["name", title_field],
            limit_page_length=0,
        )
        labels.update({(doctype, row.name): row.get(title_field) or row.name for row in readable})
    return labels


@frappe.whitelist()
def list_appointments(search=None, status=None, assigned_to=None, time_filter="upcoming", limit_start=0, limit_page_length=20):
    """Permission-scoped server filtering and pagination for the Appointment list."""
    frappe.has_permission("DoubleT Appointment", "read", throw=True)
    limit_start = max(0, cint(limit_start))
    limit_page_length = min(100, max(1, cint(limit_page_length) or 20))
    filters = []
    if status:
        if status not in STATUSES:
            frappe.throw(_("Invalid appointment status."), frappe.ValidationError)
        filters.append(["status", "=", status])
    if assigned_to:
        filters.append(["assigned_to", "=", assigned_to])
    if time_filter == "upcoming":
        filters.append(["ends_on", ">=", now_datetime()])
    elif time_filter == "past":
        filters.append(["ends_on", "<", now_datetime()])
    elif time_filter != "all":
        frappe.throw(_("Invalid appointment time filter."), frappe.ValidationError)

    term = (search or "").strip()
    or_filters = []
    if term:
        pattern = f"%{term}%"
        or_filters = [[field, "like", pattern] for field in ("name", "title", "description", "location", "reference_docname")]

    fields = [
        "name", "title", "description", "starts_on", "ends_on", "assigned_to", "status",
        "meeting_type", "location", "reference_doctype", "reference_docname", "reminder_at", "reminder_sent_at",
    ]
    rows = frappe.get_list(
        "DoubleT Appointment",
        filters=filters,
        or_filters=or_filters,
        fields=fields,
        order_by="starts_on asc, name asc",
        limit_start=limit_start,
        limit_page_length=limit_page_length,
    )
    count = frappe.get_list(
        "DoubleT Appointment",
        filters=filters,
        or_filters=or_filters,
        fields=["count(*) as total"],
        order_by=None,
        limit_page_length=1,
    )
    labels = _reference_labels(rows)
    for row in rows:
        row["reference_label"] = labels.get((row.reference_doctype, row.reference_docname))
    return {"rows": rows, "total": cint(count[0].total) if count else 0}


@frappe.whitelist()
def get_appointment_defaults():
    if frappe.session.user == "Guest":
        frappe.throw(_("Authentication required."), frappe.PermissionError)
    starts_on = now_datetime().replace(second=0, microsecond=0)
    return {
        "starts_on": starts_on,
        "ends_on": add_to_date(starts_on, minutes=30, as_datetime=True),
    }
