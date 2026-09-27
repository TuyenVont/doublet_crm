import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime


class TestDoubleTDealLifecycle(FrappeTestCase):
	def setUp(self):
		unique = frappe.generate_hash(length=10)
		self.open_stage = self.make_stage(f"Alpha-{unique}", "OPEN")
		self.won_stage = self.make_stage(f"Beta-{unique}", "WON")
		self.lost_stage = self.make_stage(f"Gamma-{unique}", "LOST")
		self.title = f"Lifecycle-{unique}"
		self.contact = frappe.get_doc({
			"doctype": "DoubleT Contact",
			"first_name": f"Contact-{unique}",
		}).insert()
		self.company = frappe.get_doc({
			"doctype": "DoubleT Company",
			"company_name": f"Company-{unique}",
		}).insert()

	def make_stage(self, name, stage_type):
		return frappe.get_doc({
			"doctype": "DoubleT Deal Stage",
			"stage_name": name,
			"sort_order": 1,
			"stage_type": stage_type,
			"enabled": 1,
		}).insert()

	def make_deal(self, stage=None, **values):
		return frappe.get_doc({
			"doctype": "DoubleT Deal",
			"deal_title": self.title,
			"deal_type": "PERSONAL",
			"contact": self.contact.name,
			"stage": stage or self.open_stage.name,
			**values,
		}).insert()

	def test_valid_personal_deal(self):
		deal = self.make_deal()
		deal.reload()
		self.assertEqual(deal.deal_type, "PERSONAL")
		self.assertEqual(deal.contact, self.contact.name)
		self.assertFalse(deal.company)

	def test_valid_company_deal_with_optional_contact(self):
		for contact in (None, self.contact.name):
			with self.subTest(contact=contact):
				deal = self.make_deal(deal_type="COMPANY", company=self.company.name, contact=contact)
				deal.reload()
				self.assertEqual(deal.deal_type, "COMPANY")
				self.assertEqual(deal.company, self.company.name)
				self.assertEqual(deal.contact or None, contact)

	def test_personal_requires_contact(self):
		with self.assertRaisesRegex(frappe.ValidationError, "Contact is required for a PERSONAL deal"):
			self.make_deal(contact=None)

	def test_personal_rejects_company(self):
		with self.assertRaisesRegex(frappe.ValidationError, "Company must be empty for a PERSONAL deal"):
			self.make_deal(company=self.company.name)

	def test_company_requires_company(self):
		with self.assertRaisesRegex(frappe.ValidationError, "Company is required for a COMPANY deal"):
			self.make_deal(deal_type="COMPANY", company=None)

	def test_invalid_deal_type(self):
		with self.assertRaisesRegex(frappe.ValidationError, "Deal Type must be PERSONAL or COMPANY"):
			self.make_deal(deal_type="INVALID")

	def test_missing_deal_type(self):
		for deal_type in (None, ""):
			with self.subTest(deal_type=deal_type):
				with self.assertRaisesRegex(frappe.ValidationError, "Deal Type must be PERSONAL or COMPANY"):
					self.make_deal(deal_type=deal_type)

	def test_omitted_deal_type(self):
		deal = frappe.get_doc({
			"doctype": "DoubleT Deal",
			"deal_title": self.title,
			"contact": self.contact.name,
			"stage": self.open_stage.name,
		})
		with self.assertRaisesRegex(frappe.ValidationError, "Deal Type must be PERSONAL or COMPANY"):
			deal.insert()

	def test_company_to_personal_rejects_stale_company(self):
		deal = self.make_deal(deal_type="COMPANY", company=self.company.name)
		deal.deal_type = "PERSONAL"
		with self.assertRaisesRegex(frappe.ValidationError, "Company must be empty for a PERSONAL deal"):
			deal.save()
		deal.reload()
		self.assertEqual(deal.deal_type, "COMPANY")
		self.assertEqual(deal.company, self.company.name)

	def test_personal_to_company_requires_company(self):
		deal = self.make_deal()
		deal.deal_type = "COMPANY"
		with self.assertRaisesRegex(frappe.ValidationError, "Company is required for a COMPANY deal"):
			deal.save()
		deal.reload()
		self.assertEqual(deal.deal_type, "PERSONAL")
		self.assertFalse(deal.company)

	def test_negative_amount_is_rejected(self):
		with self.assertRaisesRegex(frappe.ValidationError, "Amount cannot be negative"):
			self.make_deal(amount=-1)

	def test_open_deal_has_no_lifecycle_fields(self):
		deal = self.make_deal(
			won_on=now_datetime(),
			lost_on=now_datetime(),
			lost_reason="Stale reason",
		)
		self.assertFalse(deal.won_on)
		self.assertFalse(deal.lost_on)
		self.assertFalse(deal.lost_reason)

	def test_open_to_won_sets_timestamp_and_clears_lost_fields(self):
		deal = self.make_deal()
		deal.stage = self.won_stage.name
		deal.lost_on = now_datetime()
		deal.lost_reason = "Stale reason"
		deal.save()

		self.assertTrue(deal.won_on)
		self.assertFalse(deal.lost_on)
		self.assertFalse(deal.lost_reason)

	def test_saving_won_preserves_timestamp(self):
		deal = self.make_deal()
		deal.stage = self.won_stage.name
		deal.save()
		frappe.db.set_value("DoubleT Deal", deal.name, "won_on", "2020-01-02 03:04:05", update_modified=False)
		deal.reload()
		original_won_on = frappe.db.get_value("DoubleT Deal", deal.name, "won_on")

		deal.deal_title += " edited"
		deal.save()
		self.assertEqual(frappe.db.get_value("DoubleT Deal", deal.name, "won_on"), original_won_on)

	def test_won_to_open_clears_timestamp(self):
		deal = self.make_deal(stage=self.won_stage.name)
		deal.stage = self.open_stage.name
		deal.save()

		self.assertFalse(deal.won_on)
		self.assertFalse(deal.lost_on)
		self.assertFalse(deal.lost_reason)

	def test_open_to_lost_requires_reason(self):
		deal = self.make_deal()
		deal.stage = self.lost_stage.name
		with self.assertRaisesRegex(frappe.ValidationError, "Lost Reason is required"):
			deal.save()

		persisted = frappe.get_doc("DoubleT Deal", deal.name)
		self.assertEqual(persisted.stage, self.open_stage.name)
		self.assertFalse(persisted.lost_on)

	def test_open_to_lost_sets_timestamp(self):
		deal = self.make_deal()
		deal.stage = self.lost_stage.name
		deal.lost_reason = "Customer declined"
		deal.save()

		self.assertTrue(deal.lost_on)
		self.assertEqual(deal.lost_reason, "Customer declined")
		self.assertFalse(deal.won_on)

	def test_saving_lost_preserves_timestamp(self):
		deal = self.make_deal(stage=self.lost_stage.name, lost_reason="Customer declined")
		frappe.db.set_value("DoubleT Deal", deal.name, "lost_on", "2020-01-02 03:04:05", update_modified=False)
		deal.reload()
		original_lost_on = frappe.db.get_value("DoubleT Deal", deal.name, "lost_on")

		deal.deal_title += " edited"
		deal.save()
		self.assertEqual(frappe.db.get_value("DoubleT Deal", deal.name, "lost_on"), original_lost_on)

	def test_lost_to_open_clears_lost_fields(self):
		deal = self.make_deal(stage=self.lost_stage.name, lost_reason="Customer declined")
		deal.stage = self.open_stage.name
		deal.save()

		self.assertFalse(deal.won_on)
		self.assertFalse(deal.lost_on)
		self.assertFalse(deal.lost_reason)

	def test_won_to_lost_sets_lost_fields_and_clears_won(self):
		deal = self.make_deal(stage=self.won_stage.name)
		deal.stage = self.lost_stage.name
		deal.lost_reason = "Budget withdrawn"
		deal.save()

		self.assertFalse(deal.won_on)
		self.assertTrue(deal.lost_on)
		self.assertEqual(deal.lost_reason, "Budget withdrawn")

	def test_lost_to_won_sets_won_and_clears_lost_fields(self):
		deal = self.make_deal(stage=self.lost_stage.name, lost_reason="Delayed")
		deal.stage = self.won_stage.name
		deal.save()

		self.assertTrue(deal.won_on)
		self.assertFalse(deal.lost_on)
		self.assertFalse(deal.lost_reason)

	def test_won_to_another_won_stage_preserves_timestamp(self):
		deal = self.make_deal(stage=self.won_stage.name)
		frappe.db.set_value("DoubleT Deal", deal.name, "won_on", "2020-01-02 03:04:05", update_modified=False)
		deal.reload()
		original_won_on = frappe.db.get_value("DoubleT Deal", deal.name, "won_on")
		other_won_stage = self.make_stage(f"Delta-{frappe.generate_hash(length=10)}", "WON")

		deal.stage = other_won_stage.name
		deal.save()
		self.assertEqual(frappe.db.get_value("DoubleT Deal", deal.name, "won_on"), original_won_on)

	def test_creating_lost_deal_requires_reason(self):
		with self.assertRaisesRegex(frappe.ValidationError, "Lost Reason is required"):
			self.make_deal(stage=self.lost_stage.name, lost_reason="   ")
