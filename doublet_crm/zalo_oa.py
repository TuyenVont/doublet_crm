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


def _message_result(conversation_name, message_name, *, duplicate):
    conversation = frappe.get_doc(CONVERSATION, conversation_name, for_update=True)
    if conversation.lead:
        lead = frappe.get_doc(LEAD, conversation.lead, for_update=True)
        lead.check_permission("read")
    else:
        conversation.check_permission("write")
        lead = frappe.get_doc({
            "doctype": LEAD,
            "first_name": f"Zalo user {conversation.external_user_id}"[:140],
            "source": LEAD_SOURCE,
            "status": "NEW",
        }).insert()
        conversation.db_set("lead", lead.name)

    contact = lead.converted_contact
    if contact and not frappe.has_permission("DoubleT Contact", "read", doc=contact):
        contact = None
    return {
        "conversation": conversation_name,
        "message": message_name,
        "duplicate": duplicate,
        "lead": lead.name,
        "contact": contact,
    }


def _duplicate_result(message_name, actual_conversation, expected_conversation):
    if actual_conversation != expected_conversation:
        frappe.throw(
            _("This message ID is already associated with a different sender for this OA."),
            frappe.ValidationError,
        )

    return _message_result(actual_conversation, message_name, duplicate=True)


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
    content = _required_text(content, _("Content"), 10000)
    sent_at = _parse_sent_at(sent_at)

    conversation_name = external_key(SOURCE, oa_id, user_id)
    message_name = external_key(SOURCE, oa_id, message_id)

    existing_conversation = frappe.db.get_value(MESSAGE, message_name, "conversation")
    if existing_conversation:
        return _duplicate_result(message_name, existing_conversation, conversation_name)

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

    savepoint = "doublet_inbound_message"
    frappe.db.savepoint(savepoint)
    try:
        if not frappe.db.exists(CONVERSATION, conversation_name):
            frappe.get_doc({
                "doctype": CONVERSATION,
                "source": SOURCE,
                "oa_id": oa_id,
                "external_user_id": user_id,
            }).insert(ignore_if_duplicate=True)

        # The conversation above is server-resolved. A concurrent insert may be
        # outside the transaction snapshot used by Frappe's link lookup.
        message.insert(ignore_links=True)
    except frappe.DuplicateEntryError:
        frappe.db.rollback(save_point=savepoint)
        frappe.db.release_savepoint(savepoint)
        # A locking read can see the winner even under repeatable read.
        existing_conversation = frappe.db.get_value(MESSAGE, message_name, "conversation", for_update=True)
        if not existing_conversation:
            raise
        frappe.clear_last_message()
        return _duplicate_result(message_name, existing_conversation, conversation_name)

    result = _message_result(conversation_name, message_name, duplicate=False)
    frappe.db.release_savepoint(savepoint)
    return result
