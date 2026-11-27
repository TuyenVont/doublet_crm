import frappe
from frappe import _
from frappe.utils import cint, get_datetime, now_datetime

from doublet_crm import zalo_workflow as workflow
from doublet_crm.zalo_oa import CONTACT, CONVERSATION, LEAD, MESSAGE, SOURCE, _required_text, external_key

COMPANY = "DoubleT Company"
DEAL = "DoubleT Deal"
REFERENCE_DOCTYPES = {LEAD, DEAL, CONTACT, COMPANY}
PAGE_SIZE = 30
MESSAGE_FIELDS = ["name", "direction", "content", "sent_at", "is_simulated"]
REPLY_FILTERS = {"All", "Needs reply", "Replied"}
ORDER = "sent_at desc, creation desc, name desc"
CONVERSATION_FIELDS = ["name", "oa_id", "external_user_id", "lead", "contact", "creation",
                       "modified", "handling_status", "assigned_to"]


def _linked_records(doc):
    doctype, name = workflow.customer(doc)
    if not name or not frappe.has_permission(doctype, "read", doc=name):
        return {}
    customer = frappe.get_doc(doctype, name)
    result = {
        workflow.CUSTOMER_FIELDS[doctype]: name,
        "display_name": " ".join(filter(None, [customer.first_name, customer.last_name])) or name,
    }
    if doctype == LEAD and customer.converted_contact and frappe.has_permission(
        CONTACT, "read", doc=customer.converted_contact,
    ):
        result["contact"] = customer.converted_contact
    return result


def _response_metrics(messages, now):
    """Use delivered timestamps for intervals. Creation orders legacy undated rows."""
    ordered = sorted(messages, key=lambda row: (row.sent_at or row.creation, row.creation, row.name))
    first_response = last_inbound = last_outbound = pending_since = None
    pending = first_cycle_closed = False

    def elapsed(start, end):
        return int((end - start).total_seconds()) if start and end and end >= start else None

    for row in ordered:
        if row.direction == "inbound":
            if not pending:
                pending_since = row.sent_at
            pending = True
            last_inbound = row.sent_at
        elif row.direction == "outbound":
            if pending and not first_cycle_closed:
                first_response = elapsed(pending_since, row.sent_at)
                first_cycle_closed = True
            pending = False
            pending_since = None
            last_outbound = row.sent_at

    return {
        "last_inbound_at": last_inbound,
        "last_outbound_at": last_outbound,
        "first_response_seconds": first_response,
        "waiting_since": pending_since,
        "waiting_seconds": elapsed(pending_since, now) if pending else None,
        "reply_status": ("Needs reply" if pending else "Replied") if ordered else None,
    }, (ordered[-1] if ordered else None)


def _conversation_rows(docs):
    if not docs:
        return []
    by_oa = {doc.name: doc.oa_id for doc in docs}
    metadata = frappe.get_list(
        MESSAGE,
        filters={"conversation": ["in", list(by_oa)], "source": SOURCE},
        fields=["name", "conversation", "oa_id", "direction", "sent_at", "creation", "is_simulated"],
        page_length=0,
    )
    timelines = {}
    for message in metadata:
        if by_oa.get(message.conversation) == message.oa_id:
            timelines.setdefault(message.conversation, []).append(message)
    now = now_datetime()
    rows = []
    preview_names = {}
    for doc in docs:
        metrics, latest = _response_metrics(timelines.get(doc.name, ()), now)
        row = {
            "name": doc.name,
            "oa_id": doc.oa_id,
            "external_user_id": doc.external_user_id,
            "customer_linked": bool(workflow.customer(doc)[1]),
            "handling_status": workflow.status(doc),
            "assigned_to": doc.assigned_to,
            "version": str(doc.modified),
            **_linked_records(doc),
            **metrics,
            "creation": doc.creation,
            "last_message_content": None,
            "last_message_sent_at": latest.sent_at if latest else None,
            "last_message_direction": latest.direction if latest else None,
            "last_message_is_simulated": latest.is_simulated if latest else 0,
        }
        rows.append(row)
        if latest:
            preview_names[latest.name] = row

    if preview_names:
        for message in frappe.get_list(
            MESSAGE, filters={"name": ["in", list(preview_names)]}, fields=["name", "content"], page_length=0,
        ):
            preview_names[message.name]["last_message_content"] = message.content
    return rows


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
        CONVERSATION, filters=workflow.scoped_filters({"source": SOURCE}),
        fields=CONVERSATION_FIELDS, page_length=0,
    )
    return _conversation_rows(rows)


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


def _get_record_conversation(reference_doctype, reference_name, conversation, *, for_update=False):
    reference_doc = _get_reference(reference_doctype, reference_name)
    doc = workflow.get_conversation(conversation, for_update=for_update)
    linked_contact = reference_doctype == CONTACT and doc.contact == reference_doc.name
    linked_lead = doc.lead and doc.lead in _reference_leads(reference_doc)
    if not (linked_contact or linked_lead):
        frappe.throw(_("Conversation does not belong to this record."), frappe.PermissionError)
    return doc


def _message_page(doc, before=None):
    filters = [["conversation", "=", doc.name], ["source", "=", SOURCE], ["oa_id", "=", doc.oa_id]]
    rows = []

    def fetch(extra):
        remaining = PAGE_SIZE + 1 - len(rows)
        if remaining:
            rows.extend(frappe.get_list(
                MESSAGE, filters=[*filters, *extra],
                fields=MESSAGE_FIELDS, order_by=ORDER, page_length=remaining,
            ))

    if before:
        anchor = frappe.get_doc(MESSAGE, _required_text(before, _("Message"), 140))
        anchor.check_permission("read")
        if anchor.conversation != doc.name or anchor.source != SOURCE or anchor.oa_id != doc.oa_id:
            frappe.throw(_("Message does not belong to this conversation."), frappe.ValidationError)
        time_filter = ["sent_at", "=", anchor.sent_at] if anchor.sent_at else ["sent_at", "is", "not set"]
        fetch([time_filter, ["creation", "=", anchor.creation], ["name", "<", anchor.name]])
        fetch([time_filter, ["creation", "<", anchor.creation]])
        if anchor.sent_at:
            fetch([["sent_at", "<", anchor.sent_at]])
            fetch([["sent_at", "is", "not set"]])
    else:
        fetch([])
    return {
        "messages": list(reversed(rows[:PAGE_SIZE])),
        "has_more": len(rows) > PAGE_SIZE,
        "can_reply": workflow.can_reply(doc),
    }


def _insert_mock_reply(doc, content, request_id=None):
    frappe.has_permission(MESSAGE, "read", throw=True)
    content = _required_text(content, _("Reply"), 10000)
    request_id = (
        _required_text(request_id, _("Request ID"), 140).strip()
        if request_id is not None else frappe.generate_hash(length=32)
    )
    message_id = "mock-reply-" + external_key(doc.name, request_id)
    name = external_key(SOURCE, doc.oa_id, message_id)
    if frappe.db.exists(MESSAGE, name):
        return _existing_reply(doc, name, content)

    if not workflow.can_reply(doc):
        frappe.throw(_("Accept the conversation before replying, or wait for it to reopen."), frappe.PermissionError)
    message = frappe.get_doc({
        "doctype": MESSAGE,
        "conversation": doc.name,
        "source": SOURCE,
        "oa_id": doc.oa_id,
        "external_message_id": message_id,
        "direction": "outbound",
        "content": content,
        "sent_at": now_datetime(),
        "is_simulated": 1,
    })
    # The conversation lock and authorization checks cover this write. Sales
    # users cannot insert messages via the generic DocType resource API.
    message.insert(ignore_permissions=True, ignore_if_duplicate=True)
    return _existing_reply(doc, name, content)


def _existing_reply(doc, name, content):
    message = frappe.get_doc(MESSAGE, name, for_update=True)
    if (message.conversation != doc.name or message.source != SOURCE or message.oa_id != doc.oa_id
        or message.direction != "outbound" or not message.is_simulated
        or message.owner != frappe.session.user or message.content != content):
        frappe.throw(_("This request ID was already used for another reply."), frappe.ValidationError)
    return {field: message.get(field) for field in MESSAGE_FIELDS}


@frappe.whitelist()
def list_conversations(start=0, search=None, oa_id=None, reply_status="All", handling_status=None):
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

    handling_status = _normalized_optional_text(handling_status, _("Handling status"))
    if handling_status and handling_status not in workflow.STATUSES:
        frappe.throw(_("Unsupported handling status."), frappe.ValidationError)

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

    if handling_status:
        rows = [row for row in rows if row["handling_status"] == handling_status]
    rows.sort(key=_activity_sort_key, reverse=True)
    if reply_status == "Needs reply":
        rows.sort(key=lambda row: (row["waiting_since"] is None, row["waiting_since"]))
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
    doc = workflow.get_conversation(conversation)
    row = _conversation_rows([doc])[0]
    row.pop("creation")
    return {**row, "actions": workflow.available_actions(doc), "history": workflow.history(doc)}


def _readable_link(doctype, name, title_fields):
    if not name or not frappe.has_permission(doctype, "read", doc=name):
        return None
    doc = frappe.get_doc(doctype, name)
    label = " ".join(str(doc.get(field) or "").strip() for field in title_fields).strip()
    return {"name": doc.name, "label": label or doc.name}


@frappe.whitelist()
def get_customer_details(conversation):
    frappe.has_permission(MESSAGE, "read", throw=True)
    conversation_doc = workflow.get_conversation(conversation)
    result = {
        "external_user_id": conversation_doc.external_user_id,
        "oa_id": conversation_doc.oa_id,
        "lead": None,
        "contact": None,
        "deal": None,
        "company": None,
    }
    if conversation_doc.contact:
        result["contact"] = _readable_link(CONTACT, conversation_doc.contact, ["first_name", "last_name"])
        return result
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
    filters = workflow.scoped_filters({"source": SOURCE})
    alternatives = []
    if lead_names:
        alternatives.append(["lead", "in", list(lead_names)])
    if reference_doctype == CONTACT:
        alternatives.append(["contact", "=", reference_doc.name])
    if not alternatives:
        return {"can_read": True, "conversations": []}
    rows = frappe.get_list(
        CONVERSATION, filters=filters, or_filters=alternatives,
        fields=["name", "oa_id", "external_user_id", "lead", "contact"],
        order_by="creation desc, name desc", page_length=0,
    )
    return {
        "can_read": True,
        "conversations": [
            {"name": row.name, "oa_id": row.oa_id, "external_user_id": row.external_user_id, **_linked_records(row)}
            for row in rows
        ],
    }


@frappe.whitelist()
def get_messages(conversation, before=None):
    frappe.has_permission(MESSAGE, "read", throw=True)
    doc = workflow.get_conversation(conversation)
    return _message_page(doc, before)


@frappe.whitelist()
def get_record_messages(reference_doctype, reference_name, conversation, before=None):
    frappe.has_permission(MESSAGE, "read", throw=True)
    doc = _get_record_conversation(reference_doctype, reference_name, conversation)
    return _message_page(doc, before)


@frappe.whitelist(methods=["POST"])
def save_mock_reply(conversation, content, request_id=None):
    doc = workflow.get_conversation(conversation, for_update=True)
    return _insert_mock_reply(doc, content, request_id)


@frappe.whitelist(methods=["POST"])
def save_record_mock_reply(reference_doctype, reference_name, conversation, content, request_id=None):
    doc = _get_record_conversation(reference_doctype, reference_name, conversation, for_update=True)
    return _insert_mock_reply(doc, content, request_id)
