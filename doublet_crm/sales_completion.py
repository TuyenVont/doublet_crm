"""Permission-aware Deal products and Quotation draft context for EXT-05/EXT-06."""

import frappe
from frappe import _

from doublet_crm.doublet_crm.doctype.doublet_deal.doublet_deal import positive_quantity
from doublet_crm.pricing import readable_doc, resolve_product_price


LEAD_QUOTATION_STATUSES = {"QUALIFIED", "CONVERTED"}


def _customer_fields_are_readable(deal):
	levels = {deal.meta.get_field(field).permlevel for field in ("contact", "company")}
	if frappe.session.user != "Administrator" and not levels.issubset(set(deal.meta.get_permlevel_access("read"))):
		frappe.throw(_("You cannot read the Deal customer fields."), frappe.PermissionError)


def _readable_deal(name, permission="read"):
	deal = frappe.get_doc("DoubleT Deal", name)
	deal.check_permission(permission)
	_customer_fields_are_readable(deal)
	return deal


def _safe_product_rows(deal):
	result = []
	for row in (deal.interested_products or []):
		readable_doc("DoubleT Product", row.product)
		result.append({
			"name": row.name,
			"product": row.product,
			"product_name": row.product_name,
			"sku": row.sku,
			"variant_attributes": row.variant_attributes,
			"quantity": row.quantity,
			"reference_price": str(row.reference_price or 0),
		})
	return result


def _lead_deal_names(lead):
	names = []
	if lead.converted_deal:
		names.append(lead.converted_deal)
	linked = frappe.get_list(
		"DoubleT Deal",
		filters={"source_lead": lead.name},
		fields=["name"],
		order_by="modified desc",
		limit_page_length=100,
	)
	for row in linked:
		name = row.get("name") if isinstance(row, dict) else row.name
		if name and name not in names:
			names.append(name)
	return names


def _quotation_context(deal, source_lead=None):
	if deal.deal_type == "PERSONAL":
		if not deal.contact or deal.company:
			frappe.throw(_("The Deal customer is incomplete. Complete its Contact before creating a quotation."))
		readable_doc("DoubleT Contact", deal.contact)
	elif deal.deal_type == "COMPANY":
		if not deal.company:
			frappe.throw(_("The Deal customer is incomplete. Complete its Company before creating a quotation."))
		readable_doc("DoubleT Company", deal.company)
		if deal.contact:
			contact = readable_doc("DoubleT Contact", deal.contact)
			if contact.company != deal.company:
				frappe.throw(_("The Deal Contact must belong to its Company."))
	else:
		frappe.throw(_("The Deal customer type is invalid."))

	items = []
	selected_price_list = None
	for row in deal.interested_products or []:
		product = readable_doc("DoubleT Product", row.product)
		resolution = resolve_product_price(
			product,
			deal.deal_type,
			contact=deal.contact,
			company=deal.company,
		)
		quantity = positive_quantity(row.quantity)
		if selected_price_list is None:
			selected_price_list = resolution["price_list"]
		items.append(
			{
				"product": product.name,
				"product_name": product.product_name,
				"sku": product.sku,
				"quantity": str(quantity),
				"unit_price": str(resolution["price"]),
				"discount_type": "Percentage",
				"discount_percent": 0,
				"discount_amount": 0,
				"pricing_source": resolution["source"],
				"pricing_price_list": resolution["price_list"],
			}
		)
	return {
		"deal": deal.name,
		"source_lead": source_lead or deal.source_lead,
		"customer_type": deal.deal_type,
		"contact": deal.contact,
		"company": deal.company,
		"price_list": selected_price_list,
		"items": items,
	}


@frappe.whitelist()
def get_deal_products(deal_name):
	deal = _readable_deal(deal_name)
	return {
		"deal": deal.name,
		"modified": str(deal.modified),
		"can_write": bool(deal.has_permission("write")),
		"products": _safe_product_rows(deal),
	}


@frappe.whitelist(methods=["POST"])
def save_deal_products(deal_name, products, modified=None):
	deal = _readable_deal(deal_name, "write")
	if modified and str(deal.modified) != str(modified):
		frappe.throw(_("This Deal changed after Products were loaded. Reload and try again."), frappe.TimestampMismatchError)
	rows = frappe.parse_json(products) if isinstance(products, str) else products
	if not isinstance(rows, list):
		frappe.throw(_("Products must be a list."), frappe.ValidationError)
	deal.set("interested_products", [])
	for row in rows:
		if not isinstance(row, dict):
			frappe.throw(_("Each Product row must be an object."), frappe.ValidationError)
		deal.append("interested_products", {"product": row.get("product"), "quantity": row.get("quantity")})
	deal.save()
	return {
		"deal": deal.name,
		"modified": str(deal.modified),
		"can_write": True,
		"products": _safe_product_rows(deal),
	}


@frappe.whitelist()
def get_quotation_draft_context(deal_name=None, lead_name=None):
	frappe.has_permission("DoubleT Quotation", "create", throw=True)
	lead = None
	deal_names = []
	if lead_name:
		lead = readable_doc("DoubleT Lead", lead_name)
		if lead.status not in LEAD_QUOTATION_STATUSES:
			frappe.throw(_("Only a Qualified or converted Qualified Lead can create a quotation."), frappe.ValidationError)
		deal_names = _lead_deal_names(lead)
		if not deal_names:
			return {
				"conversion_required": lead.status == "QUALIFIED",
				"deal_required": lead.status == "CONVERTED",
				"message": (
					_("Convert this Qualified Lead using the existing conversion flow before creating a quotation.")
					if lead.status == "QUALIFIED"
					else _("This converted Lead has no linked Deal. Create or link a Deal through the existing sales workflow first.")
				),
			}

	if deal_name:
		if lead and deal_name not in deal_names:
			frappe.throw(_("The selected Deal does not originate from this Lead."), frappe.ValidationError)
		deal = _readable_deal(deal_name)
		if lead and deal.source_lead != lead.name:
			frappe.throw(_("The selected Deal does not originate from this Lead."), frappe.ValidationError)
		return _quotation_context(deal, lead.name if lead else None)

	if lead:
		choices = []
		for name in deal_names:
			try:
				deal = _readable_deal(name)
			except (frappe.PermissionError, frappe.DoesNotExistError):
				continue
			if deal.source_lead != lead.name:
				continue
			choices.append({"name": deal.name, "label": deal.deal_title or deal.name})
		if not choices:
			return {
				"conversion_required": lead.status == "QUALIFIED",
				"deal_required": lead.status == "CONVERTED",
				"message": _("No readable Deal linked to this Lead is available for quotation."),
			}
		if len(choices) > 1:
			return {"requires_deal_selection": True, "deals": choices}
		return _quotation_context(_readable_deal(choices[0]["name"]), lead.name)

	frappe.throw(_("Select a Deal or Lead."), frappe.ValidationError)
