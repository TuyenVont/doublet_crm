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
			"stage": stage or self.open_stage.name,
			**values,
		}).insert()

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
