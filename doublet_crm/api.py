from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import frappe
from frappe import _
from frappe.utils import cstr, get_datetime, get_system_timezone, now

from doublet_crm.doublet_crm.doctype.doublet_call_log.doublet_call_log import normalize_phone_number


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
        "name": deal.name,
        "stage": deal.stage,
        "lost_reason": deal.lost_reason,
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


@frappe.whitelist()
def get_call_log_stats():
    """Permission-aware Call Log statistics."""
    if not frappe.has_permission("DoubleT Call Log", "read"):
        frappe.throw(
            _("Not permitted to read Call Logs."),
            frappe.PermissionError,
        )

    rows = frappe.get_list(
        "DoubleT Call Log",
        fields=[
            "status",
            "count(name) as call_count",
            "sum(duration) as duration_sum",
        ],
        group_by="status",
        order_by="status asc",
        limit_page_length=20,
    )

    total = sum(int(row.call_count or 0) for row in rows)
    completed = sum(
        int(row.call_count or 0)
        for row in rows if row.status == "Completed"
    )
    missed = sum(
        int(row.call_count or 0)
        for row in rows
        if row.status in ("Missed", "No Answer")
    )
    total_duration = sum(
        float(row.duration_sum or 0) for row in rows
    )

    return {
        "total": total,
        "completed": completed,
        "missed": missed,
        "avg_duration": (
            round(total_duration / total) if total else 0
        ),
    }


@frappe.whitelist()
def get_call_logs_page(
    page=1, page_size=25,
    search=None, status=None, call_type=None,
):
    """Return permission-aware paginated Call Logs."""
    if not frappe.has_permission("DoubleT Call Log", "read"):
        frappe.throw(
            _("Not permitted to read Call Logs."),
            frappe.PermissionError,
        )

    try:
        page = int(page)
        page_size = int(page_size)
    except (TypeError, ValueError):
        frappe.throw(
            _("Invalid pagination parameters."),
            frappe.ValidationError,
        )

    if page < 1 or not 1 <= page_size <= 100:
        frappe.throw(
            _("Invalid page or page size."),
            frappe.ValidationError,
        )

    status = cstr(status).strip()
    call_type = cstr(call_type).strip()
    search = cstr(search).strip()[:100]

    if status and status not in CALL_LOG_STATUSES:
        frappe.throw(_("Invalid Call Log status."))

    if call_type and call_type not in CALL_LOG_TYPES:
        frappe.throw(_("Invalid Call Type."))

    filters = {}
    if status:
        filters["status"] = status
    if call_type:
        filters["call_type"] = call_type

    or_filters = None
    if search:
        pattern = f"%{search}%"
        or_filters = {
            field: ["like", pattern]
            for field in (
                "from_number", "to_number", "agent",
                "reference_name", "reference_doctype",
                "external_call_id", "line_number",
                "status", "call_type",
            )
        }

    kwargs = {
        "filters": filters,
        "or_filters": or_filters,
    }

    counts = frappe.get_list(
        "DoubleT Call Log",
        fields=["count(name) as total"],
        limit_page_length=1,
        **kwargs,
    )
    total = int(counts[0].total or 0) if counts else 0

    rows = frappe.get_list(
        "DoubleT Call Log",
        fields=[
            "name", "agent", "line_number", "call_type",
            "duration", "start_time", "end_time", "status",
            "from_number", "to_number", "recording_url",
            "reference_doctype", "reference_name",
            "note", "external_call_id", "creation",
            "modified",
        ],
        order_by="start_time desc, creation desc",
        start=(page - 1) * page_size,
        page_length=page_size,
        **kwargs,
    )

    return {
        "rows": rows,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
