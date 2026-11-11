from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from doublet_crm.pricing import resolve_product_price


def decimal_value(value, label):
	try:
		result = Decimal(str(value))
		if not result.is_finite():
			raise InvalidOperation
		return result
	except (InvalidOperation, TypeError, ValueError):
		frappe.throw(_("{0} must be a finite number.").format(label))


def vnd(value):
	return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def readable_doc(doctype, name):
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	return doc


class DoubleTQuotation(Document):
	def validate(self):
		previous = self.get_doc_before_save()
		self.validate_lifecycle(previous)
		self.validate_customer()
		if getdate(self.valid_until) < getdate(self.quotation_date):
			frappe.throw(_("Valid Until cannot be before Quotation Date."))
		if previous and previous.status != "Draft":
			self.preserve_historical_totals(previous)
			return
		self.validate_items_and_calculate(previous)

	def preserve_historical_totals(self, previous):
		self.subtotal = previous.subtotal
		self.total_discount = previous.total_discount
		self.grand_total = previous.grand_total

	def validate_lifecycle(self, previous):
		allowed = {"Draft": {"Draft", "Sent"}, "Sent": {"Sent", "Accepted", "Rejected"},
			"Accepted": {"Accepted"}, "Rejected": {"Rejected"}}
		if not previous:
			if self.status != "Draft":
				frappe.throw(_("A new quotation must be Draft."))
			return
		if self.status not in allowed.get(previous.status, set()):
			frappe.throw(_("Invalid quotation status transition."))
		if previous.status != "Draft":
			fields = ("deal", "customer_type", "contact", "company", "price_list", "quotation_date", "valid_until", "notes")
			if any(self.has_value_changed(field) for field in fields):
				frappe.throw(_("Quotation fields are locked after Draft."))
			old_items = [self.item_snapshot(row) for row in previous.items]
			new_items = [self.item_snapshot(row) for row in self.items]
			if old_items != new_items:
				frappe.throw(_("Quotation items are locked after Draft."))

	@staticmethod
	def item_snapshot(row):
		return (
			row.name,
			row.product,
			row.product_name,
			row.sku,
			row.unit_price,
			row.quantity,
			row.discount_type or "Percentage",
			row.discount_percent or 0,
			row.discount_amount or 0,
		)

	def validate_customer(self):
		if self.customer_type not in ("PERSONAL", "COMPANY"):
			frappe.throw(_("Select PERSONAL or COMPANY."))
		if self.customer_type == "PERSONAL" and (not self.contact or self.company):
			frappe.throw(_("A PERSONAL quotation requires a Contact and no Company."))
		if self.customer_type == "COMPANY" and not self.company:
			frappe.throw(_("A COMPANY quotation requires a Company."))
		contact = readable_doc("DoubleT Contact", self.contact) if self.contact else None
		if self.company:
			readable_doc("DoubleT Company", self.company)
		if self.customer_type == "COMPANY" and contact and contact.company != self.company:
			frappe.throw(_("Contact must belong to the selected Company."))
		if self.deal:
			deal = readable_doc("DoubleT Deal", self.deal)
			customer_levels = {deal.meta.get_field(field).permlevel for field in ("contact", "company")}
			if frappe.session.user != "Administrator" and not customer_levels.issubset(set(deal.meta.get_permlevel_access("read"))):
				frappe.throw(_("You cannot read the Deal customer fields."), frappe.PermissionError)
			if (deal.deal_type, deal.contact or None, deal.company or None) != (self.customer_type, self.contact or None, self.company or None):
				frappe.throw(_("Quotation customer must match the Deal customer."))

	def validate_items_and_calculate(self, previous):
		if not self.items:
			frappe.throw(_("At least one item is required."))
		old_items = {row.name: row for row in previous.items} if previous else {}
		subtotal = Decimal(0)
		total_discount = Decimal(0)
		for row in self.items:
			old = old_items.get(row.name)
			if old and old.product != row.product:
				frappe.throw(_("Remove and add an item to change its Product."))
			product = readable_doc("DoubleT Product", row.product)
			if not old:
				resolution = resolve_product_price(
					product,
					self.customer_type,
					contact=self.contact,
					company=self.company,
					price_list=self.price_list,
				)
				row.product_name, row.sku = product.product_name, product.sku
				if row.unit_price is None or row.unit_price == "":
					row.unit_price = resolution["price"]
			else:
				row.product_name, row.sku = old.product_name, old.sku
			quantity = decimal_value(row.quantity, _("Quantity"))
			price = decimal_value(row.unit_price, _("Unit Price"))
			discount_type = row.discount_type or "Percentage"
			discount_percent = decimal_value(row.discount_percent or 0, _("Discount"))
			discount_amount = decimal_value(row.discount_amount or 0, _("Discount Amount"))
			if quantity <= 0 or price < 0 or not 0 <= discount_percent <= 100:
				frappe.throw(_("Quantity must be positive, price nonnegative and discount between 0 and 100."))
			gross = vnd(quantity * price)
			if discount_type == "Percentage":
				line_discount = vnd(gross * discount_percent / 100)
				row.discount_type = "Percentage"
				row.discount_amount = int(line_discount)
			elif discount_type == "Amount":
				if discount_percent:
					frappe.throw(_("Amount discounts cannot also have a discount percentage."))
				if not 0 <= discount_amount <= gross:
					frappe.throw(_("Discount Amount must be between zero and the gross line total."))
				line_discount = vnd(discount_amount)
				row.discount_type = "Amount"
				row.discount_percent = 0
				row.discount_amount = int(line_discount)
			else:
				frappe.throw(_("Discount Type must be Percentage or Amount."))
			row.line_total = int(gross - line_discount)
			subtotal += gross
			total_discount += line_discount
		self.subtotal = int(subtotal)
		self.total_discount = int(total_discount)
		self.grand_total = int(subtotal - total_discount)

	def on_trash(self):
		if self.status != "Draft":
			frappe.throw(_("Only Draft quotations can be deleted."))
