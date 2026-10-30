import frappe


ELEVATED_CALL_LOG_ROLES = {
    "System Manager",
    "Sales Manager",
    "Call Log Viewer",
}


def get_doublet_call_log_permission_query_conditions(user=None, doctype=None):
    user = user or frappe.session.user

    if user == "Administrator":
        return ""

    roles = set(frappe.get_roles(user))

    if roles & ELEVATED_CALL_LOG_ROLES:
        return ""

    if "Sales User" in roles:
        return (
            "`tabDoubleT Call Log`.`agent` = "
            f"{frappe.db.escape(user)}"
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

    if ptype in {
        "read",
        "write",
        "delete",
        "submit",
        "cancel",
    }:
        return doc.agent == user

    return None
