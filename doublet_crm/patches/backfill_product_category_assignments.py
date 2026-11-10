"""Backfill Product V2 category assignments without modifying Product records."""

import frappe


PRODUCT_DOCTYPE = "DoubleT Product"
ASSIGNMENT_DOCTYPE = "DoubleT Product Category Assignment"
PARENTFIELD = "categories"


def execute():
    """Create the missing assignment for every legacy Product category.

    This deliberately inserts child rows directly and never saves a Product, so
    its name, SKU, category, price, active status, and product kind are left
    untouched. Re-running the patch only considers missing assignments.
    """
    assigned_categories = {}
    assignments = frappe.get_all(
        ASSIGNMENT_DOCTYPE,
        filters={"parenttype": PRODUCT_DOCTYPE, "parentfield": PARENTFIELD},
        fields=("parent", "category"),
        limit_page_length=0,
    )
    for assignment in assignments:
        assigned_categories.setdefault(assignment.parent, set()).add(assignment.category)

    products = frappe.get_all(
        PRODUCT_DOCTYPE,
        fields=("name", "category"),
        limit_page_length=0,
    )
    for product in products:
        if not product.category or product.category in assigned_categories.get(product.name, set()):
            continue

        frappe.get_doc(
            {
                "doctype": ASSIGNMENT_DOCTYPE,
                "parent": product.name,
                "parenttype": PRODUCT_DOCTYPE,
                "parentfield": PARENTFIELD,
                "category": product.category,
            }
        ).db_insert()
        assigned_categories.setdefault(product.name, set()).add(product.category)
