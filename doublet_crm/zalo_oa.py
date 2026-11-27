import json
from datetime import datetime
from hashlib import sha256
from zoneinfo import ZoneInfo

import frappe
from frappe import _
from frappe.utils import get_system_timezone

SOURCE = "zalo_oa"
CONVERSATION = "DoubleT Conversation"
MESSAGE = "DoubleT Message"
LEAD = "DoubleT Lead"
CONTACT = "DoubleT Contact"
LEAD_SOURCE = "Zalo OA"


def external_key(*parts):
    encoded = json.dumps(parts, ensure_ascii=False, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _required_text(value, label, max_length):
    if not isinstance(value, str) or not value.strip() or len(value) > max_length:
        frappe.throw(
            _("{0} must be text between 1 and {1} characters.").format(label, max_length),
            frappe.ValidationError,
        )
    return value


def _parse_sent_at(value):
    value = _required_text(value, _("Sent At"), 64).strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        frappe.throw(_("Sent At must be an ISO 8601 datetime with a timezone."), frappe.ValidationError)

    if parsed.utcoffset() is None:
        frappe.throw(_("Sent At must include a timezone offset."), frappe.ValidationError)

    try:
        return parsed.astimezone(ZoneInfo(get_system_timezone())).replace(tzinfo=None)
    except OverflowError:
        frappe.throw(_("Sent At is outside the supported datetime range."), frappe.ValidationError)


def _message_result(doc, message_name, *, duplicate):
    lead = doc.lead if doc.lead and frappe.has_permission(LEAD, "read", doc=doc.lead) else None
    contact = doc.contact
    if not contact and lead:
        contact = frappe.db.get_value(LEAD, lead, "converted_contact")
    if contact and not frappe.has_permission(CONTACT, "read", doc=contact):
        contact = None
    return {"conversation": doc.name, "message": message_name, "duplicate": duplicate,
            "lead": lead, "contact": contact}


def _duplicate_result(doc, message_name, stored):
    if stored.conversation != doc.name or stored.direction != "inbound":
        frappe.throw(
            _("This message ID is already associated with a different sender or direction for this OA."),
            frappe.ValidationError,
        )
    return _message_result(doc, message_name, duplicate=True)


@frappe.whitelist(methods=["POST"])
def receive_mock_text(oa_id=None, external_user_id=None, external_message_id=None, content=None, sent_at=None):
    """Receive one simulated inbound text through an authenticated Frappe session or API token."""
    if frappe.session.user != "Administrator" and "System Manager" not in frappe.get_roles():
        frappe.throw(_("You are not permitted to ingest simulated Zalo OA messages."), frappe.PermissionError)

    frappe.has_permission(CONVERSATION, "create", throw=True)
    frappe.has_permission(MESSAGE, "create", throw=True)

    oa_id = _required_text(oa_id, _("OA ID"), 140).strip()
    user_id = _required_text(external_user_id, _("External User ID"), 140).strip()
    message_id = _required_text(external_message_id, _("External Message ID"), 140).strip()
    if message_id.startswith("mock-reply-"):
        frappe.throw(_("This message ID prefix is reserved for mock replies."), frappe.ValidationError)
    content = _required_text(content, _("Content"), 10000)
    sent_at = _parse_sent_at(sent_at)

    conversation_name = external_key(SOURCE, oa_id, user_id)
    message_name = external_key(SOURCE, oa_id, message_id)

    from doublet_crm.zalo_workflow import get_conversation, reopen_on_inbound

    # Create the parent if needed, then serialize all updates to the thread.
    savepoint = "doublet_inbound_message"
    frappe.db.savepoint(savepoint)
    parent_exists = frappe.db.exists(CONVERSATION, conversation_name)
    if not parent_exists:
        frappe.get_doc({
            "doctype": CONVERSATION,
            "source": SOURCE,
            "oa_id": oa_id,
            "external_user_id": user_id,
        }).insert(ignore_if_duplicate=True)
    doc = get_conversation(conversation_name, for_update=True)
    key_fields = ["conversation", "direction"]
    message = frappe.get_doc({
        "doctype": MESSAGE,
        "conversation": conversation_name,
        "source": SOURCE,
        "oa_id": oa_id,
        "external_message_id": message_id,
        "direction": "inbound",
        "content": content,
        "sent_at": sent_at,
        "is_simulated": 1,
    })
    try:
        # A concurrently created parent may be outside the initial read snapshot.
        message.insert(ignore_links=True)
    except frappe.DuplicateEntryError:
        frappe.db.rollback(save_point=savepoint)
        stored = frappe.db.get_value(MESSAGE, message_name, key_fields, as_dict=True, for_update=True)
        if not stored:
            raise
        return _duplicate_result(doc, message_name, stored)
    finally:
        frappe.db.release_savepoint(savepoint)

    reopen_on_inbound(doc, sent_at)
    return _message_result(doc, message_name, duplicate=False)
