from email.utils import getaddresses
from html import escape

import frappe
from frappe import _
from frappe.core.doctype.communication.email import _make as make_communication
from frappe.email.doctype.email_account.email_account import EmailAccount
from frappe.utils import cint, getdate, get_datetime, nowdate, validate_email_address

from doublet_crm.doublet_crm.doctype.doublet_quotation.doublet_quotation import (
	ensure_quotation_can_send,
	is_quotation_expired,
)
from doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_pdf import (
	_pdf_content,
	_pdf_filename,
	_render_quotation,
)


QUEUE_STATUS = {
	"Sent": "Sent",
	"Error": "Failed",
	"Partially Sent": "Failed",
}
SENT_DELIVERY_STATUS = {"Sent", "Opened", "Read", "Clicked"}
FAILED_DELIVERY_STATUS = {"Error", "Expired", "Rejected", "Bounced", "Soft-Bounced", "Marked As Spam"}
QUEUED_DELIVERY_STATUS = {"Sending", "Scheduled", "Delayed"}


def _quotation(name, permission="read"):
	if not isinstance(name, str) or not name.strip():
		frappe.throw(_("Quotation is required."), frappe.ValidationError)
	quotation = frappe.get_doc("DoubleT Quotation", name.strip())
	quotation.check_permission("read")
	if permission == "write":
		quotation.check_permission("write")
	return quotation


def _validated_email(value):
	value = (value or "").strip()
	addresses = [address for _label, address in getaddresses([value]) if address]
	if len(addresses) != 1 or validate_email_address(addresses[0]) != addresses[0]:
		frappe.throw(_("Enter one valid recipient email address."), frappe.ValidationError)
	return addresses[0]


def _optional_email(value):
	try:
		return _validated_email(value) if value else None
	except frappe.ValidationError:
		return None


def _validated_message(subject, body):
	subject = (subject or "").strip()
	body = (body or "").strip()
	if not subject or len(subject) > 140 or "\r" in subject or "\n" in subject:
		frappe.throw(_("Enter a subject of up to 140 characters on one line."), frappe.ValidationError)
	if not body or len(body) > 10000:
		frappe.throw(_("Enter a message of up to 10,000 characters."), frappe.ValidationError)
	return subject, escape(body).replace("\n", "<br>")


def _queue_for_communication(communication):
	rows = frappe.get_all(
		"Email Queue",
		filters={"communication": communication},
		fields=["name", "status"],
		order_by="creation desc",
		limit_page_length=1,
	)
	return rows[0] if rows else None


def _display_status(communication, queue):
	if communication.delivery_status in SENT_DELIVERY_STATUS:
		return "Sent"
	if communication.delivery_status in FAILED_DELIVERY_STATUS:
		return "Failed"
	if communication.delivery_status in QUEUED_DELIVERY_STATUS:
		return "Queued"
	if queue:
		return QUEUE_STATUS.get(queue.status, "Queued")
	if communication.sent_or_received == "Sent":
		return "Unknown"
	return None


def _reply_recipient(communication):
	value = communication.sender
	addresses = [address for _label, address in getaddresses([value or ""]) if address]
	return addresses[0] if addresses else ""


def _party(doctype, name, label_fields):
	if not name or not frappe.has_permission(doctype, "read", doc=name):
		return None
	doc = frappe.get_doc(doctype, name)
	doc.apply_fieldlevel_read_permissions()
	label = " ".join(str(doc.get(field) or "").strip() for field in label_fields).strip() or doc.name
	return {"name": doc.name, "label": label, "email": _optional_email(doc.get("email"))}


def _crm_email_accounts(quotation):
	outgoing = EmailAccount.find_outgoing(match_by_doctype=quotation.doctype, _raise_error=True)
	if not outgoing or not outgoing.enable_outgoing or not _optional_email(outgoing.email_id):
		frappe.throw(_("Configure a valid outgoing CRM Email Account before sending."), frappe.OutgoingEmailError)
	incoming = EmailAccount.find_incoming(
		match_by_email=outgoing.email_id,
		match_by_doctype=quotation.doctype,
	)
	if not incoming or not incoming.enable_incoming or not _optional_email(incoming.email_id):
		frappe.throw(
			_("The outgoing CRM Email Account must also have a receiving inbox for replies."),
			frappe.OutgoingEmailError,
		)
	return outgoing, incoming


def _is_expired(quotation):
	return is_quotation_expired(quotation.status, quotation.valid_until)


def _attachments(communication):
	attachments = []
	for row in frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Communication", "attached_to_name": communication},
		fields=["name"],
		order_by="creation asc",
	):
		file = frappe.get_doc("File", row.name)
		if not file.has_permission("read"):
			continue
		file.apply_fieldlevel_read_permissions()
		attachments.append({
			"name": file.name,
			"file_name": file.file_name,
			"file_url": file.file_url,
			"file_size": file.file_size,
			"is_private": file.is_private,
		})
	return attachments


def _email_targets(reference_doctype, reference_name):
	if reference_doctype not in {"DoubleT Lead", "DoubleT Deal", "DoubleT Quotation"}:
		frappe.throw(_("Emails are only available for Leads, Deals and Quotations."), frappe.ValidationError)

	record = frappe.get_doc(reference_doctype, reference_name)
	record.check_permission("read")
	targets = [(record.doctype, record.name, record.name if record.doctype == "DoubleT Quotation" else None)]

	if record.doctype == "DoubleT Quotation":
		return targets

	if record.doctype == "DoubleT Lead":
		deals = frappe.get_list(
			"DoubleT Deal",
			filters={"source_lead": record.name},
			fields=["name"],
			limit_page_length=0,
		)
	else:
		deals = [{"name": record.name}]

	for row in deals:
		deal = frappe.get_doc("DoubleT Deal", row.get("name"))
		deal.check_permission("read")
		for quotation_row in frappe.get_list(
			"DoubleT Quotation",
			filters={"deal": deal.name},
			fields=["name"],
			limit_page_length=0,
		):
			quotation = frappe.get_doc("DoubleT Quotation", quotation_row.get("name"))
			quotation.check_permission("read")
			targets.append((quotation.doctype, quotation.name, quotation.name))

	return targets


def _record_emails(reference_doctype, reference_name):
	emails = []
	seen = set()
	for target_doctype, target_name, quotation_name in _email_targets(reference_doctype, reference_name):
		rows = frappe.get_all(
			"Communication",
			filters={
				"reference_doctype": target_doctype,
				"reference_name": target_name,
				"communication_medium": "Email",
				"sent_or_received": ["in", ["Sent", "Received"]],
			},
			fields=["name"],
			order_by="communication_date desc, creation desc",
		)
		for row in rows:
			if row.name in seen:
				continue
			communication = frappe.get_doc("Communication", row.name)
			queue = _queue_for_communication(communication.name)
			delivery_status = _display_status(communication, queue)
			emails.append({
				"name": communication.name,
				"sent_or_received": communication.sent_or_received,
				"sender": communication.sender,
				"sender_full_name": communication.sender_full_name,
				"recipients": communication.recipients,
				"cc": communication.cc,
				"bcc": communication.bcc,
				"subject": communication.subject,
				"content": communication.content,
				"communication_date": communication.communication_date or communication.creation,
				"creation": communication.creation,
				"in_reply_to": communication.in_reply_to,
				"reply_to": _reply_recipient(communication),
				"reference_doctype": communication.reference_doctype,
				"reference_name": communication.reference_name,
				"quotation": quotation_name,
				"email_queue": queue.name if queue else None,
				"queue_status": queue.status if queue else None,
				"delivery_status": delivery_status,
				"delivery_error": _("Email delivery failed. Refresh or ask an administrator to check Email Queue.")
				if delivery_status == "Failed" else None,
				"attachments": _attachments(communication.name),
			})
			seen.add(row.name)

	emails.sort(
		key=lambda item: get_datetime(item.get("communication_date") or item.get("creation")),
		reverse=True,
	)
	return emails


def _send_email_queue(email_queue):
	# Use the same row lock as Frappe's scheduler flush. If both workers pick
	# the row, the second one reloads its final status and EmailQueue.send()
	# becomes a no-op instead of delivering the same message twice.
	queue = frappe.get_doc("Email Queue", email_queue, for_update=True)
	queue.send()


def _queue_email(quotation, recipient, subject, content, attachments=None, in_reply_to=None):
	outgoing, incoming = _crm_email_accounts(quotation)
	result = make_communication(
		doctype=quotation.doctype,
		name=quotation.name,
		content=content,
		subject=subject,
		recipients=recipient,
		# Store the account address (not the current user and not a formatted
		# address) on Communication. Frappe combines this with sender_full_name
		# when it builds the actual From header.
		sender=outgoing.email_id,
		sender_full_name=outgoing.name,
		communication_medium="Email",
		sent_or_received="Sent",
		send_email=True,
		attachments=attachments or [],
		in_reply_to=in_reply_to,
	)
	communication = result.get("name")
	queue = _queue_for_communication(communication)
	if not communication or not queue:
		frappe.throw(_("The email could not be queued. Check the outgoing email account."))
	frappe.enqueue(
		"doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email._send_email_queue",
		queue="short",
		enqueue_after_commit=True,
		job_id=f"doublet-quotation-email-{queue.name}",
		deduplicate=True,
		email_queue=queue.name,
	)
	return {
		"communication": communication,
		"email_queue": queue.name,
		"delivery_status": _display_status(frappe.get_doc("Communication", communication), queue),
		"sender": outgoing.email_id,
		"reply_to": incoming.email_id,
	}


@frappe.whitelist()
def get_quotation_email_context(name: str, search: str | None = None):
	quotation = _quotation(name)
	contact = _party("DoubleT Contact", quotation.contact, ("first_name", "last_name"))
	company = _party("DoubleT Company", quotation.company, ("company_name",))
	suggested = None
	if contact and contact["email"]:
		suggested = {**contact, "source": "Quotation Contact"}
	elif company and company["email"]:
		suggested = {**company, "source": "Quotation Company"}

	company_contacts = []
	term = (search or "").strip()[:100]
	if company:
		filters = [["company", "=", company["name"]], ["email", "!=", ""]]
		or_filters = None
		if term:
			pattern = f"%{term}%"
			or_filters = [
				["first_name", "like", pattern],
				["last_name", "like", pattern],
				["email", "like", pattern],
			]
		rows = frappe.get_list(
			"DoubleT Contact",
			filters=filters,
			or_filters=or_filters,
			fields=["name", "first_name", "last_name", "email"],
			order_by="first_name asc, last_name asc, name asc",
			limit_page_length=20,
		)
		for row in rows:
			email = _optional_email(row.email)
			if not email:
				continue
			company_contacts.append({
				"name": row.name,
				"label": " ".join(part for part in (row.first_name, row.last_name) if part).strip() or row.name,
				"email": email,
				"source": "Company Contact",
			})

	return {
		"suggested": suggested,
		"company": company,
		"company_contacts": company_contacts,
		"valid_until": quotation.valid_until,
		"is_expired": _is_expired(quotation),
	}


@frappe.whitelist()
def get_quotation_emails(name: str):
	quotation = _quotation(name)
	return {"emails": _record_emails(quotation.doctype, quotation.name), "can_write": bool(quotation.has_permission("write"))}


@frappe.whitelist()
def get_record_emails(reference_doctype: str, reference_name: str):
	return {"emails": _record_emails(reference_doctype, reference_name)}


@frappe.whitelist(methods=["POST"])
def send_quotation_email(
	name: str,
	recipient: str,
	subject: str,
	body: str,
	modified: str,
	confirm_expired: int | str = 0,
):
	if not isinstance(name, str) or not name.strip():
		frappe.throw(_("Quotation is required."), frappe.ValidationError)
	# Hold the Quotation row while validating and creating the queued message so
	# an approval/edit action cannot race this controlled send.
	quotation = frappe.get_doc("DoubleT Quotation", name.strip(), for_update=True)
	quotation.check_permission("read")
	quotation.check_permission("write")
	if quotation.status != "Draft" or str(quotation.modified) != str(modified):
		frappe.throw(_("Reload the latest draft before sending this quotation."))
	ensure_quotation_can_send(quotation)
	if _is_expired(quotation) and not cint(confirm_expired):
		frappe.throw(
			_("This quotation expired on {0}. Confirm the expired quotation before sending.").format(
				frappe.format_value(quotation.valid_until, {"fieldtype": "Date"})
			),
			frappe.ValidationError,
		)
	recipient = _validated_email(recipient)
	subject, content = _validated_message(subject, body)
	pdf = _pdf_content(_render_quotation(quotation))
	return _queue_email(
		quotation,
		recipient,
		subject,
		content,
		attachments=[{"fname": _pdf_filename(quotation.name), "fcontent": pdf}],
	)


@frappe.whitelist(methods=["POST"])
def reply_quotation_email(name: str, communication: str, recipient: str, subject: str, body: str):
	quotation = _quotation(name, "write")
	original = frappe.get_doc("Communication", communication)
	original.check_permission("read")
	if (
		original.reference_doctype != quotation.doctype
		or original.reference_name != quotation.name
		or original.communication_medium != "Email"
		or original.sent_or_received != "Received"
	):
		frappe.throw(_("Only a received email linked to this quotation can be replied to."), frappe.PermissionError)
	reply_recipient = _validated_email(_reply_recipient(original))
	if recipient and _validated_email(recipient) != reply_recipient:
		frappe.throw(_("The reply recipient must match the original email sender."), frappe.ValidationError)
	subject, content = _validated_message(subject, body)
	return _queue_email(
		quotation,
		reply_recipient,
		subject,
		content,
		in_reply_to=original.name,
	)
