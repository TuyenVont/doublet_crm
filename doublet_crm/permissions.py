import frappe
from frappe import share
from frappe.utils import cint


CALL_MANAGER_ROLES = {"System Manager", "Sales Manager"}
CALLBACK_TASK_READ_ROLES = {"Sales Manager", "Sales User"}
ELEVATED_CALL_LOG_ROLES = CALL_MANAGER_ROLES | {"Call Log Viewer"}


def can_manage_calls(user=None):
    user = user or frappe.session.user
    return user == "Administrator" or bool(CALL_MANAGER_ROLES.intersection(frappe.get_roles(user)))


def get_doublet_call_log_permission_query_conditions(user=None, doctype=None):
    user = user or frappe.session.user

    if user == "Administrator":
        return ""

    roles = set(frappe.get_roles(user))

    if roles & ELEVATED_CALL_LOG_ROLES:
        return ""

    if "Sales User" in roles:
        return (
            f"(`tabDoubleT Call Log`.`agent` = {frappe.db.escape(user)} "
            f"or `tabDoubleT Call Log`.`assigned_to` = {frappe.db.escape(user)})"
        )

    return "1=0"


def has_doublet_call_log_permission(
    doc,
    user=None,
    ptype=None,
    debug=False,
):
    user = user or frappe.session.user

    if user == "Administrator":
        return None

    roles = set(frappe.get_roles(user))

    if roles & ELEVATED_CALL_LOG_ROLES:
        return None

    if "Sales User" not in roles:
        return None

    if ptype == "create":
        if doc.agent and doc.agent != user:
            return False
        return None

    if ptype == "read":
        return doc.agent == user or doc.assigned_to == user

    if ptype in {
        "write",
        "delete",
        "submit",
        "cancel",
    }:
        return doc.agent == user

    return None


def _ordinary_task_role_scope(roles, *rights):
    # The shipped Sales read rows exist for callbacks. Custom DocPerm replaces
    # standard permissions and represents the site's own role policy.
    scope = None
    for row in frappe.get_meta("DoubleT Task").permissions:
        if row.role not in roles or cint(row.permlevel):
            continue
        if row.doctype == "DocPerm" and row.role in CALLBACK_TASK_READ_ROLES:
            continue
        if any(row.get(right) for right in rights):
            if not cint(row.get("if_owner")):
                return "all"
            scope = "owner"
    return scope


def get_doublet_task_permission_query_conditions(user=None, doctype=None):
    user = user or frappe.session.user
    if user == "Administrator":
        return ""

    roles = set(frappe.get_roles(user))
    manages_callbacks = bool(roles & CALL_MANAGER_ROLES)
    ordinary_scope = _ordinary_task_role_scope(roles, "read", "select")
    if manages_callbacks and ordinary_scope == "all":
        return ""

    table = "`tabDoubleT Task`"
    callback = f"{table}.`callback_call_log`"
    ordinary = f"coalesce({callback}, '') = ''"
    conditions = []
    user_value = frappe.db.escape(user, percent=False)
    if ordinary_scope == "all":
        conditions.append(ordinary)
    elif ordinary_scope == "owner":
        conditions.append(f"({ordinary} and {table}.`owner` = {user_value})")

    # The merged role capabilities may hide owner-only rules and skip loading
    # ordinary shares when a stock callback read row applies.
    if ordinary_scope != "all" and (names := share.get_shared("DoubleT Task", user)):
        shared = ", ".join(frappe.db.escape(name, percent=False) for name in names)
        conditions.append(f"({ordinary} and {table}.`name` in ({shared}))")

    if manages_callbacks:
        conditions.append(f"coalesce({callback}, '') != ''")
    elif "Sales User" in roles:
        conditions.append(
            f"({table}.`assigned_to` = {user_value} and {_assigned_call_condition(callback, user)})"
        )

    return f"({' or '.join(conditions)})" if conditions else "1=0"


def has_doublet_task_permission(doc, user=None, ptype=None, debug=False):
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    if user == "Administrator":
        return None

    if doc.callback_call_log:
        return bool(roles & CALL_MANAGER_ROLES) or (
            "Sales User" in roles
            and doc.assigned_to == user
            and _call_assignee(doc.callback_call_log) == user
        )

    if ptype in {"read", "select"}:
        rights = ("read", "select") if ptype == "select" else ("read",)
        scope = _ordinary_task_role_scope(roles, *rights)
        if scope == "owner":
            return (doc.owner or "").lower() == user.lower()
        if scope is None:
            return False
    return None


def can_handle_call(assignee, user=None):
    user = user or frappe.session.user
    return can_manage_calls(user) or (assignee == user and "Sales User" in frappe.get_roles(user))



def can_use_call_summary(call, user=None):
    user = user or frappe.session.user
    return can_handle_call(call.assigned_to, user) or (
        not call.assigned_to and call.agent == user and "Sales User" in frappe.get_roles(user)
    )


def _assigned_call_condition(link_field, user):
    return (
        "exists (select 1 from `tabDoubleT Call Log` as handling_call "
        f"where handling_call.name = {link_field} and handling_call.assigned_to = {frappe.db.escape(user)})"
    )


def _call_assignee(name):
    return frappe.db.get_value("DoubleT Call Log", name, "assigned_to") if name else None


def get_doublet_call_event_permission_query_conditions(user=None, doctype=None):
    user = user or frappe.session.user
    if can_manage_calls(user):
        return ""
    if "Sales User" in frappe.get_roles(user):
        return _assigned_call_condition("`tabDoubleT Call Event`.`call_log`", user)
    return "1=0"


def has_doublet_call_event_permission(doc, user=None, ptype=None, debug=False):
    if ptype in {"read", "select"}:
        return can_handle_call(_call_assignee(doc.call_log), user)


def get_doublet_appointment_permission_query_conditions(user=None, doctype=None):
    user = user or frappe.session.user
    if user == "Administrator" or set(frappe.get_roles(user)) & CALL_MANAGER_ROLES:
        return ""
    escaped = frappe.db.escape(user, percent=False)
    shared = share.get_shared("DoubleT Appointment", user)
    conditions = [
        f"`tabDoubleT Appointment`.`owner` = {escaped}",
        f"`tabDoubleT Appointment`.`assigned_to` = {escaped}",
    ]
    if shared:
        names = ", ".join(frappe.db.escape(name, percent=False) for name in shared)
        conditions.append(f"`tabDoubleT Appointment`.`name` in ({names})")
    return f"({' or '.join(conditions)})"


def has_doublet_appointment_permission(doc, user=None, ptype=None, debug=False):
    user = user or frappe.session.user
    if user == "Administrator" or set(frappe.get_roles(user)) & CALL_MANAGER_ROLES:
        return None
    if ptype in {"read", "select", "write", "delete"}:
        if doc.owner == user or doc.assigned_to == user:
            return None
        share_field = "write" if ptype in {"write", "delete"} else "read"
        return bool(frappe.db.exists("DocShare", {
            "share_doctype": "DoubleT Appointment",
            "share_name": doc.name,
            "user": user,
            share_field: 1,
        }))
    return None
