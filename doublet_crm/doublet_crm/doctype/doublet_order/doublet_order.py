"""Orders use saved prices, never a live Product/Price List price lookup."""

from decimal import Decimal

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate, nowdate

from doublet_crm.doublet_crm.doctype.doublet_quotation.doublet_quotation import (
    DoubleTQuotation,
    decimal_value,
    readable_doc,
    usd,
)


CUSTOMER_FIELDS = ("customer_type", "contact", "company", "deal")
LOCKED_FIELDS = (*CUSTOMER_FIELDS, "quotation", "currency", "order_date", "notes")
TRANSITIONS = {
    "Draft": {"Draft", "Confirmed", "Cancelled"},
    "Confirmed": {"Confirmed", "Completed", "Cancelled"},
    "Completed": {"Completed"},
    "Cancelled": {"Cancelled"},
}


class DoubleTOrder(Document):
    def validate(self):
        self.quotation = self.quotation or None
        previous = self.get_doc_before_save()
        self.validate_lifecycle(previous)
        # Reuse the existing Contact/Company/Deal permission and consistency rules.
        DoubleTQuotation.validate_customer(self)
        if not self.order_date:
            frappe.throw(_("Order Date is required."))
        getdate(self.order_date)
        if self.currency != "USD":
            frappe.throw(_("Orders use USD, matching Quotation currency."))
        quotation = self.validate_quotation(previous)
        if previous and previous.status != "Draft":
            self.subtotal, self.total_discount, self.total = (
                previous.subtotal, previous.total_discount, previous.total
            )
            for row, old in zip(self.items, previous.items):
                row.subtotal = old.subtotal
            return
        self.calculate_items(previous, quotation)

    def validate_lifecycle(self, previous):
        if not previous:
            if self.status != "Draft":
                frappe.throw(_("A new Order must be Draft."))
            return
        if self.status not in TRANSITIONS.get(previous.status, set()):
            frappe.throw(_("Invalid Order status transition."))
        if (self.quotation or None) != (previous.quotation or None):
            frappe.throw(_("The source Quotation cannot be changed after creation."))
        if previous.status != "Draft":
            if any(self.has_value_changed(field) for field in LOCKED_FIELDS):
                frappe.throw(_("Order fields are locked after Draft."))
            if [self.item_snapshot(row) for row in self.items] != [
                self.item_snapshot(row) for row in previous.items
            ]:
                frappe.throw(_("Order items are locked after Draft."))

    @staticmethod
    def item_snapshot(row):
        return (
            row.name, row.product, row.product_name, row.sku,
            decimal_value(row.quantity, _("Quantity")),
            decimal_value(row.unit_price, _("Unit Price")),
            row.discount_type or "Percentage",
            decimal_value(row.discount_percent or 0, _("Discount")),
            decimal_value(row.discount_amount or 0, _("Discount Amount")),
        )

    def validate_quotation(self, previous):
        if not self.quotation:
            return None
        if previous:
            return None
        quotation = lock_quotation(self.quotation)
        if quotation.status != "Accepted":
            frappe.throw(_("Only Accepted Quotations can be linked to a new Order."), frappe.ValidationError)
        if any((self.get(field) or None) != (quotation.get(field) or None) for field in CUSTOMER_FIELDS):
            frappe.throw(_("Order customer and Deal must match the source Quotation."))
        if self.currency != (quotation.get("currency") or "USD"):
            frappe.throw(_("Order currency must match the source Quotation."))
        self.validate_quotation_snapshot(quotation)
        return quotation

    def validate_quotation_snapshot(self, quotation):
        if len(self.items or []) != len(quotation.items or []):
            frappe.throw(_("Order items must exactly match the Accepted Quotation snapshot."))
        fields = (
            "product", "quantity", "unit_price", "discount_type",
            "discount_percent", "discount_amount",
        )
        number_fields = {"quantity", "unit_price", "discount_percent", "discount_amount"}
        for order_row, quote_row in zip(self.items, quotation.items):
            for field in fields:
                order_value = order_row.get(field)
                quote_value = quote_row.get(field)
                if field in number_fields:
                    matches = decimal_value(order_value or 0, _(field)) == decimal_value(quote_value or 0, _(field))
                else:
                    matches = (order_value or "Percentage") == (quote_value or "Percentage") if field == "discount_type" else order_value == quote_value
                if not matches:
                    frappe.throw(_("Order items must exactly match the Accepted Quotation snapshot."))

    def calculate_items(self, previous, quotation):
        if not self.items:
            frappe.throw(_("At least one item is required."))
        old_items = {row.name: row for row in previous.items} if previous else {}
        gross_total = discount_total = Decimal(0)
        for index, row in enumerate(self.items):
            old = old_items.get(row.name)
            if old and old.product != row.product:
                frappe.throw(_("Remove and add an item to change its Product."))
            product = readable_doc("DoubleT Product", row.product)
            source = quotation.items[index] if quotation and index < len(quotation.items) else None
            source = source if source and source.product == row.product else None
            if not old and not source and not product.is_sellable():
                frappe.throw(_("Select an active Standard Product or Variant."))
            snapshot = old or source or product
            row.product_name, row.sku = snapshot.product_name, snapshot.sku
            quantity = decimal_value(row.quantity, _("Quantity"))
            price = decimal_value(row.unit_price, _("Unit Price"))
            percent = decimal_value(row.discount_percent or 0, _("Discount"))
            amount = decimal_value(row.discount_amount or 0, _("Discount Amount"))
            if quantity <= 0 or price < 0 or not 0 <= percent <= 100:
                frappe.throw(_("Quantity must be positive, price nonnegative and discount between 0 and 100."))
            gross = usd(quantity * price)
            row.discount_type = row.discount_type or "Percentage"
            if row.discount_type == "Percentage":
                discount = usd(gross * percent / 100)
            elif row.discount_type == "Amount":
                if percent or not 0 <= amount <= gross:
                    frappe.throw(_("Amount discounts require zero percent and an amount between zero and the gross line total."))
                discount = usd(amount)
            else:
                frappe.throw(_("Discount Type must be Percentage or Amount."))
            row.discount_amount = discount
            row.subtotal = usd(gross - discount)
            gross_total += gross
            discount_total += discount
        self.subtotal = usd(gross_total)
        self.total_discount = usd(discount_total)
        self.total = usd(gross_total - discount_total)

    def on_trash(self):
        if self.status != "Draft":
            frappe.throw(_("Only Draft Orders can be deleted."))


def lock_quotation(name):
    # Serialize all creation paths for this source until the request transaction ends.
    quotation = frappe.get_doc("DoubleT Quotation", name, for_update=True)
    quotation.check_permission("read")
    return quotation


@frappe.whitelist(methods=["POST"])
def create_order_from_quotation(quotation):
    """Create once per saved Quotation, or return the existing readable Order.

    The row lock and unique quotation column protect concurrent requests. No commit
    occurs here: Frappe commits or rolls back the complete POST transaction.
    """
    readable_doc("DoubleT Quotation", quotation)
    source = lock_quotation(quotation)
    existing = frappe.db.get_value(
        "DoubleT Order", {"quotation": quotation}, "name", for_update=True
    )
    if existing:
        return readable_doc("DoubleT Order", existing).name
    if source.status != "Accepted":
        frappe.throw(_("Only Accepted Quotations can be converted to an Order."), frappe.ValidationError)
    frappe.has_permission("DoubleT Order", "create", throw=True)
    order = frappe.get_doc({
        "doctype": "DoubleT Order",
        "status": "Draft",
        "order_date": nowdate(),
        "quotation": source.name,
        "currency": source.get("currency") or "USD",
        **{field: source.get(field) for field in CUSTOMER_FIELDS},
        "items": [{
            field: row.get(field)
            for field in (
                "product", "quantity", "unit_price", "discount_type",
                "discount_percent", "discount_amount",
            )
        } for row in source.items],
    })
    # Validate and compare before inserting, so a corrupt/unsupported historical
    # snapshot cannot silently produce a different Order total.
    order.validate()
    if (
        usd(decimal_value(source.subtotal, _("Quotation Subtotal"))) != order.subtotal
        or usd(decimal_value(source.total_discount, _("Quotation Discount"))) != order.total_discount
        or usd(decimal_value(source.grand_total, _("Quotation Total"))) != order.total
        or any(usd(decimal_value(old.line_total, _("Quotation Line Total"))) != row.subtotal
               for old, row in zip(source.items, order.items))
    ):
        frappe.throw(_("Stored Quotation totals do not match its item pricing."))
    order.insert()
    order.check_permission("read")
    return order.name


@frappe.whitelist()
def list_orders(search=None, status=None, limit_start=0, limit_page_length=20):
    """Permission-scoped Order search across number, Customer and Deal labels."""
    frappe.has_permission("DoubleT Order", "read", throw=True)
    filters = []
    term = (search or "").strip()
    if term:
        pattern = f"%{term}%"
        companies = frappe.get_list("DoubleT Company", or_filters=[["name", "like", pattern], ["company_name", "like", pattern]], pluck="name", limit_page_length=100) if frappe.has_permission("DoubleT Company", "read") else []
        contacts = frappe.get_list("DoubleT Contact", or_filters=[["name", "like", pattern], ["first_name", "like", pattern], ["last_name", "like", pattern]], pluck="name", limit_page_length=100) if frappe.has_permission("DoubleT Contact", "read") else []
        deals = frappe.get_list("DoubleT Deal", or_filters=[["name", "like", pattern], ["deal_title", "like", pattern]], pluck="name", limit_page_length=100) if frappe.has_permission("DoubleT Deal", "read") else []
        or_filters = [["name", "like", pattern]]
        if companies:
            or_filters.append(["company", "in", companies])
        if contacts:
            or_filters.append(["contact", "in", contacts])
        if deals:
            or_filters.append(["deal", "in", deals])
        names = frappe.get_list("DoubleT Order", or_filters=or_filters, pluck="name", limit_page_length=0)
        if not names:
            return []
        filters.append(["name", "in", names])
    if status:
        filters.append(["status", "=", status])
    return frappe.get_list(
        "DoubleT Order", fields=["name", "contact", "company", "deal", "quotation", "order_date", "status", "total"],
        filters=filters, order_by="modified desc", limit_start=max(0, cint(limit_start)),
        limit_page_length=min(100, max(1, cint(limit_page_length) or 20)),
    )
