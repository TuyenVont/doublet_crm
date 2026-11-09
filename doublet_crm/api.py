from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import frappe
from frappe import _
from frappe.utils import cstr, get_datetime, get_system_timezone, now

from doublet_crm.doublet_crm.doctype.doublet_call_log.doublet_call_log import normalize_phone_number
from doublet_crm.doublet_crm.doctype.doublet_note.doublet_note import ALLOWED_REFERENCES


def _note_reference_label(doctype, docname):
    """Readable reference name for centralized Notes; keep docname as the link ID."""
    record = frappe.get_doc(doctype, docname)
    if doctype in ("DoubleT Lead", "DoubleT Contact"):
        label = record.get("full_name") or " ".join(
            part.strip()
            for part in (record.get("first_name"), record.get("last_name"))
            if isinstance(part, str) and part.strip()
        )
    elif doctype == "DoubleT Deal":
        label = record.get("deal_title")
    elif doctype == "DoubleT Company":
        label = record.get("company_name")
    else:
        label = None
    return str(label or record.get_title() or docname).strip()


@frappe.whitelist()
def get_notes(search: str | None = None, reference_doctype: str | None = None):
    frappe.has_permission("DoubleT Note", "read", throw=True)
    if reference_doctype and reference_doctype not in ALLOWED_REFERENCES:
        frappe.throw(_("Unsupported reference DocType"), frappe.ValidationError)

    filters = {"reference_doctype": reference_doctype} if reference_doctype else {}
    term = (search or "").strip()
    or_filters = None
    if term:
        pattern = f"%{term}%"
        or_filters = {
            "title": ["like", pattern],
            "content": ["like", pattern],
            "reference_name": ["like", pattern],
        }

    notes = frappe.get_list(
        "DoubleT Note",
        filters=filters,
        or_filters=or_filters,
        fields=[
            "name",
            "title",
            "content",
            "reference_doctype",
            "reference_name",
            "owner",
            "modified",
            "creation",
        ],
        order_by="modified desc",
        limit_page_length=500,
    )
    visible_notes = []
    reference_labels = {}
    for note in notes:
        if not (
            frappe.db.exists(note.reference_doctype, note.reference_name)
            and frappe.has_permission(note.reference_doctype, "read", note.reference_name)
        ):
            continue
        reference = (note.reference_doctype, note.reference_name)
        if reference not in reference_labels:
            reference_labels[reference] = _note_reference_label(*reference)
        note["reference_label"] = reference_labels[reference]
        visible_notes.append(note)
    return visible_notes


@frappe.whitelist()
def get_linked_notes(doctype: str, docname: str):
    if doctype not in ALLOWED_REFERENCES:
        frappe.throw(_("Unsupported reference DocType"), frappe.ValidationError)

    if not frappe.db.exists(doctype, docname):
        frappe.throw(_("Document not found"), frappe.DoesNotExistError)
    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    return frappe.get_list(
        "DoubleT Note",
        filters={"reference_doctype": doctype, "reference_name": docname},
        fields=[
            "name",
            "title",
            "content",
            "reference_doctype",
            "reference_name",
            "owner",
            "modified",
            "creation",
        ],
        order_by="modified desc",
    )


@frappe.whitelist()
def get_linked_tasks(doctype: str, docname: str):
    supported_doctypes = {
        "DoubleT Lead",
        "DoubleT Deal",
        "DoubleT Contact",
        "DoubleT Company",
    }
    if doctype not in supported_doctypes:
        frappe.throw(_("Unsupported reference DocType"), frappe.ValidationError)

    if not frappe.db.exists(doctype, docname):
        frappe.throw(_("Document not found"), frappe.DoesNotExistError)
    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    tasks = frappe.get_list(
        "DoubleT Task",
        filters={"reference_doctype": doctype, "reference_docname": docname},
        fields=[
            "name",
            "title",
            "description",
            "assigned_to",
            "due_date",
            "priority",
            "status",
            "modified",
            "creation",
        ],
    )
    return [[], [], [], tasks, []]


@frappe.whitelist()
def update_deal_stage(deal_name, stage, lost_reason=None):
    if not frappe.db.exists("DoubleT Deal", deal_name):
        frappe.throw(_("Deal does not exist"))

    if not frappe.db.exists("DoubleT Deal Stage", stage):
        frappe.throw(_("Deal Stage does not exist"))

    stage_doc = frappe.get_doc(
        "DoubleT Deal Stage",
        stage,
    )

    if not stage_doc.enabled:
        frappe.throw(
            _("Deal Stage is disabled"),
            frappe.ValidationError,
        )

    deal = frappe.get_doc(
        "DoubleT Deal",
        deal_name,
    )

    deal.check_permission("write")

    target_type = (
        stage_doc.stage_type or ""
    ).upper()

    deal.stage = stage

    if target_type == "LOST":
        reason = (
            lost_reason or ""
        ).strip()

        if not reason:
            frappe.throw(
                _(
                    "Lost Reason is required"
                ),
                frappe.ValidationError,
            )

        deal.lost_reason = reason

    deal.save()

    return {
        "stage": deal.stage,
        "lost_reason": deal.lost_reason,
        "won_on": deal.won_on,
        "lost_on": deal.lost_on,
    }

CALL_LOG_API_ROLE = "Call Log API"

CALL_LOG_TYPES = {
    "Incoming",
    "Outgoing",
    "Incoming Forwarded",
    "Callback",
}

CALL_LOG_STATUSES = {
    "Completed",
    "Missed",
    "Canceled",
    "Failed",
    "Busy",
    "No Answer",
}


def _require_call_log_api_role():
    if CALL_LOG_API_ROLE not in frappe.get_roles():
        frappe.throw(
            _("You are not permitted to create Call Logs through this API."),
            frappe.PermissionError,
        )


def _parse_call_log_datetime(value, field_label, required=False):
    value = cstr(value).strip()

    if not value:
        if required:
            frappe.throw(
                _("{0} is required.").format(field_label),
                frappe.ValidationError,
            )
        return None

    try:
        parsed = get_datetime(value)
    except Exception:
        parsed = None

    if not parsed:
        frappe.throw(
            _("{0} must be a valid ISO 8601 datetime.").format(field_label),
            frappe.ValidationError,
        )

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        frappe.throw(
            _(
                "{0} must include a timezone offset, "
                "for example 2026-10-29T10:00:00+07:00."
            ).format(field_label),
            frappe.ValidationError,
        )

    try:
        system_timezone = ZoneInfo(get_system_timezone())
    except ZoneInfoNotFoundError:
        frappe.throw(
            _("The system timezone configuration is invalid."),
            frappe.ValidationError,
        )

    return (
        parsed.astimezone(system_timezone)
        .replace(tzinfo=None)
    )



def _parse_call_log_phone(value, field_label):
    value = cstr(value).strip()

    if not value:
        return None

    normalized = normalize_phone_number(value)

    if not normalized:
        frappe.throw(
            _("{0} is not a valid phone number.").format(field_label),
            frappe.ValidationError,
        )

    return normalized

def _parse_call_log_duration(value):
    if value is None or value == "":
        return 0

    try:
        duration = int(value)
    except (TypeError, ValueError):
        frappe.throw(
            _("Duration must be an integer number of seconds."),
            frappe.ValidationError,
        )

    if duration < 0:
        frappe.throw(
            _("Duration cannot be negative."),
            frappe.ValidationError,
        )

    return duration


@frappe.whitelist(methods=["POST"])
def create_call_log(
    agent,
    call_type,
    start_time,
    status,
    external_call_id,
    line_number=None,
    duration=0,
    end_time=None,
    from_number=None,
    to_number=None,
    recording_url=None,
    note=None,
    reference_doctype=None,
    reference_name=None,
):
    """Create one DoubleT Call Log from an authenticated integration."""

    _require_call_log_api_role()

    agent = cstr(agent).strip()
    call_type = cstr(call_type).strip()
    status = cstr(status).strip()
    external_call_id = cstr(external_call_id).strip()

    if not agent:
        frappe.throw(
            _("Agent is required."),
            frappe.ValidationError,
        )

    if not external_call_id:
        frappe.throw(
            _("External Call ID is required."),
            frappe.ValidationError,
        )

    if call_type not in CALL_LOG_TYPES:
        frappe.throw(
            _("Invalid Call Type: {0}").format(call_type),
            frappe.ValidationError,
        )

    if status not in CALL_LOG_STATUSES:
        frappe.throw(
            _("Invalid Status: {0}").format(status),
            frappe.ValidationError,
        )

    existing_name = frappe.db.get_value(
        "DoubleT Call Log",
        {"external_call_id": external_call_id},
        "name",
    )

    if existing_name:
        return {
            "name": existing_name,
            "external_call_id": external_call_id,
            "duplicate": True,
        }

    start_time = _parse_call_log_datetime(
        start_time,
        _("Start Time"),
        required=True,
    )

    end_time = _parse_call_log_datetime(
        end_time,
        _("End Time"),
    )

    if end_time and end_time < start_time:
        frappe.throw(
            _("End Time cannot be earlier than Start Time."),
            frappe.ValidationError,
        )

    duration = _parse_call_log_duration(duration)

    doc = frappe.get_doc({
        "doctype": "DoubleT Call Log",
        "agent": agent,
        "line_number": cstr(line_number).strip() or None,
        "call_type": call_type,
        "duration": duration,
        "start_time": start_time,
        "end_time": end_time,
        "status": status,
        "from_number": _parse_call_log_phone(
            from_number,
            _("From Number"),
        ),
        "to_number": _parse_call_log_phone(
            to_number,
            _("To Number"),
        ),
        "recording_url": cstr(recording_url).strip() or None,
        "reference_doctype": (
            cstr(reference_doctype).strip() or None
        ),
        "reference_name": (
            cstr(reference_name).strip() or None
        ),
        "note": cstr(note).strip() or None,
        "external_call_id": external_call_id,
    })

    try:
        doc.insert()

    except frappe.DuplicateEntryError:
        existing_name = frappe.db.get_value(
            "DoubleT Call Log",
            {"external_call_id": external_call_id},
            "name",
        )

        if existing_name:
            return {
                "name": existing_name,
                "external_call_id": external_call_id,
                "duplicate": True,
            }

        raise

    return {
        "name": doc.name,
        "external_call_id": doc.external_call_id,
        "reference_doctype": doc.reference_doctype,
        "reference_name": doc.reference_name,
        "duplicate": False,
    }
