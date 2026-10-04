import frappe
from frappe.desk.doctype.kanban_board.kanban_board import add_card, update_order, update_order_for_single_card
from frappe.tests.utils import FrappeTestCase

from doublet_crm.kanban import DEAL_BOARD_NAME, sync_deal_kanban_board


class TestDoubleTDealKanban(FrappeTestCase):
	def setUp(self):
		unique = frappe.generate_hash(length=10)
		self.title = f"Kanban Deal {unique}"
		self.open_stage = self.make_stage(f"First-{unique}", "OPEN", 30)
		self.won_stage = self.make_stage(f"Second-{unique}", "WON", 20)
		self.lost_stage = self.make_stage(f"Third-{unique}", "LOST", 10)
		self.board = sync_deal_kanban_board()
		self.contact = frappe.get_doc({
			"doctype": "DoubleT Contact",
        		"first_name": f"Kanban Contact {unique}",
		}).insert()

	def make_stage(self, name, stage_type, sort_order):
		return frappe.get_doc({
			"doctype": "DoubleT Deal Stage",
			"stage_name": name,
			"stage_type": stage_type,
			"sort_order": sort_order,
			"enabled": 1,
		}).insert()

	def make_card(self, stage=None, **values):
		stage = stage or self.open_stage.name
		deal = frappe.get_doc({
			"doctype": "DoubleT Deal",
			"deal_title": self.title,
			"deal_type": "PERSONAL",
                	"contact": self.contact.name,
			"stage": stage,
			**values,
		}).insert()
		add_card(self.board.name, deal.name, stage)
		return deal

	def move_card(self, deal, target_stage):
		return update_order_for_single_card(
			self.board.name,
			deal.name,
			frappe.db.get_value("DoubleT Deal", deal.name, "stage"),
			target_stage,
			0,
			0,
		)

	def test_board_uses_existing_stage_records_as_link_columns(self):
		stage_count = frappe.db.count("DoubleT Deal Stage")
		board = sync_deal_kanban_board()

		self.assertEqual(board.name, DEAL_BOARD_NAME)
		self.assertEqual(board.reference_doctype, "DoubleT Deal")
		self.assertEqual(board.field_name, "stage")
		self.assertFalse(board.private)
		self.assertEqual(frappe.get_meta("DoubleT Deal").get_field("stage").fieldtype, "Link")
		self.assertEqual(frappe.db.count("DoubleT Deal Stage"), stage_count)
		self.assertEqual(
			{column.column_name for column in board.columns},
			set(frappe.get_all("DoubleT Deal Stage", pluck="name")),
		)

	def test_column_order_follows_stage_sort_order(self):
		expected = frappe.get_all(
			"DoubleT Deal Stage", pluck="name", order_by="sort_order asc, name asc"
		)
		self.assertEqual([column.column_name for column in self.board.columns], expected)

	def test_stage_sort_change_preserves_card_order(self):
		deal = self.make_card()
		before = frappe.get_doc("Kanban Board", self.board.name)
		before_order = next(c.order for c in before.columns if c.column_name == self.open_stage.name)

		self.open_stage.sort_order = 1
		self.open_stage.save()
		board = frappe.get_doc("Kanban Board", self.board.name)
		expected = frappe.get_all(
			"DoubleT Deal Stage", pluck="name", order_by="sort_order asc, name asc"
		)
		self.assertEqual([column.column_name for column in board.columns], expected)
		self.assertEqual(
			next(c.order for c in board.columns if c.column_name == self.open_stage.name), before_order
		)
		self.assertIn(deal.name, frappe.parse_json(before_order))

	def test_open_to_won_runs_deal_lifecycle(self):
		deal = self.make_card()
		board = self.move_card(deal, self.won_stage.name)
		deal.reload()

		self.assertEqual(deal.stage, self.won_stage.name)
		self.assertTrue(deal.won_on)
		self.assertFalse(deal.lost_on)
		self.assertFalse(deal.lost_reason)
		self.assertIn(
			deal.name,
			frappe.parse_json(next(c.order for c in board.columns if c.column_name == self.won_stage.name)),
		)

	def test_won_to_open_clears_won_timestamp(self):
		deal = self.make_card(self.won_stage.name)
		self.assertTrue(deal.won_on)
		self.move_card(deal, self.open_stage.name)
		deal.reload()

		self.assertEqual(deal.stage, self.open_stage.name)
		self.assertFalse(deal.won_on)

	def test_bulk_order_update_also_runs_deal_lifecycle(self):
		deal = self.make_card()
		update_order(
			self.board.name,
			frappe.as_json({self.open_stage.name: [], self.won_stage.name: [deal.name]}),
		)
		deal.reload()

		self.assertEqual(deal.stage, self.won_stage.name)
		self.assertTrue(deal.won_on)

	def test_open_to_lost_without_reason_is_rejected(self):
		deal = self.make_card()
		before = frappe.get_doc("Kanban Board", self.board.name)
		before_order = next(c.order for c in before.columns if c.column_name == self.open_stage.name)
		save_point = f"kanban_lost_{frappe.generate_hash(length=10)}"
		frappe.db.savepoint(save_point)
		try:
			with self.assertRaisesRegex(frappe.ValidationError, "Lost Reason is required"):
				self.move_card(deal, self.lost_stage.name)
		finally:
			# A failed HTTP request rolls back; reproduce that boundary for this direct call.
			frappe.db.rollback(save_point=save_point)

		deal.reload()
		board = frappe.get_doc("Kanban Board", self.board.name)
		self.assertEqual(deal.stage, self.open_stage.name)
		self.assertFalse(deal.lost_on)
		self.assertEqual(next(c.order for c in board.columns if c.column_name == self.open_stage.name), before_order)

	def test_move_to_lost_succeeds_when_reason_is_already_present(self):
		deal = self.make_card()
		# Model an existing Deal that already has a reason before the Kanban request.
		frappe.db.set_value("DoubleT Deal", deal.name, "lost_reason", "Customer declined", update_modified=False)
		self.move_card(deal, self.lost_stage.name)
		deal.reload()

		self.assertEqual(deal.stage, self.lost_stage.name)
		self.assertEqual(deal.lost_reason, "Customer declined")
		self.assertTrue(deal.lost_on)
		self.assertFalse(deal.won_on)

	def test_lost_to_another_lost_stage_keeps_reason_and_timestamp(self):
		deal = self.make_card(self.lost_stage.name, lost_reason="Customer declined")
		frappe.db.set_value("DoubleT Deal", deal.name, "lost_on", "2020-01-02 03:04:05", update_modified=False)
		original_lost_on = frappe.db.get_value("DoubleT Deal", deal.name, "lost_on")
		other_lost_stage = self.make_stage(f"Other-{frappe.generate_hash(length=10)}", "LOST", 40)
		self.move_card(deal, other_lost_stage.name)
		deal.reload()

		self.assertEqual(deal.stage, other_lost_stage.name)
		self.assertEqual(deal.lost_reason, "Customer declined")
		self.assertEqual(frappe.db.get_value("DoubleT Deal", deal.name, "lost_on"), original_lost_on)

	def test_nonexistent_stage_column_is_rejected(self):
		deal = self.make_card()
		invalid_stage = f"Missing-{frappe.generate_hash(length=10)}"
		board = frappe.get_doc("Kanban Board", self.board.name)
		board.append("columns", {"column_name": invalid_stage, "order": "[]"})
		with self.assertRaisesRegex(frappe.ValidationError, "columns are managed"):
			board.save(ignore_permissions=True)

		persisted = frappe.get_doc("Kanban Board", self.board.name)
		self.assertNotIn(invalid_stage, [column.column_name for column in persisted.columns])
		self.assertEqual(frappe.db.get_value("DoubleT Deal", deal.name, "stage"), self.open_stage.name)

	def test_other_doctype_board_keeps_native_column_behavior(self):
		board = frappe.get_doc({
			"doctype": "Kanban Board",
			"kanban_board_name": f"Other-{frappe.generate_hash(length=10)}",
			"reference_doctype": "ToDo",
			"field_name": "status",
		})
		board.append("columns", {"column_name": "Open"})
		board.insert(ignore_permissions=True)
		board.append("columns", {"column_name": "Closed", "order": "[]"})
		board.save(ignore_permissions=True)

		self.assertEqual([column.column_name for column in board.columns], ["Open", "Closed"])
