"""Permission-aware Product pricing for quotations and future clients."""

from decimal import Decimal, InvalidOperation

import frappe
from frappe import _


PRICE_LIST_DOCTYPE = "DoubleT Price List"
PRICING_SETTINGS_DOCTYPE = "DoubleT Pricing Settings"


def decimal_price(value):
    try:
        price = Decimal(str(value))
        if not price.is_finite():
            raise InvalidOperation
        return price
    except (InvalidOperation, TypeError, ValueError):
        frappe.throw(_("Price must be a finite number."))


def readable_doc(doctype, name):
    doc = frappe.get_doc(doctype, name)
    doc.check_permission("read")
    return doc


def validate_product(product):
    product.check_permission("read")
    if product.is_sellable():
        return
    if product.product_kind == "Template":
        frappe.throw(_("Product Templates cannot be added to a quotation."))
    frappe.throw(_("Inactive Products cannot be added to a quotation."))


def usable_price_list(price_list_name):
    price_list = readable_doc(PRICE_LIST_DOCTYPE, price_list_name)
    if not price_list.is_active:
        frappe.throw(_("Price List {0} is inactive.").format(price_list.name))
    return price_list


def resolve_price_list(customer_type, contact=None, company=None, price_list=None):
    """Resolve the authorized active Price List for a customer context."""
    if customer_type not in {"PERSONAL", "COMPANY"}:
        frappe.throw(_("Select PERSONAL or COMPANY."))

    contact_doc = readable_doc("DoubleT Contact", contact) if contact else None
    company_doc = readable_doc("DoubleT Company", company) if company else None

    if customer_type == "PERSONAL" and (not contact_doc or company_doc):
        frappe.throw(_("A PERSONAL quotation requires a Contact and no Company."))
    if customer_type == "COMPANY" and not company_doc:
        frappe.throw(_("A COMPANY quotation requires a Company."))
    if customer_type == "COMPANY" and contact_doc and contact_doc.company != company_doc.name:
        frappe.throw(_("Contact must belong to the selected Company."))

    if price_list:
        return usable_price_list(price_list)
    if customer_type == "COMPANY" and company_doc.price_list:
        return usable_price_list(company_doc.price_list)
    if contact_doc and contact_doc.price_list:
        return usable_price_list(contact_doc.price_list)

    settings = frappe.get_doc(PRICING_SETTINGS_DOCTYPE)
    settings.check_permission("read")
    if settings.default_price_list:
        return usable_price_list(settings.default_price_list)
    return None


def resolve_product_price(product, customer_type, contact=None, company=None, price_list=None):
    """Return the applicable Product price and its source without mutating data."""
    validate_product(product)
    resolved_price_list = resolve_price_list(
        customer_type,
        contact=contact,
        company=company,
        price_list=price_list,
    )
    if not resolved_price_list:
        return {"price": decimal_price(product.price), "price_list": None, "source": "product"}

    item_price = frappe.db.get_value(
        "DoubleT Price List Item",
        {
            "parent": resolved_price_list.name,
            "parenttype": PRICE_LIST_DOCTYPE,
            "parentfield": "items",
            "product": product.name,
        },
        "price",
    )
    if item_price is None:
        return {
            "price": decimal_price(product.price),
            "price_list": resolved_price_list.name,
            "source": "product",
        }
    return {
        "price": decimal_price(item_price),
        "price_list": resolved_price_list.name,
        "source": "price_list",
    }


@frappe.whitelist()
def get_product_price(product, customer_type, contact=None, company=None, price_list=None):
    """Return a single permitted price; callers cannot bypass linked-doc access."""
    product_doc = readable_doc("DoubleT Product", product)
    result = resolve_product_price(
        product_doc,
        customer_type,
        contact=contact,
        company=company,
        price_list=price_list,
    )
    return {**result, "price": str(result["price"])}
