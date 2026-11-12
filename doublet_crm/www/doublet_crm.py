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


def get_doublet_crm_settings():
    timestamp_format = frappe.conf.get(
        "doublet_crm_timeline_timestamp_format", "Relative"
    )
    if timestamp_format not in {"Relative", "Exact"}:
        timestamp_format = "Relative"

    sort_order = frappe.conf.get(
        "doublet_crm_timeline_sort_order", "Oldest First"
    )
    if sort_order not in {"Oldest First", "Newest First"}:
        sort_order = "Oldest First"

    brand_logo = (
        frappe.conf.get("doublet_crm_brand_logo")
        or frappe.db.get_single_value("Website Settings", "app_logo", cache=True)
        or frappe.db.get_single_value("Navbar Settings", "app_logo", cache=True)
    )
    favicon = (
        frappe.conf.get("doublet_crm_favicon")
        or frappe.db.get_single_value("Website Settings", "favicon", cache=True)
        or "/assets/frappe/images/frappe-favicon.svg"
    )

    return {
        "brand_name": frappe.conf.get(
            "doublet_crm_brand_name", "DoubleT CRM"
        ),
        "brand_logo": brand_logo,
        "favicon": favicon,
        "crm_timeline_timestamp_format": timestamp_format,
        "crm_timeline_sort_order": sort_order,
    }


def get_boot():
    return frappe._dict(
        {
            "frappe_version": frappe.__version__,
            "site_name": frappe.local.site,
            "user": frappe.session.user,
            "csrf_token": frappe.sessions.get_csrf_token(),
            "translated_messages": get_messages_for_boot(),
            "doublet_crm_settings": get_doublet_crm_settings(),
        }
    )
