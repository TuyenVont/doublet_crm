from decimal import Decimal, ROUND_HALF_UP
from html import escape

import frappe
from frappe import _
from frappe.utils import formatdate, validate_email_address
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
def send_quotation_email(name: str, recipient: str, subject: str, body: str, modified: str):
	quote = frappe.get_doc("DoubleT Quotation", name)
	quote.check_permission("read")
	quote.check_permission("write")
	if quote.status != "Draft" or str(quote.modified) != modified:
		frappe.throw(_("Reload the latest draft before sending this quotation."))

	recipient = recipient.strip()
	if (
		recipient.count("@") != 1
		or any(char.isspace() for char in recipient)
		or validate_email_address(recipient) != recipient
	):
		frappe.throw(_("Enter one valid recipient email address."))
	if not subject.strip() or len(subject) > 140 or "\r" in subject or "\n" in subject:
		frappe.throw(_("Enter a subject of up to 140 characters on one line."))
	if not body.strip() or len(body) > 10000:
		frappe.throw(_("Enter a message of up to 10,000 characters."))

	pdf = _pdf_content(_render_quotation(quote))
	queue = frappe.sendmail(
		recipients=[recipient],
		subject=subject.strip(),
		message=escape(body.strip()).replace("\n", "<br>"),
		attachments=[{"fname": _pdf_filename(quote.name), "fcontent": pdf}],
		reference_doctype=quote.doctype,
		reference_name=quote.name,
		add_unsubscribe_link=0,
	)
	if not queue:
		frappe.throw(_("The quotation email could not be queued. Check the outgoing email account."))
	return {"email_queue": queue.name}
