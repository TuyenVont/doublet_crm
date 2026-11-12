from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import json

import frappe
from frappe import _
from frappe.utils import cint, cstr, get_datetime, get_system_timezone, now

from doublet_crm.doublet_crm.doctype.doublet_call_log.doublet_call_log import normalize_phone_number
from doublet_crm.doublet_crm.doctype.doublet_note.doublet_note import ALLOWED_REFERENCES


NOTE_FIELDS = [
    "name",
    "title",
    "content",
    "reference_doctype",
    "reference_name",
    "owner",
    "modified",
    "creation",
]
NOTE_ORDER_BY = "modified desc, name desc"
NOTE_LEGACY_PAGE_LENGTH = 500
NOTE_DEFAULT_PAGE_LENGTH = 20
NOTE_MAX_PAGE_LENGTH = 500
NOTE_SCAN_PAGE_LENGTH = 100
TASK_FIELDS = [
    "name",
    "title",
    "description",
    "assigned_to",
    "due_date",
    "priority",
    "status",
    "modified",
    "creation",
]
TASK_ORDER_BY = "modified desc, name desc"


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


def _page_value(value, default, minimum, label):
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        frappe.throw(_("{0} must be an integer").format(label), frappe.ValidationError)
    if parsed < minimum:
        frappe.throw(_("{0} must be at least {1}").format(label, minimum), frappe.ValidationError)
    return parsed


@frappe.whitelist()
def get_notes(
    search: str | None = None,
    reference_doctype: str | None = None,
    limit_start: int | str | None = None,
    limit_page_length: int | str | None = None,
    include_pagination: int | str = 0,
):
    frappe.has_permission("DoubleT Note", "read", throw=True)
    if reference_doctype and reference_doctype not in ALLOWED_REFERENCES:
        frappe.throw(_("Unsupported reference DocType"), frappe.ValidationError)

    paginated = limit_start is not None or limit_page_length is not None or cint(include_pagination)
    visible_start = _page_value(limit_start, 0, 0, _("Limit start"))
    page_length = _page_value(
        limit_page_length,
        NOTE_DEFAULT_PAGE_LENGTH if paginated else NOTE_LEGACY_PAGE_LENGTH,
        1,
        _("Page length"),
    )
    if page_length > NOTE_MAX_PAGE_LENGTH:
        frappe.throw(
            _("Page length cannot exceed {0}").format(NOTE_MAX_PAGE_LENGTH),
            frappe.ValidationError,
        )

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

    visible_notes = []
    reference_labels = {}
    candidate_start = 0
    target_count = visible_start + page_length + (1 if paginated else 0)

    # Page after checking the linked CRM record. Applying SQL pagination first
    # would let inaccessible records crowd accessible notes out of a page.
    while len(visible_notes) < target_count:
        notes = frappe.get_list(
            "DoubleT Note",
            filters=filters,
            or_filters=or_filters,
            fields=NOTE_FIELDS,
            order_by=NOTE_ORDER_BY,
            limit_start=candidate_start,
            limit_page_length=NOTE_SCAN_PAGE_LENGTH,
        )
        if not notes:
            break
        candidate_start += len(notes)

        for note in notes:
            if not (
                frappe.db.exists(note.reference_doctype, note.reference_name)
                and frappe.has_permission(
                    note.reference_doctype,
                    "read",
                    doc=note.reference_name,
                )
            ):
                continue
            reference = (note.reference_doctype, note.reference_name)
            if reference not in reference_labels:
                reference_labels[reference] = _note_reference_label(*reference)
            note["reference_label"] = reference_labels[reference]
            visible_notes.append(note)
            if len(visible_notes) >= target_count:
                break

        if len(notes) < NOTE_SCAN_PAGE_LENGTH:
            break

    page = visible_notes[visible_start:visible_start + page_length]
    if cint(include_pagination):
        return {
            "notes": page,
            "has_more": len(visible_notes) > visible_start + page_length,
            "limit_start": visible_start,
            "limit_page_length": page_length,
        }
    return page


@frappe.whitelist()
def get_linked_notes(
    doctype: str,
    docname: str,
    limit_start: int | str | None = None,
    limit_page_length: int | str | None = None,
    include_pagination: int | str = 0,
):
    frappe.has_permission("DoubleT Note", "read", throw=True)
    if doctype not in ALLOWED_REFERENCES:
        frappe.throw(_("Unsupported reference DocType"), frappe.ValidationError)

    if not frappe.db.exists(doctype, docname):
        frappe.throw(_("Document not found"), frappe.DoesNotExistError)
    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    paginated = limit_start is not None or limit_page_length is not None or cint(include_pagination)
    if not paginated:
        return frappe.get_list(
            "DoubleT Note",
            filters={"reference_doctype": doctype, "reference_name": docname},
            fields=NOTE_FIELDS,
            order_by=NOTE_ORDER_BY,
        )

    start = _page_value(limit_start, 0, 0, _("Limit start"))
    page_length = _page_value(limit_page_length, NOTE_DEFAULT_PAGE_LENGTH, 1, _("Page length"))
    if page_length > NOTE_MAX_PAGE_LENGTH:
        frappe.throw(
            _("Page length cannot exceed {0}").format(NOTE_MAX_PAGE_LENGTH),
            frappe.ValidationError,
        )
    notes = frappe.get_list(
        "DoubleT Note",
        filters={"reference_doctype": doctype, "reference_name": docname},
        fields=NOTE_FIELDS,
        order_by=NOTE_ORDER_BY,
        limit_start=start,
        limit_page_length=page_length + 1,
    )
    page = notes[:page_length]
    if cint(include_pagination):
        return {
            "notes": page,
            "has_more": len(notes) > page_length,
            "limit_start": start,
            "limit_page_length": page_length,
        }
    return page


@frappe.whitelist()
def get_linked_tasks(
    doctype: str,
    docname: str,
    limit_start: int | str | None = None,
    limit_page_length: int | str | None = None,
    include_pagination: int | str = 0,
):
    frappe.has_permission("DoubleT Task", "read", throw=True)
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

    paginated = limit_start is not None or limit_page_length is not None or cint(include_pagination)
    if not paginated:
        tasks = frappe.get_list(
            "DoubleT Task",
            filters={"reference_doctype": doctype, "reference_docname": docname},
            fields=TASK_FIELDS,
            order_by=TASK_ORDER_BY,
        )
        return [[], [], [], tasks, []]

    start = _page_value(limit_start, 0, 0, _("Limit start"))
    page_length = _page_value(limit_page_length, NOTE_DEFAULT_PAGE_LENGTH, 1, _("Page length"))
    if page_length > NOTE_MAX_PAGE_LENGTH:
        frappe.throw(
            _("Page length cannot exceed {0}").format(NOTE_MAX_PAGE_LENGTH),
            frappe.ValidationError,
        )
    tasks = frappe.get_list(
        "DoubleT Task",
        filters={"reference_doctype": doctype, "reference_docname": docname},
        fields=TASK_FIELDS,
        order_by=TASK_ORDER_BY,
        limit_start=start,
        limit_page_length=page_length + 1,
    )
    page = tasks[:page_length]
    if cint(include_pagination):
        return [
            [],
            [],
            [],
            {
                "tasks": page,
                "has_more": len(tasks) > page_length,
                "limit_start": start,
                "limit_page_length": page_length,
            },
            [],
        ]
    return [[], [], [], page, []]


def _check_activity_reference(doctype, docname):
    if doctype not in ALLOWED_REFERENCES:
        frappe.throw(_("Unsupported reference DocType"), frappe.ValidationError)
    if not frappe.db.exists(doctype, docname):
        frappe.throw(_("Document not found"), frappe.DoesNotExistError)
    if not frappe.has_permission(doctype, "read", doc=docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)


@frappe.whitelist()
def get_activities(doctype, docname):
    """Timeline data for a single DoubleT record, in the shared Activities shape."""
    _check_activity_reference(doctype, docname)
    record = frappe.get_doc(doctype, docname)
    versions = [frappe._dict(
        name=f"creation-{docname}", activity_type="creation", data=doctype,
        owner=record.owner, creation=record.creation, is_lead=doctype == "DoubleT Lead",
    )]

    comments = frappe.get_list(
        "Comment", filters={"reference_doctype": doctype, "reference_name": docname,
                            "comment_type": "Comment"},
        fields=["name", "content", "owner", "creation"],
        order_by="creation asc",
    )
    for comment in comments:
        comment.update(activity_type="comment", is_lead=doctype == "DoubleT Lead")
    versions.extend(comments)

    if frappe.has_permission("Version", "read"):
        history = frappe.get_list(
            "Version", filters={"ref_doctype": doctype, "docname": docname},
            fields=["name", "owner", "creation", "data"], order_by="creation asc",
        )
        for revision in history:
            changes = json.loads(revision.data or "{}")
            for index, change in enumerate(changes.get("changed", [])):
                if len(change) < 3:
                    continue
                fieldname, old, value = change[:3]
                field = frappe.get_meta(doctype).get_field(fieldname)
                versions.append(frappe._dict(
                    name=f"{revision.name}-{index}", activity_type="changed",
                    data={"field_label": field.label if field else fieldname,
                          "old_value": old, "value": value},
                    owner=revision.owner, creation=revision.creation,
                    options=field.options if field else None,
                ))

    emails = frappe.get_list(
        "Communication", filters={"reference_doctype": doctype, "reference_name": docname,
                                  "communication_type": "Communication", "sent_or_received": ["in", ["Sent", "Received"]]},
        fields=["name", "owner", "creation", "communication_date", "communication_type",
                "sender", "sender_full_name", "recipients", "cc", "bcc", "subject", "content",
                "delivery_status"],
        order_by="creation asc",
    )
    for email in emails:
        email["activity_type"] = "communication"
        email["data"] = {key: email.get(key) for key in (
            "sender", "sender_full_name", "recipients", "cc", "bcc", "subject", "content", "delivery_status")}
        email["data"]["attachments"] = frappe.get_list(
            "File", filters={"attached_to_doctype": "Communication", "attached_to_name": email.name},
            fields=["file_name", "file_url"],
        )
    versions.extend(emails)

    calls = frappe.get_list(
        "DoubleT Call Log", filters={"reference_doctype": doctype, "reference_name": docname},
        fields=["name", "agent", "call_type", "duration", "status", "start_time",
                "from_number", "to_number", "recording_url", "creation", "modified"],
        order_by="creation asc",
    )
    for entry in calls:
        incoming = entry.call_type.startswith("Incoming")
        entry.update(type="Incoming" if incoming else "Outgoing",
                     activity_type="incoming_call" if incoming else "outgoing_call",
                     owner=entry.agent,
                     _caller={"label": entry.from_number or entry.agent, "image": None},
                     _receiver={"label": entry.to_number or "", "image": None},
                     _duration=f"{entry.duration or 0}s")

    notes = get_linked_notes(doctype, docname) if frappe.has_permission("DoubleT Note", "read") else []
    tasks = get_linked_tasks(doctype, docname)[3] if frappe.has_permission("DoubleT Task", "read") else []
    attachments = frappe.get_list(
        "File", filters={"attached_to_doctype": doctype, "attached_to_name": docname},
        fields=["name", "file_name", "file_url", "file_type", "file_size", "is_private", "creation", "modified"],
        order_by="creation desc",
    )
    return [versions, calls, notes, tasks, attachments]


@frappe.whitelist(methods=["POST"])
def add_activity_comment(doctype, docname, content, attachments=None):
    _check_activity_reference(doctype, docname)
    if not frappe.has_permission(doctype, "write", doc=docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    if not (content or "").strip():
        frappe.throw(_("Comment cannot be empty"), frappe.ValidationError)
    names = json.loads(attachments) if isinstance(attachments, str) else (attachments or [])
    if not isinstance(names, list):
        frappe.throw(_("Invalid attachments"), frappe.ValidationError)
    for name in names:
        file = frappe.get_doc("File", name)
        file.check_permission("write")
        if file.attached_to_doctype != doctype or file.attached_to_name != docname:
            frappe.throw(_("Attachment is not linked to this document"), frappe.PermissionError)
    comment = frappe.get_doc({
        "doctype": "Comment", "comment_type": "Comment", "comment_email": frappe.session.user,
        "reference_doctype": doctype, "reference_name": docname, "content": content,
    }).insert()
    return comment.name


ASSIGNABLE_ROLES = ("System Manager", "Sales Manager", "Sales User")
USER_PROFILE_FIELDS = ["name", "email", "first_name", "last_name", "full_name",
                       "user_image", "user_type", "language"]


def _require_crm_user():
    if frappe.session.user == "Guest" or not set(frappe.get_roles()).intersection(ASSIGNABLE_ROLES):
        frappe.throw(_("Not permitted"), frappe.PermissionError)


def _assignable_user_names():
    names = set(frappe.get_all(
        "Has Role", filters={"parenttype": "User", "role": ["in", ASSIGNABLE_ROLES]},
        pluck="parent", distinct=True,
    ))
    names.add("Administrator")
    return names


def _user_profiles(names):
    if not names:
        return []
    users = frappe.get_all(
        "User", filters={"name": ["in", list(names)], "enabled": 1,
                         "user_type": "System User"},
        fields=USER_PROFILE_FIELDS, order_by="full_name asc",
    )
    roles = frappe.get_all(
        "Has Role", filters={"parenttype": "User", "parent": ["in", [u.name for u in users]]},
        fields=["parent", "role"],
    ) if users else []
    by_user = {}
    for row in roles:
        by_user.setdefault(row.parent, []).append(row.role)
    for user in users:
        user["roles"] = by_user.get(user.name, [])
        if user.name == "Administrator":
            user["roles"] = ["System Manager"]
        user["role"] = next((role for role in ASSIGNABLE_ROLES if role in user.roles), None)
        user["session_user"] = user.name == frappe.session.user
    return users


@frappe.whitelist()
def get_assignment_users(include_all=0):
    """Return [visible users, assignable users] for the existing users store."""
    _require_crm_user()
    eligible = _assignable_user_names()
    names = eligible
    if cint(include_all) and "System Manager" in frappe.get_roles():
        names = set(frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name"))
    users = _user_profiles(names)
    assignable = [user for user in users if user.name in eligible]
    return [users, assignable]


@frappe.whitelist()
def get_assignment_user_info(users):
    _require_crm_user()
    try:
        names = frappe.parse_json(users) if isinstance(users, str) else users
    except (TypeError, ValueError):
        frappe.throw(_("Invalid user list"), frappe.ValidationError)
    if not isinstance(names, list) or len(names) > 200 or any(not isinstance(name, str) for name in names):
        frappe.throw(_("Invalid user list"), frappe.ValidationError)
    permitted = _assignable_user_names() | {frappe.session.user}
    return _user_profiles(set(names) & permitted)


@frappe.whitelist()
def get_assigned_users(doctype, name):
    _check_activity_reference(doctype, name)
    return sorted(set(frappe.get_all(
        "ToDo", filters={"reference_type": doctype, "reference_name": name,
                       "status": ["!=", "Cancelled"]},
        pluck="allocated_to",
    )))


@frappe.whitelist(methods=["POST"])
def remove_assignments(doctype, name, assignees):
    _check_activity_reference(doctype, name)
    if not frappe.has_permission(doctype, "write", doc=name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    names = frappe.parse_json(assignees) if isinstance(assignees, str) else assignees
    if not isinstance(names, list) or any(not isinstance(user, str) for user in names):
        frappe.throw(_("Invalid assignees"), frappe.ValidationError)
    from frappe.desk.form.assign_to import remove

    for user in set(names):
        remove(doctype, name, user)
    return get_assigned_users(doctype, name)


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
