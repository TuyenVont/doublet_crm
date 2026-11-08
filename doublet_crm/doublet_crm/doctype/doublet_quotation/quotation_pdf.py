from decimal import Decimal, ROUND_HALF_UP

import frappe
from frappe.utils import formatdate
from frappe.utils.pdf import get_pdf


def _customer_name(doctype, name, fields):
	if not name:
		return ""
	try:
		doc = frappe.get_doc(doctype, name)
		doc.check_permission("read")
		doc.apply_fieldlevel_read_permissions()
		return " ".join(str(doc.get(field) or "").strip() for field in fields).strip()
	except (frappe.PermissionError, frappe.DoesNotExistError):
		return ""


def _currency(value):
	if value is None or value == "":
		return "—"
	amount = Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
	return f"{amount:,.0f}".replace(",", ".")


def quotation_html(name):
	if not name or not isinstance(name, str):
		frappe.throw("Quotation is required.")
	quote = frappe.get_doc("DoubleT Quotation", name)
	quote.check_permission("read")
	quote.apply_fieldlevel_read_permissions()
	company = _customer_name("DoubleT Company", quote.get("company"), ("company_name",))
	contact = _customer_name("DoubleT Contact", quote.get("contact"), ("first_name", "last_name"))
	return frappe.render_template(
		"doublet_crm/templates/quotation_pdf.html",
		{"doc": quote, "company_name": company, "contact_name": contact, "currency": _currency,
		 "format_date": lambda value: formatdate(value, "dd/MM/yyyy") if value else "—"},
	)


@frappe.whitelist(methods=["GET"])
def download_quotation_pdf(name):
	html = quotation_html(name)
	frappe.local.response.filename = f"{name.replace('/', '-').replace(' ', '-')}.pdf"
	frappe.local.response.filecontent = get_pdf(html, {"page-size": "A4", "orientation": "Portrait"})
	frappe.local.response.type = "pdf"
