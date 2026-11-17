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
	amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
	return f"${amount:,.2f}"


def quotation_html(name):
	if not name or not isinstance(name, str):
		frappe.throw("Quotation is required.")
	quote = frappe.get_doc("DoubleT Quotation", name)
	quote.check_permission("read")
	return _render_quotation(quote)


def _render_quotation(quote):
	quote.apply_fieldlevel_read_permissions()
	company = _customer_name("DoubleT Company", quote.get("company"), ("company_name",))
	contact = _customer_name("DoubleT Contact", quote.get("contact"), ("first_name", "last_name"))
	return frappe.render_template(
		"doublet_crm/templates/quotation_pdf.html",
		{"doc": quote, "company_name": company, "contact_name": contact, "currency": _currency,
		 "format_date": lambda value: formatdate(value, "dd/MM/yyyy") if value else "—"},
	)


def _pdf_filename(name):
	return f"{name.replace('/', '-').replace(' ', '-')}.pdf"


def _pdf_content(html):
	return get_pdf(html, {"page-size": "A4", "orientation": "Portrait"})


@frappe.whitelist(methods=["GET"])
def download_quotation_pdf(name):
	html = quotation_html(name)
	frappe.local.response.filename = _pdf_filename(name)
	frappe.local.response.filecontent = _pdf_content(html)
	frappe.local.response.type = "pdf"


@frappe.whitelist(methods=["POST"])
def send_quotation_email(
	name: str,
	recipient: str,
	subject: str,
	body: str,
	modified: str,
	confirm_expired: int | str = 0,
):
	# Keep the original endpoint stable for existing clients while the email
	# implementation lives with quotation history and threaded replies.
	from doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email import send_quotation_email as send

	return send(name, recipient, subject, body, modified, confirm_expired)
