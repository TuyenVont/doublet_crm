from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, now_datetime

from doublet_crm.zalo_oa import CONVERSATION, LEAD, MESSAGE, SOURCE, _required_text

CONTACT = "DoubleT Contact"
COMPANY = "DoubleT Company"
DEAL = "DoubleT Deal"
REFERENCE_DOCTYPES = {LEAD, DEAL, CONTACT, COMPANY}
PAGE_SIZE = 30
MESSAGE_FIELDS = ["name", "direction", "content", "sent_at", "is_simulated"]
REPLY_FILTERS = {"All", "Needs reply", "Replied"}


def _get_conversation(name):
    doc = frappe.get_doc(CONVERSATION, _required_text(name, _("Conversation"), 140))
    doc.check_permission("read")
    if doc.source != SOURCE:
        frappe.throw(_("Zalo OA conversation required."), frappe.ValidationError)
    return doc


def _linked_records(lead_name):
    if not lead_name or not frappe.has_permission(LEAD, "read", doc=lead_name):
        return {}

    lead = frappe.get_doc(LEAD, lead_name)
    result = {"lead": lead.name, "display_name": " ".join(filter(None, [lead.first_name, lead.last_name]))}
    if lead.converted_contact and frappe.has_permission(CONTACT, "read", doc=lead.converted_contact):
        result["contact"] = lead.converted_contact
    return result


def _conversation_row(doc, latest_message=None):
    row = {
        "name": doc.name,
        "oa_id": doc.oa_id,
        "external_user_id": doc.external_user_id,
        **_linked_records(doc.lead),
    }
    if latest_message:
        row.update({
            "last_message_content": latest_message.content,
            "last_message_direction": latest_message.direction,
            "last_message_sent_at": latest_message.sent_at,
            "last_message_is_simulated": latest_message.is_simulated,
            "reply_status": "Needs reply" if latest_message.direction == "inbound" else "Replied",
        })
    else:
        row.update({
            "last_message_content": None,
            "last_message_direction": None,
            "last_message_sent_at": None,
            "last_message_is_simulated": 0,
            "reply_status": None,
        })
    return row


def _latest_messages(conversation_names):
    if not conversation_names:
        return {}

    rows = frappe.get_list(
        MESSAGE,
        filters={"conversation": ["in", conversation_names], "source": SOURCE},
        fields=["name", "conversation", *MESSAGE_FIELDS[1:]],
        order_by="sent_at desc, name desc",
        page_length=0,
    )
    latest = {}
    for row in rows:
        latest.setdefault(row.conversation, row)
    return latest


def _normalized_optional_text(value, label, max_length=140):
    if value in (None, ""):
        return ""
    if not isinstance(value, str) or len(value) > max_length:
        frappe.throw(
            _("{0} must be text no longer than {1} characters.").format(label, max_length),
            frappe.ValidationError,
        )
    return value.strip()


def _activity_sort_key(row):
    activity = row.get("last_message_sent_at") or row.get("creation")
    return (get_datetime(activity), row.get("name"))


def _permitted_conversation_rows():
    rows = frappe.get_list(
        CONVERSATION,
        filters={"source": SOURCE},
        fields=["name", "oa_id", "external_user_id", "lead", "creation"],
        page_length=0,
    )
    latest = _latest_messages([row.name for row in rows])
    return [
        {**_conversation_row(row, latest.get(row.name)), "creation": row.creation}
        for row in rows
    ]


def _get_reference(reference_doctype, reference_name):
    if reference_doctype not in REFERENCE_DOCTYPES:
        frappe.throw(_("Unsupported reference type."), frappe.ValidationError)

    doc = frappe.get_doc(
        reference_doctype,
        _required_text(reference_name, _("Reference name"), 140),
    )
    doc.check_permission("read")
    return doc


def _reference_leads(reference_doc):
    if reference_doc.doctype == LEAD:
        return {reference_doc.name}

    if reference_doc.doctype == DEAL:
        lead_names = {reference_doc.source_lead} if reference_doc.source_lead else set()
        lead_names.update(
            frappe.get_list(
                LEAD,
                filters={"converted_deal": reference_doc.name},
                pluck="name",
                page_length=0,
            )
        )
        return lead_names

    link_field = "converted_contact" if reference_doc.doctype == CONTACT else "converted_company"
    return set(
        frappe.get_list(
            LEAD,
            filters={link_field: reference_doc.name},
            pluck="name",
            page_length=0,
        )
    )


def _get_record_conversation(reference_doctype, reference_name, conversation):
    reference_doc = _get_reference(reference_doctype, reference_name)
    conversation_doc = _get_conversation(conversation)
    if not conversation_doc.lead or conversation_doc.lead not in _reference_leads(reference_doc):
        frappe.throw(_("Conversation does not belong to this record."), frappe.PermissionError)
    return conversation_doc


def _message_page(doc, before=None):
    filters = {"conversation": doc.name, "source": SOURCE}
    if before:
        anchor = frappe.get_doc(MESSAGE, _required_text(before, _("Message"), 140))
        anchor.check_permission("read")
        if anchor.conversation != doc.name or anchor.source != SOURCE:
            frappe.throw(_("Message does not belong to this conversation."), frappe.ValidationError)
        # Fetch older timestamps and same-timestamp messages separately so the
        # combination works with Frappe's permission-aware list API.
        filters["sent_at"] = anchor.sent_at
        tied = frappe.get_list(
            MESSAGE,
            filters={**filters, "name": ["<", anchor.name]},
            fields=MESSAGE_FIELDS,
            order_by="name desc",
            page_length=PAGE_SIZE + 1,
        )
        filters["sent_at"] = ["<", anchor.sent_at]
    else:
        tied = []

    remaining = PAGE_SIZE + 1 - len(tied)
    rows = tied
    if remaining:
        rows += frappe.get_list(
            MESSAGE,
            filters=filters,
            fields=MESSAGE_FIELDS,
            order_by="sent_at desc, name desc",
            page_length=remaining,
        )
    return {
        "messages": list(reversed(rows[:PAGE_SIZE])),
        "has_more": len(rows) > PAGE_SIZE,
        "can_reply": frappe.has_permission(CONVERSATION, "write", doc=doc)
        and frappe.has_permission(MESSAGE, "create"),
    }


def _insert_mock_reply(doc, content):
    frappe.has_permission(MESSAGE, "read", throw=True)
    frappe.has_permission(MESSAGE, "create", throw=True)
    doc.check_permission("write")
    content = _required_text(content, _("Reply"), 10000)
    sent_at = now_datetime()
    latest = frappe.get_list(
        MESSAGE,
        filters={"conversation": doc.name, "source": SOURCE},
        fields=["sent_at"],
        order_by="sent_at desc, name desc",
        page_length=1,
    )
    if latest and get_datetime(latest[0].sent_at) >= sent_at:
        sent_at = get_datetime(latest[0].sent_at) + timedelta(microseconds=1)

    message = frappe.get_doc({
        "doctype": MESSAGE,
        "conversation": doc.name,
        "source": SOURCE,
        "oa_id": doc.oa_id,
        "external_message_id": f"mock-reply-{frappe.generate_hash(length=32)}",
        "direction": "outbound",
        "content": content,
        "sent_at": sent_at,
        "is_simulated": 1,
    }).insert()
    return {field: message.get(field) for field in MESSAGE_FIELDS}


@frappe.whitelist()
def list_conversations(start=0, search=None, oa_id=None, reply_status="All"):
    if not (frappe.has_permission(CONVERSATION, "read") and frappe.has_permission(MESSAGE, "read")):
        return {
            "can_read": False,
            "conversations": [],
            "has_more": False,
            "total": 0,
            "oa_options": [],
        }

    search = _normalized_optional_text(search, _("Search")).casefold()
    oa_id = _normalized_optional_text(oa_id, _("OA ID"))
    reply_status = _normalized_optional_text(reply_status, _("Reply status")) or "All"
    if reply_status not in REPLY_FILTERS:
        frappe.throw(_("Unsupported reply status."), frappe.ValidationError)

    rows = _permitted_conversation_rows()
    oa_options = sorted({row["oa_id"] for row in rows}, key=str.casefold)
    if search:
        rows = [
            row for row in rows
            if search in (row.get("display_name") or "").casefold()
            or search in row["external_user_id"].casefold()
        ]
    if oa_id:
        rows = [row for row in rows if row["oa_id"] == oa_id]
    if reply_status != "All":
        rows = [row for row in rows if row["reply_status"] == reply_status]

    rows.sort(key=_activity_sort_key, reverse=True)
    start = max(0, cint(start))
    page = rows[start:start + PAGE_SIZE]
    for row in page:
        row.pop("creation", None)
    return {
        "can_read": True,
        "conversations": page,
        "has_more": start + PAGE_SIZE < len(rows),
        "total": len(rows),
        "oa_options": oa_options,
    }


@frappe.whitelist()
def get_conversation_info(conversation):
    frappe.has_permission(MESSAGE, "read", throw=True)
    doc = _get_conversation(conversation)
    latest = _latest_messages([doc.name]).get(doc.name)
    return _conversation_row(doc, latest)


def _readable_link(doctype, name, title_fields):
    if not name or not frappe.has_permission(doctype, "read", doc=name):
        return None
    doc = frappe.get_doc(doctype, name)
    label = " ".join(str(doc.get(field) or "").strip() for field in title_fields).strip()
    return {"name": doc.name, "label": label or doc.name}


@frappe.whitelist()
def get_customer_details(conversation):
    frappe.has_permission(MESSAGE, "read", throw=True)
    conversation_doc = _get_conversation(conversation)
    result = {
        "external_user_id": conversation_doc.external_user_id,
        "oa_id": conversation_doc.oa_id,
        "lead": None,
        "contact": None,
        "deal": None,
        "company": None,
    }
    if not conversation_doc.lead or not frappe.has_permission(LEAD, "read", doc=conversation_doc.lead):
        return result

    lead = frappe.get_doc(LEAD, conversation_doc.lead)
    lead_link = _readable_link(LEAD, lead.name, ["first_name", "last_name"])
    result["lead"] = {
        **lead_link,
        "source": lead.source,
        "status": lead.status,
    }
    result["contact"] = _readable_link(CONTACT, lead.converted_contact, ["first_name", "last_name"])
    result["company"] = _readable_link(COMPANY, lead.converted_company, ["company_name"])
    result["deal"] = _readable_link(DEAL, lead.converted_deal, ["deal_title"])
    if not result["deal"]:
        deals = frappe.get_list(
            DEAL,
            filters={"source_lead": lead.name},
            fields=["name", "deal_title"],
            order_by="modified desc, name desc",
            page_length=1,
        )
        if deals:
            result["deal"] = {"name": deals[0].name, "label": deals[0].deal_title or deals[0].name}
    return result


@frappe.whitelist()
def list_record_conversations(reference_doctype, reference_name):
    reference_doc = _get_reference(reference_doctype, reference_name)
    if not (frappe.has_permission(CONVERSATION, "read") and frappe.has_permission(MESSAGE, "read")):
        return {"can_read": False, "conversations": []}

    lead_names = _reference_leads(reference_doc)
    if not lead_names:
        return {"can_read": True, "conversations": []}

    rows = frappe.get_list(
        CONVERSATION,
        filters={"source": SOURCE, "lead": ["in", list(lead_names)]},
        fields=["name", "oa_id", "external_user_id", "lead"],
        order_by="creation desc, name desc",
        page_length=0,
    )
    return {
        "can_read": True,
        "conversations": [
            {**row, **_linked_records(row.get("lead"))}
            for row in rows
        ],
    }


@frappe.whitelist()
def get_messages(conversation, before=None):
    frappe.has_permission(MESSAGE, "read", throw=True)
    doc = _get_conversation(conversation)
    return _message_page(doc, before)


@frappe.whitelist()
def get_record_messages(reference_doctype, reference_name, conversation, before=None):
    frappe.has_permission(MESSAGE, "read", throw=True)
    doc = _get_record_conversation(reference_doctype, reference_name, conversation)
    return _message_page(doc, before)


@frappe.whitelist(methods=["POST"])
def save_mock_reply(conversation, content):
    doc = _get_conversation(conversation)
    return _insert_mock_reply(doc, content)


@frappe.whitelist(methods=["POST"])
def save_record_mock_reply(reference_doctype, reference_name, conversation, content):
    doc = _get_record_conversation(reference_doctype, reference_name, conversation)
    return _insert_mock_reply(doc, content)
