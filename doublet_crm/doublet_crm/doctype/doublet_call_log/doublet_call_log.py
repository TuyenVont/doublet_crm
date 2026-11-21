import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime
from phonenumbers import (
    NumberParseException,
    PhoneNumberFormat,
    format_number,
    is_valid_number,
    parse,
)


ALLOWED_REFERENCE_DOCTYPES = {"DoubleT Lead", "DoubleT Contact"}

INCOMING_CALL_TYPES = {"Incoming", "Incoming Forwarded"}
OUTGOING_CALL_TYPES = {"Outgoing", "Callback"}
MISSED_STATUSES = {"Missed", "No Answer"}
HANDLING_STATUSES = ("Waiting", "In Progress", "Resolved")


def is_missed_incoming(call):
    return call.call_type in INCOMING_CALL_TYPES and call.status in MISSED_STATUSES


class DoubleTCallLog(Document):
    def validate(self):
        self.validate_duration()
        self.validate_times()
        self.validate_reference()
        self.normalize_phone_fields()

        previous = self.get_doc_before_save()
        number_fields = ("call_type", "from_number", "to_number")
        needs_matching = previous is None or any(self.get(field) != previous.get(field) for field in number_fields)
        if needs_matching and not self.flags.call_case_workflow and not self.reference_doctype and not self.reference_name:
            self.auto_link_reference()

        self.validate_case_fields()
        self.queue_priority = int(self.handling_status == "Waiting" and is_missed_incoming(self))

    def validate_case_fields(self):
        if self.flags.call_case_workflow:
            return

        if self.is_new():
            if self.assigned_to or self.handling_status not in (None, "", "Waiting"):
                frappe.throw(_("Use Contact Center to update call handling."))
            self.handling_status = "Waiting"
            return

        previous = self.get_doc_before_save()
        fields = ("handling_status", "assigned_to")
        if any((self.get(field) or "") != (previous.get(field) or "") for field in fields):
            frappe.throw(_("Use Contact Center to update call handling."))

        callback_fields = ("reference_doctype", "reference_name", "call_type", "status")
        if any((self.get(field) or "") != (previous.get(field) or "") for field in callback_fields):
            if frappe.db.get_value("DoubleT Task", {"callback_call_log": self.name}, "name", for_update=True):
                frappe.throw(_("This call is linked to a callback task. Update its customer from Contact Center."))

    def validate_duration(self):
        if (self.duration or 0) < 0:
            frappe.throw(_("Duration cannot be negative."))

    def validate_times(self):
        if not self.start_time or not self.end_time:
            return

        start_time = get_datetime(self.start_time)
        end_time = get_datetime(self.end_time)

        if end_time < start_time:
            frappe.throw(_("End Time cannot be earlier than Start Time."))

    def validate_reference(self):
        if bool(self.reference_doctype) != bool(self.reference_name):
            frappe.throw(
                _("Reference DocType and Reference Name must be set together.")
            )

        if (
            self.reference_doctype
            and self.reference_doctype not in ALLOWED_REFERENCE_DOCTYPES
        ):
            frappe.throw(
                _("Reference DocType must be DoubleT Lead or DoubleT Contact.")
            )

    def normalize_phone_fields(self):
        for fieldname in ("from_number", "to_number"):
            value = self.get(fieldname)

            if not value:
                continue

            normalized = normalize_phone_number(value)

            if normalized:
                self.set(fieldname, normalized)

    def auto_link_reference(self):
        contact_number = get_contact_number(
            self.call_type,
            self.from_number,
            self.to_number,
        )

        if not contact_number:
            return

        matches = find_phone_matches(contact_number)

        if len(matches) == 1:
            match = matches[0]
            self.reference_doctype = match["doctype"]
            self.reference_name = match["name"]
            return

        if len(matches) > 1:
            message = _("Auto-link skipped: phone {0} matched multiple CRM records.").format(contact_number)
            if message not in (self.note or "").splitlines():
                append_note(self, message)


def normalize_phone_number(phone_number):
    if not phone_number:
        return None

    try:
        parsed = parse(str(phone_number).strip(), "VN")
    except NumberParseException:
        return None

    if not is_valid_number(parsed):
        return None

    return format_number(parsed, PhoneNumberFormat.E164)


def get_contact_number(call_type, from_number=None, to_number=None):
    if call_type in INCOMING_CALL_TYPES:
        return normalize_phone_number(from_number)

    if call_type in OUTGOING_CALL_TYPES:
        return normalize_phone_number(to_number)

    return None


def find_phone_matches(phone_number):
    normalized_target = normalize_phone_number(phone_number)

    if not normalized_target:
        return []

    matches = []

    for doctype in ("DoubleT Lead", "DoubleT Contact"):
        records = frappe.get_all(
            doctype,
            filters={"phone": ["is", "set"]},
            fields=["name", "phone"],
        )

        for record in records:
            if normalize_phone_number(record.phone) == normalized_target:
                matches.append(
                    {
                        "doctype": doctype,
                        "name": record.name,
                    }
                )

    return matches


def append_note(doc, message):
    if doc.note:
        doc.note = f"{doc.note}\n{message}"
    else:
        doc.note = message
