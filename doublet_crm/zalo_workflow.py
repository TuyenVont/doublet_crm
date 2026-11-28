"""The handling state and explicit customer links for a Zalo OA thread."""

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from doublet_crm.permissions import can_manage_calls
from doublet_crm.zalo_oa import CONTACT, CONVERSATION, LEAD, LEAD_SOURCE, SOURCE, _required_text, external_key

WAITING = "Waiting"
IN_PROGRESS = "In Progress"
RESOLVED = "Resolved"
EVENT = "DoubleT Conversation Event"
STATUSES = {WAITING, IN_PROGRESS, RESOLVED}
CUSTOMER_FIELDS = {LEAD: "lead", CONTACT: "contact"}
ACTIONS = {"Assign", "Accept", "Resolve", "Link Customer", "Create Lead"}


def can_access(assignee, user=None):
    user = user or frappe.session.user
    return can_manage_calls(user) or (assignee == user and "Sales User" in frappe.get_roles(user))


def scoped_filters(filters):
    return filters if can_manage_calls() else {**filters, "assigned_to": frappe.session.user}


def conversation_query(user=None, doctype=None):
    user = user or frappe.session.user
    if can_manage_calls(user):
        return ""
    if "Sales User" in frappe.get_roles(user):
        return f"`tabDoubleT Conversation`.assigned_to = {frappe.db.escape(user)}"
    return "1=0"


def message_query(user=None, doctype=None):
    user = user or frappe.session.user
    if can_manage_calls(user):
        return ""
    if "Sales User" in frappe.get_roles(user):
        return (
            "exists (select 1 from `tabDoubleT Conversation` as conversation "
            "where conversation.name = `tabDoubleT Message`.conversation "
            "and conversation.oa_id = `tabDoubleT Message`.oa_id "
            "and conversation.source = `tabDoubleT Message`.source "
            f"and conversation.assigned_to = {frappe.db.escape(user)})"
        )
    return "1=0"


def conversation_permission(doc, user=None, ptype=None, debug=False):
    if ptype in ("read", "select"):
        return can_access(doc.assigned_to, user)


def message_permission(doc, user=None, ptype=None, debug=False):
    if ptype in ("read", "select"):
        parent = frappe.db.get_value(CONVERSATION, doc.conversation, ["source", "oa_id", "assigned_to"], as_dict=True)
        return bool(parent and parent.source == doc.source and parent.oa_id == doc.oa_id
                    and can_access(parent.assigned_to, user))


def get_conversation(name, *, for_update=False):
    doc = frappe.get_doc(CONVERSATION, _required_text(name, _("Conversation"), 140), for_update=for_update)
    if not can_access(doc.assigned_to):
        frappe.throw(_("You do not have access to this conversation."), frappe.PermissionError)
    doc.check_permission("read")
    if doc.source != SOURCE or doc.name != external_key(doc.source, doc.oa_id, doc.external_user_id):
        frappe.throw(_("Invalid Zalo OA conversation identity."), frappe.ValidationError)
    return doc


def status(doc):
    return doc.handling_status or WAITING


def customer(doc):
    if doc.contact:
        return CONTACT, doc.contact
    return LEAD, doc.lead


def available_actions(doc):
    manager = can_manage_calls()
    state = status(doc)
    actions = []
    if state != RESOLVED:
        if manager:
            actions.append("Assign")
        if state == WAITING and doc.assigned_to == frappe.session.user:
            actions.append("Accept")
        if manager or state == IN_PROGRESS:
            actions.append("Resolve")
    if not customer(doc)[1] or manager:
        actions.append("Link Customer")
    if not customer(doc)[1] and frappe.has_permission(LEAD, "create"):
        actions.append("Create Lead")
    return actions


def can_reply(doc):
    return status(doc) != RESOLVED and (
        can_manage_calls() or (status(doc) == IN_PROGRESS and can_access(doc.assigned_to))
    )


def _save_event(doc, action, *, reason=None, previous_assignee=None, previous_customer=(None, None),
                linked_customer=(None, None), request_id=None, request_hash=None):
    frappe.get_doc({
        "doctype": EVENT,
        "conversation": doc.name,
        "action": action,
        "actor": frappe.session.user,
        "occurred_at": now_datetime(),
        "previous_assignee": previous_assignee,
        "new_assignee": doc.assigned_to,
        "previous_customer_type": previous_customer[0],
        "previous_customer": previous_customer[1],
        "customer_type": linked_customer[0],
        "customer": linked_customer[1],
        "reason": reason,
        "request_id": request_id,
        "request_hash": request_hash,
    }).insert(ignore_permissions=True)
    # Only the scoped workflow can change these read-only parent fields.
    frappe.db.set_value(CONVERSATION, doc.name, {
        field: doc.get(field) for field in ("handling_status", "assigned_to", "resolved_at", "lead", "contact")
    })


def reopen_on_inbound(doc, sent_at):
    if status(doc) == RESOLVED and (not doc.resolved_at or sent_at > get_datetime(doc.resolved_at)):
        doc.handling_status = WAITING
        _save_event(doc, "Reopened", previous_assignee=doc.assigned_to)


@frappe.whitelist(methods=["GET", "POST"])
def list_assignees():
    if not can_manage_calls():
        frappe.throw(_("Only managers can assign conversations."), frappe.PermissionError)
    from doublet_crm.api import _assignable_user_names

    return frappe.get_all(
        "User", filters={"name": ["in", list(_assignable_user_names())], "enabled": 1, "user_type": "System User"},
        fields=["name", "full_name"], order_by="full_name asc, name asc", page_length=0,
    )


@frappe.whitelist(methods=["POST"])
def update_conversation(conversation, action, request_id, version, assignee=None, reason=None,
                        customer_type=None, customer_name=None, lead_name=None):
    action = _required_text(action, _("Action"), 30)
    if action not in ACTIONS:
        frappe.throw(_("Unsupported conversation action."), frappe.ValidationError)
    request_id = _required_text(request_id, _("Request ID"), 140).strip()
    version = _required_text(version, _("Conversation version"), 40)
    reason = _required_text(reason, _("Reason"), 500).strip() if reason else ""
    request_hash = external_key(frappe.session.user, action, assignee, reason, customer_type, customer_name, lead_name)
    doc = get_conversation(conversation, for_update=True)
    is_stale = str(doc.modified) != version
    # A stale version commonly means a retry. Locking reads see the previous
    # request even when the transaction already took a repeatable-read snapshot.
    stored_hash = frappe.db.get_value(EVENT, external_key(doc.name, request_id), "request_hash", for_update=is_stale)
    if stored_hash:
        if stored_hash != request_hash:
            frappe.throw(_("This request ID was already used for another action."), frappe.ValidationError)
        return {"duplicate": True}

    if is_stale:
        frappe.throw(_("This conversation changed. Refresh it before trying again."), frappe.ValidationError)
    if action not in available_actions(doc):
        frappe.throw(_("You cannot perform this action in the current state."), frappe.PermissionError)

    previous_assignee = doc.assigned_to
    previous_customer = customer(doc)
    linked_customer = (None, None)
    if action == "Assign":
        assignee = _required_text(assignee, _("Assignee"), 140)
        if not any(user.name == assignee for user in list_assignees()):
            frappe.throw(_("Choose an enabled Contact Center user."), frappe.ValidationError)
        if previous_assignee == assignee:
            return {"duplicate": True}
        if previous_assignee and not reason:
            frappe.throw(_("Enter a handover reason."), frappe.ValidationError)
        doc.assigned_to = assignee
        doc.handling_status = WAITING
        action = "Transferred" if previous_assignee else "Assigned"
    elif action == "Accept":
        doc.handling_status = IN_PROGRESS
        action = "Accepted"
    elif action == "Resolve":
        doc.handling_status = RESOLVED
        doc.resolved_at = now_datetime()
        action = "Resolved"
    else:
        if action == "Create Lead":
            lead = frappe.get_doc({
                "doctype": LEAD,
                "first_name": _required_text(lead_name, _("Lead name"), 140).strip(),
                "source": LEAD_SOURCE,
                "status": "NEW",
            }).insert()
            customer_type, customer_name = LEAD, lead.name
        else:
            if not isinstance(customer_type, str) or customer_type not in CUSTOMER_FIELDS:
                frappe.throw(_("Select a Lead or Contact."), frappe.ValidationError)
            customer_name = _required_text(customer_name, _("Customer"), 140)
            frappe.get_doc(customer_type, customer_name).check_permission("read")

        linked_customer = (customer_type, customer_name)
        if previous_customer == linked_customer:
            return {"duplicate": True}
        if previous_customer[1] and not reason:
            frappe.throw(_("Enter a reason for changing the linked customer."), frappe.ValidationError)
        for doctype, fieldname in CUSTOMER_FIELDS.items():
            doc.set(fieldname, customer_name if doctype == customer_type else None)
        action = "Customer linked"

    _save_event(doc, action, reason=reason, previous_assignee=previous_assignee,
                previous_customer=previous_customer if linked_customer[0] else (None, None),
                linked_customer=linked_customer, request_id=request_id, request_hash=request_hash)
    return {"duplicate": False}


def history(doc):
    events = []
    rows = frappe.get_all(
        EVENT, filters={"conversation": doc.name},
        fields=["name", "action", "actor", "occurred_at", "previous_assignee", "new_assignee",
                "previous_customer_type", "previous_customer", "customer_type", "customer", "reason"],
        order_by="occurred_at asc, creation asc, name asc", page_length=0,
    )
    for event in rows:
        row = {key: event.get(key) for key in (
            "name", "action", "actor", "occurred_at", "previous_assignee", "new_assignee", "reason",
        )}
        for prefix in ("", "previous_"):
            doctype = event.get(f"{prefix}customer_type")
            name = event.get(f"{prefix}customer")
            if doctype in CUSTOMER_FIELDS and name and frappe.has_permission(doctype, "read", doc=name):
                row[f"{prefix}customer_type"] = doctype
                row[f"{prefix}customer"] = name
        events.append(row)
    return events
