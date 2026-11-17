from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate
from frappe.utils.file_manager import save_file

from doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email import (
	_display_status,
	_send_email_queue,
	get_record_emails,
	get_quotation_email_context,
	get_quotation_emails,
	reply_quotation_email,
	send_quotation_email,
)


class TestQuotationEmail(FrappeTestCase):
	def setUp(self):
		self.tag = frappe.generate_hash(length=10)
		self.company = frappe.get_doc({
			"doctype": "DoubleT Company",
			"company_name": f"Email Company {self.tag}",
		}).insert()
		self.category = frappe.get_doc({
			"doctype": "DoubleT Product Category",
			"category_name": f"Email Category {self.tag}",
		}).insert()
		self.product = frappe.get_doc({
			"doctype": "DoubleT Product",
			"product_name": f"Email Product {self.tag}",
			"sku": f"EMAIL-{self.tag}",
			"category": self.category.name,
			"price": 25,
		}).insert()

	def quotation(self, **values):
		return frappe.get_doc({
			"doctype": "DoubleT Quotation",
			"customer_type": "COMPANY",
			"company": self.company.name,
			"quotation_date": nowdate(),
			"valid_until": nowdate(),
			"items": [{"product": self.product.name, "quantity": 1}],
			**values,
		}).insert()

	def email_accounts(self):
		return (
			frappe._dict(
				name="DoubleT CRM",
				email_id="crm@example.com",
				enable_outgoing=1,
				default_sender="DoubleT CRM <crm@example.com>",
			),
			frappe._dict(name="DoubleT CRM", email_id="crm@example.com", enable_incoming=1),
		)

	def communication(self, quotation, **values):
		return frappe.get_doc({
			"doctype": "Communication",
			"communication_type": "Communication",
			"communication_medium": "Email",
			"sent_or_received": "Received",
			"sender": "customer@example.com",
			"recipients": "sales@example.com",
			"subject": "Quotation question",
			"content": "<p>Please clarify the quotation.</p>",
			"reference_doctype": quotation.doctype,
			"reference_name": quotation.name,
			"message_id": f"{frappe.generate_hash()}@example.com",
			**values,
		}).insert(ignore_permissions=True)

	def fake_make(self, calls):
		def make(**kwargs):
			calls.append(kwargs)
			communication = frappe.get_doc({
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Sent",
				"sender": frappe.session.user,
				"recipients": kwargs["recipients"],
				"subject": kwargs["subject"],
				"content": kwargs["content"],
				"reference_doctype": kwargs["doctype"],
				"reference_name": kwargs["name"],
				"in_reply_to": kwargs.get("in_reply_to"),
				"message_id": f"{frappe.generate_hash()}@example.com",
			}).insert(ignore_permissions=True)
			return {"name": communication.name}
		return make

	def test_history_returns_linked_inbound_and_denies_guest(self):
		quotation = self.quotation()
		communication = self.communication(quotation)
		attachment = save_file(
			f"{self.tag}-customer-note.txt",
			b"Customer note",
			"Communication",
			communication.name,
			is_private=1,
		)

		result = get_quotation_emails(quotation.name)
		self.assertEqual(len(result["emails"]), 1)
		email = result["emails"][0]
		self.assertEqual((email["name"], email["reply_to"]), (communication.name, "customer@example.com"))
		self.assertEqual(email["attachments"][0]["file_name"], attachment.file_name)

		try:
			frappe.set_user("Guest")
			with self.assertRaises(frappe.PermissionError):
				get_quotation_emails(quotation.name)
		finally:
			frappe.set_user("Administrator")

	def test_record_histories_follow_saved_links_and_isolate_same_customer_deals(self):
		lead = frappe.get_doc({
			"doctype": "DoubleT Lead",
			"first_name": f"Email Lead {self.tag}",
			"status": "NEW",
		}).insert()
		stage = frappe.get_doc({
			"doctype": "DoubleT Deal Stage",
			"stage_name": f"Email Stage {self.tag}",
			"stage_type": "OPEN",
			"sort_order": 1,
		}).insert()

		def deal(label):
			return frappe.get_doc({
				"doctype": "DoubleT Deal",
				"deal_title": f"{label} {self.tag}",
				"deal_type": "COMPANY",
				"company": self.company.name,
				"source_lead": lead.name,
				"stage": stage.name,
			}).insert()

		first_deal = deal("First Deal")
		second_deal = deal("Second Deal")
		first_quotation = self.quotation(deal=first_deal.name)
		second_quotation = self.quotation(deal=second_deal.name)
		lead_email = self.communication(lead)
		first_deal_email = self.communication(first_deal)
		second_deal_email = self.communication(second_deal)
		first_quotation_email = self.communication(first_quotation)
		second_quotation_email = self.communication(second_quotation)

		first_result = get_record_emails(first_deal.doctype, first_deal.name)["emails"]
		second_result = get_record_emails(second_deal.doctype, second_deal.name)["emails"]
		lead_result = get_record_emails(lead.doctype, lead.name)["emails"]
		quotation_result = get_record_emails(first_quotation.doctype, first_quotation.name)["emails"]

		self.assertEqual({row["name"] for row in first_result}, {first_deal_email.name, first_quotation_email.name})
		self.assertEqual({row["name"] for row in second_result}, {second_deal_email.name, second_quotation_email.name})
		self.assertEqual(
			{row["name"] for row in lead_result},
			{lead_email.name, first_quotation_email.name, second_quotation_email.name},
		)
		self.assertEqual([row["name"] for row in quotation_result], [first_quotation_email.name])
		self.assertEqual(
			{row["quotation"] for row in lead_result if row["quotation"]},
			{first_quotation.name, second_quotation.name},
		)
		self.assertEqual(len({row["name"] for row in lead_result}), len(lead_result))

		user = frappe.get_doc({
			"doctype": "User",
			"email": f"record-email-reader-{self.tag}@example.invalid",
			"first_name": "Record Email Reader",
			"enabled": 1,
			"send_welcome_email": 0,
		}).insert(ignore_permissions=True)
		for document in (lead, first_deal, first_quotation):
			frappe.share.add(document.doctype, document.name, user.name, read=1, write=0)
		try:
			frappe.set_user(user.name)
			restricted_result = get_record_emails(lead.doctype, lead.name)["emails"]
			self.assertEqual(
				{row["name"] for row in restricted_result},
				{lead_email.name, first_quotation_email.name},
			)
		finally:
			frappe.set_user("Administrator")

	def test_recipient_context_prefers_contact_then_company_and_searches_company(self):
		self.company.email = "company@example.com"
		self.company.save()
		contact = frappe.get_doc({
			"doctype": "DoubleT Contact",
			"first_name": "Primary",
			"last_name": "Customer",
			"email": "primary@example.com",
			"company": self.company.name,
		}).insert()
		other = frappe.get_doc({
			"doctype": "DoubleT Contact",
			"first_name": "Billing",
			"last_name": "Contact",
			"email": "billing@example.com",
			"company": self.company.name,
		}).insert()
		quotation = self.quotation(contact=contact.name)

		context = get_quotation_email_context(quotation.name, "billing@")
		self.assertEqual(
			(context["suggested"]["email"], context["suggested"]["source"]),
			("primary@example.com", "Quotation Contact"),
		)
		self.assertEqual(context["company_contacts"][0]["name"], other.name)

		contact.email = None
		contact.save()
		context = get_quotation_email_context(quotation.name)
		self.assertEqual(
			(context["suggested"]["email"], context["suggested"]["source"]),
			("company@example.com", "Quotation Company"),
		)

		self.company.email = None
		self.company.save()
		self.assertIsNone(get_quotation_email_context(quotation.name)["suggested"])

	def test_send_creates_one_linked_communication_with_pdf(self):
		quotation = self.quotation()
		user = frappe.get_doc({
			"doctype": "User",
			"email": f"quotation-sales-{self.tag}@example.invalid",
			"first_name": "Quotation Sales",
			"enabled": 1,
			"send_welcome_email": 0,
			"roles": [{"role": "Sales User"}],
		}).insert(ignore_permissions=True)
		calls = []
		queue = frappe._dict(name="QUEUE-TEST", status="Not Sent")
		enqueue = patch("frappe.enqueue")
		try:
			frappe.set_user(user.name)
			self.assertTrue(frappe.has_permission(quotation.doctype, "write", quotation.name))
			self.assertFalse(frappe.has_permission(quotation.doctype, "email", quotation.name))
			with (
				patch(
					"doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email.make_communication",
					self.fake_make(calls),
				),
				patch(
					"doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email._queue_for_communication",
					return_value=queue,
				),
				patch(
					"doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email._pdf_content",
					return_value=b"quotation-pdf",
				),
				patch(
					"doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email._crm_email_accounts",
					return_value=self.email_accounts(),
				),
				enqueue as enqueue_doc,
			):
				result = send_quotation_email(
					quotation.name,
					"customer@example.com",
					f"Quotation {quotation.name}",
					"Please find the quotation attached.",
					str(quotation.modified),
				)
		finally:
			frappe.set_user("Administrator")

		self.assertEqual(len(calls), 1)
		self.assertEqual(result["delivery_status"], "Queued")
		self.assertEqual(calls[0]["doctype"], quotation.doctype)
		self.assertEqual(calls[0]["name"], quotation.name)
		self.assertEqual(calls[0]["sender"], "crm@example.com")
		self.assertEqual(calls[0]["sender_full_name"], "DoubleT CRM")
		self.assertEqual(calls[0]["attachments"][0]["fcontent"], b"quotation-pdf")
		enqueue_doc.assert_called_once_with(
			"doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email._send_email_queue",
			queue="short",
			enqueue_after_commit=True,
			job_id="doublet-quotation-email-QUEUE-TEST",
			deduplicate=True,
			email_queue="QUEUE-TEST",
		)
		self.assertEqual(
			_display_status(frappe._dict(sent_or_received="Sent", delivery_status=None), frappe._dict(status="Error")),
			"Failed",
		)
		self.assertEqual(
			_display_status(frappe._dict(sent_or_received="Sent", delivery_status="Sent"), None),
			"Sent",
		)
		self.assertEqual(
			_display_status(frappe._dict(sent_or_received="Sent", delivery_status=None), None),
			"Unknown",
		)

	def test_immediate_queue_job_uses_scheduler_compatible_row_lock(self):
		queue = MagicMock()
		with patch("frappe.get_doc", return_value=queue) as get_doc:
			_send_email_queue("QUEUE-LOCKED")
		get_doc.assert_called_once_with("Email Queue", "QUEUE-LOCKED", for_update=True)
		queue.send.assert_called_once_with()

	def test_expired_pdf_requires_confirmation(self):
		quotation = self.quotation(
			quotation_date=add_days(nowdate(), -2),
			valid_until=add_days(nowdate(), -1),
		)
		with self.assertRaises(frappe.ValidationError):
			send_quotation_email(
				quotation.name,
				"customer@example.com",
				f"Quotation {quotation.name}",
				"Expired quotation.",
				str(quotation.modified),
			)

		calls = []
		with (
			patch(
				"doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email.make_communication",
				self.fake_make(calls),
			),
			patch(
				"doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email._queue_for_communication",
				return_value=frappe._dict(name="QUEUE-EXPIRED", status="Not Sent"),
			),
			patch(
				"doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email._crm_email_accounts",
				return_value=self.email_accounts(),
			),
			patch("doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email._pdf_content", return_value=b"pdf"),
			patch("frappe.enqueue"),
		):
			send_quotation_email(
				quotation.name,
				"customer@example.com",
				f"Quotation {quotation.name}",
				"Expired quotation.",
				str(quotation.modified),
				confirm_expired=1,
			)
		self.assertEqual(len(calls), 1)

	def test_read_only_shared_user_cannot_send(self):
		quotation = self.quotation()
		user = frappe.get_doc({
			"doctype": "User",
			"email": f"quotation-read-only-{self.tag}@example.invalid",
			"first_name": "Quotation Read Only",
			"enabled": 1,
			"send_welcome_email": 0,
		}).insert(ignore_permissions=True)
		frappe.share.add(quotation.doctype, quotation.name, user.name, read=1, write=0)
		try:
			frappe.set_user(user.name)
			self.assertTrue(frappe.has_permission(quotation.doctype, "read", quotation.name))
			self.assertFalse(frappe.has_permission(quotation.doctype, "write", quotation.name))
			with self.assertRaises(frappe.PermissionError):
				send_quotation_email(
					quotation.name,
					"customer@example.com",
					f"Quotation {quotation.name}",
					"This must not be queued.",
					str(quotation.modified),
				)
		finally:
			frappe.set_user("Administrator")

	def test_reply_threads_and_rejects_another_quotations_email(self):
		quotation = self.quotation()
		original = self.communication(quotation)
		other = self.quotation()
		foreign_email = self.communication(other)
		with self.assertRaises(frappe.PermissionError):
			reply_quotation_email(
				quotation.name,
				foreign_email.name,
				"customer@example.com",
				"Re: Quotation question",
				"This should not be sent.",
			)

		calls = []
		queue = frappe._dict(name="QUEUE-REPLY", status="Sent")
		with (
			patch(
				"doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email.make_communication",
				self.fake_make(calls),
			),
			patch(
				"doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email._queue_for_communication",
				return_value=queue,
			),
			patch(
				"doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_email._crm_email_accounts",
				return_value=self.email_accounts(),
			),
			patch("frappe.enqueue"),
		):
			result = reply_quotation_email(
				quotation.name,
				original.name,
				"customer@example.com",
				"Re: Quotation question",
				"Here is the clarification.",
			)

		self.assertEqual(len(calls), 1)
		self.assertEqual(calls[0]["in_reply_to"], original.name)
		self.assertEqual(result["delivery_status"], "Sent")

		outgoing = self.communication(
			quotation,
			sent_or_received="Sent",
			sender="crm@example.com",
			recipients="customer@example.com",
		)
		with self.assertRaises(frappe.PermissionError):
			reply_quotation_email(
				quotation.name,
				outgoing.name,
				"customer@example.com",
				"Re: Quotation question",
				"This should not be sent.",
			)
