from decimal import Decimal, InvalidOperation

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from doublet_crm.pricing import readable_doc, resolve_product_price, validate_product


def _positive_quantity(value):
	try:
		qty = Decimal(str(value))
		if not qty.is_finite() or qty <= 0:
			raise InvalidOperation
		return float(qty)
	except (InvalidOperation, TypeError, ValueError):
		frappe.throw(_("Default Quantity must be greater than zero."), frappe.ValidationError)


class DoubleTQuotationTemplate(Document):
	def validate(self):
		self.template_name = (self.template_name or "").strip()
		if not self.template_name:
			frappe.throw(_("Template Name is required."), frappe.ValidationError)
		if self.product_category:
			readable_doc("DoubleT Product Category", self.product_category)
		if not self.items:
			frappe.throw(_("At least one item is required in a quotation template."), frappe.ValidationError)

		for row in self.items:
			product = readable_doc("DoubleT Product", row.product)
			validate_product(product)
			row.product_name = product.product_name
			row.sku = product.sku
			row.default_quantity = _positive_quantity(row.default_quantity)


@frappe.whitelist()
def get_quotation_template_payload(
	template: str,
	customer_type: str | None = None,
	contact: str | None = None,
	company: str | None = None,
	price_list: str | None = None,
):
	if not isinstance(template, str) or not template.strip():
		frappe.throw(_("Quotation Template is required."), frappe.ValidationError)

	doc = frappe.get_doc("DoubleT Quotation Template", template.strip())
	doc.check_permission("read")
	if not cint(doc.is_active):
		frappe.throw(_("Selected quotation template is inactive."), frappe.ValidationError)

	has_customer = bool(
		(customer_type == "PERSONAL" and contact and not company)
		or (customer_type == "COMPANY" and company)
	)

	items = []
	for row in doc.items:
		product = readable_doc("DoubleT Product", row.product)
		validate_product(product)
		unit_price = ""
		price_source = ""
		resolved_price_list = ""
		if has_customer:
			resolution = resolve_product_price(
				product,
				customer_type,
				contact=contact or None,
				company=company or None,
				price_list=price_list or None,
			)
			unit_price = str(resolution["price"])
			price_source = resolution.get("source") or ""
			resolved_price_list = resolution.get("price_list") or ""

		items.append({
			"product": product.name,
			"product_name": product.product_name,
			"sku": product.sku,
			"quantity": row.default_quantity,
			"unit_price": unit_price,
			"price_source": price_source,
			"price_list": resolved_price_list,
		})

	return {
		"template": doc.name,
		"template_name": doc.template_name,
		"terms": doc.terms or "",
		"items": items,
	}
