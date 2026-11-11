"""Seed the initial Price Lists after their DocTypes exist."""

import frappe


PRICE_LIST_DOCTYPE = "DoubleT Price List"
RETAIL_PRICE_LIST = "Retail"
WHOLESALE_PRICE_LIST = "Wholesale"
PRICING_SETTINGS_DOCTYPE = "DoubleT Pricing Settings"


def create_price_list(price_list_name, is_default=False):
    frappe.get_doc(
        {
            "doctype": PRICE_LIST_DOCTYPE,
            "price_list_name": price_list_name,
            "is_active": 1,
            "is_default": is_default,
        }
    ).insert(ignore_permissions=True)


def execute():
    """Create Retail and Wholesale once without changing business records.

    No product prices, quotation items, quotation totals, or Price List Items are
    read or written. Retail is made default only if no Price List is already the
    default, making repeat runs safe.
    """
    default_price_list = frappe.db.get_value(
        PRICE_LIST_DOCTYPE, {"is_default": 1}, "name"
    )
    has_default = bool(default_price_list)
    retail_exists = frappe.db.exists(
        PRICE_LIST_DOCTYPE, {"price_list_name": RETAIL_PRICE_LIST}
    )

    if not retail_exists:
        create_price_list(RETAIL_PRICE_LIST, is_default=not has_default)
        default_price_list = default_price_list or RETAIL_PRICE_LIST
        has_default = True
    elif not has_default:
        frappe.db.set_value(
            PRICE_LIST_DOCTYPE,
            retail_exists,
            "is_default",
            1,
            update_modified=False,
        )
        default_price_list = retail_exists
        has_default = True

    if not frappe.db.exists(
        PRICE_LIST_DOCTYPE, {"price_list_name": WHOLESALE_PRICE_LIST}
    ):
        create_price_list(WHOLESALE_PRICE_LIST)

    if not frappe.db.get_single_value(PRICING_SETTINGS_DOCTYPE, "default_price_list"):
        frappe.db.set_single_value(
            PRICING_SETTINGS_DOCTYPE,
            "default_price_list",
            default_price_list,
        )
