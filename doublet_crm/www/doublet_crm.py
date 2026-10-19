import frappe
from frappe.translate import get_messages_for_boot

no_cache = 1


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/doublet-crm"
        raise frappe.Redirect

    context.no_cache = 1
    context.boot = get_boot()
    return context


def get_boot():
    return frappe._dict(
        {
            "frappe_version": frappe.__version__,
            "site_name": frappe.local.site,
            "user": frappe.session.user,
            "csrf_token": frappe.sessions.get_csrf_token(),
            "translated_messages": get_messages_for_boot(),
        }
    )
