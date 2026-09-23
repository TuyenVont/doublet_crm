import frappe
from frappe.tests.utils import FrappeTestCase

from doublet_crm.doublet_crm.doctype.doublet_lead.doublet_lead import convert_lead


class TestDoubleTLeadConversion(FrappeTestCase):
	def setUp(self):
		unique = frappe.generate_hash(length=10)
		self.first_name = f"Conversion-{unique}"
		self.company_name = f"Company-{unique}"
		self.deal_title = f"Deal-{unique}"
		self.source = frappe.get_doc({
			"doctype": "DoubleT Lead Source",
			"source_name": f"Source-{unique}",
		}).insert()
		self.lead = frappe.get_doc({
			"doctype": "DoubleT Lead",
			"first_name": self.first_name,
			"last_name": "Customer",
			"email": f"{unique}@example.com",
			"phone": "123456789",
			"company_name": self.company_name,
			"source": self.source.name,
			"notes": "Conversion test note",
		}).insert()

	def make_stage(self):
		return frappe.get_doc({
			"doctype": "DoubleT Deal Stage",
			"stage_name": f"Open-{frappe.generate_hash(length=10)}",
			"sort_order": 1,
			"stage_type": "OPEN",
			"enabled": 1,
		}).insert()

	def test_contact_only_conversion(self):
		result = convert_lead(self.lead.name)
		lead = frappe.get_doc("DoubleT Lead", self.lead.name)
		contact = frappe.get_doc("DoubleT Contact", result["contact"])

		self.assertEqual(lead.status, "CONVERTED")
		self.assertEqual(lead.converted_contact, contact.name)
		self.assertTrue(lead.converted_on)
		self.assertFalse(lead.converted_company)
		self.assertFalse(lead.converted_deal)
		self.assertIsNone(result["company"])
		self.assertIsNone(result["deal"])
		self.assertEqual(contact.first_name, self.lead.first_name)
		self.assertEqual(contact.last_name, self.lead.last_name)
		self.assertEqual(contact.email, self.lead.email)
		self.assertEqual(contact.phone, self.lead.phone)
		self.assertEqual(contact.source, self.source.name)
		self.assertEqual(contact.notes, self.lead.notes)

	def test_contact_and_company_conversion(self):
		result = convert_lead(self.lead.name, create_company=1, company_name=self.company_name)
		lead = frappe.get_doc("DoubleT Lead", self.lead.name)
		contact = frappe.get_doc("DoubleT Contact", result["contact"])
		company = frappe.get_doc("DoubleT Company", result["company"])

		self.assertEqual(company.company_name, self.company_name)
		self.assertEqual(contact.company, company.name)
		self.assertEqual(lead.converted_company, company.name)
		self.assertFalse(lead.converted_deal)

	def test_contact_company_and_deal_conversion(self):
		stage = self.make_stage()
		result = convert_lead(
			self.lead.name,
			create_company=1,
			company_name=self.company_name,
			create_deal=1,
			deal_title=self.deal_title,
			stage=stage.name,
			amount=125,
		)
		lead = frappe.get_doc("DoubleT Lead", self.lead.name)
		contact = frappe.get_doc("DoubleT Contact", result["contact"])
		deal = frappe.get_doc("DoubleT Deal", result["deal"])

		self.assertEqual(lead.converted_deal, deal.name)
		self.assertEqual(deal.source_lead, self.lead.name)
		self.assertEqual(deal.contact, contact.name)
		self.assertEqual(deal.company, result["company"])
		self.assertEqual(deal.stage, stage.name)
		self.assertEqual(deal.amount, 125)

	def test_deal_can_be_created_without_company(self):
		stage = self.make_stage()
		result = convert_lead(
			self.lead.name,
			create_deal=1,
			deal_title=self.deal_title,
			stage=stage.name,
		)
		lead = frappe.get_doc("DoubleT Lead", self.lead.name)
		deal = frappe.get_doc("DoubleT Deal", result["deal"])

		self.assertEqual(deal.source_lead, self.lead.name)
		self.assertEqual(deal.contact, result["contact"])
		self.assertFalse(deal.company)
		self.assertEqual(deal.amount, 0)
		self.assertFalse(lead.converted_company)
		self.assertEqual(lead.converted_deal, deal.name)

	def test_reconversion_is_rejected(self):
		convert_lead(self.lead.name)
		with self.assertRaisesRegex(frappe.ValidationError, "already been converted"):
			convert_lead(self.lead.name)

		self.assertEqual(frappe.db.count("DoubleT Contact", {"first_name": self.first_name}), 1)

	def test_existing_converted_contact_is_rejected(self):
		contact = frappe.get_doc({
			"doctype": "DoubleT Contact",
			"first_name": self.first_name,
		}).insert()
		frappe.db.set_value("DoubleT Lead", self.lead.name, "converted_contact", contact.name)

		with self.assertRaisesRegex(frappe.ValidationError, "already been converted"):
			convert_lead(self.lead.name)

		self.assertEqual(frappe.db.get_value("DoubleT Lead", self.lead.name, "status"), "NEW")
		self.assertEqual(frappe.db.count("DoubleT Contact", {"first_name": self.first_name}), 1)

	def test_invalid_deal_rolls_back_all_conversion_records(self):
		stage = self.make_stage()
		with self.assertRaises(frappe.ValidationError):
			convert_lead(
				self.lead.name,
				create_company=1,
				company_name=self.company_name,
				create_deal=1,
				deal_title=self.deal_title,
				stage=stage.name,
				amount=-1,
			)

		lead = frappe.get_doc("DoubleT Lead", self.lead.name)
		self.assertEqual(lead.status, "NEW")
		self.assertFalse(lead.converted_on)
		self.assertFalse(lead.converted_contact)
		self.assertFalse(lead.converted_company)
		self.assertFalse(lead.converted_deal)
		self.assertFalse(frappe.db.exists("DoubleT Contact", {"first_name": self.first_name}))
		self.assertFalse(frappe.db.exists("DoubleT Company", {"company_name": self.company_name}))
		self.assertFalse(frappe.db.exists("DoubleT Deal", {"deal_title": self.deal_title}))
