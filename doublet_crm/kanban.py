"""Keep the native DoubleT Deal Kanban columns aligned with Deal Stages."""

import frappe
from frappe import _
from frappe.desk.doctype.kanban_board.kanban_board import get_order_for_column


DEAL_BOARD_NAME = "DoubleT Deal Pipeline"


def validate_deal_kanban_board(board, method=None):
	"""Keep only real Stage columns, in master-data order, on this board."""
	if board.name != DEAL_BOARD_NAME and board.kanban_board_name != DEAL_BOARD_NAME:
		return

	if board.reference_doctype != "DoubleT Deal" or board.field_name != "stage":
		frappe.throw(_("The DoubleT Deal Pipeline must use DoubleT Deal.stage."), frappe.ValidationError)

	stage_names = frappe.get_all(
		"DoubleT Deal Stage", pluck="name", order_by="sort_order asc, name asc"
	)
	if [column.column_name for column in board.columns] != stage_names:
		frappe.throw(
			_("Deal Kanban columns are managed by DoubleT Deal Stage. Edit Stage records instead."),
			frappe.ValidationError,
		)


def sync_deal_kanban_board(doc=None, method=None, *args):
	"""Create or update the public Deal board using Stage names as Link values."""
	stage_names = frappe.get_all(
		"DoubleT Deal Stage",
		pluck="name",
		order_by="sort_order asc, name asc",
	)
	board_exists = frappe.db.exists("Kanban Board", DEAL_BOARD_NAME)
	if not stage_names and not board_exists:
		return None

	if board_exists:
		board = frappe.get_doc("Kanban Board", DEAL_BOARD_NAME)
		if board.reference_doctype != "DoubleT Deal" or board.field_name != "stage":
			frappe.throw(_("The DoubleT Deal Pipeline board name is already in use."), frappe.ValidationError)
	else:
		board = frappe.get_doc({
			"doctype": "Kanban Board",
			"kanban_board_name": DEAL_BOARD_NAME,
			"reference_doctype": "DoubleT Deal",
			"field_name": "stage",
			"private": 0,
		})

	if [column.column_name for column in board.columns] == stage_names and all(
		column.order for column in board.columns
	):
		return board

	previous_columns = {column.column_name: column for column in board.columns}
	renamed_from = args[0] if method == "after_rename" and len(args) >= 2 else None
	renamed_to = args[1] if method == "after_rename" and len(args) >= 2 else None
	board.set("columns", [])
	for stage_name in stage_names:
		previous = previous_columns.get(stage_name)
		if not previous and stage_name == renamed_to:
			previous = previous_columns.get(renamed_from)
		board.append("columns", {
			"column_name": stage_name,
			"status": previous.status if previous else "Active",
			"indicator": previous.indicator if previous else "Gray",
			"order": previous.order if previous and previous.order else get_order_for_column(board, stage_name),
		})

	if board.is_new():
		board.insert(ignore_permissions=True)
	else:
		board.save(ignore_permissions=True)
	return board
