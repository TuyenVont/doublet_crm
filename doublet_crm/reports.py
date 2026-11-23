"""Permission-scoped analytics APIs for the Reports Hub."""

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate


BOOKED_ORDER_STATUSES = ("Confirmed", "Completed")
MAX_REPORT_RANGE_DAYS = 366
RECENT_ORDER_LIMIT = 10
RECENT_DEAL_LIMIT = 20
DEAL_LIFECYCLES = ("OPEN", "WON", "LOST")


def _validated_range(start_date, end_date):
	if not start_date or not end_date:
		frappe.throw(_("Start Date and End Date are required."), frappe.ValidationError)

	try:
		start = getdate(start_date)
		end = getdate(end_date)
	except (TypeError, ValueError):
		frappe.throw(_("Start Date and End Date must be valid dates."), frappe.ValidationError)

	if start > end:
		frappe.throw(_("Start Date cannot be after End Date."), frappe.ValidationError)
	if (end - start).days > MAX_REPORT_RANGE_DAYS:
		frappe.throw(
			_("Date range cannot exceed {0} days.").format(MAX_REPORT_RANGE_DAYS),
			frappe.ValidationError,
		)
	return start, end


def _validated_salesperson(salesperson, can_read_deals):
	value = (salesperson or "").strip()
	if not value:
		return None
	if len(value) > 140:
		frappe.throw(_("Salesperson is invalid."), frappe.ValidationError)
	if not can_read_deals:
		frappe.throw(_("You do not have permission to filter by Deal Owner."), frappe.PermissionError)

	owned_deal = frappe.get_list(
		"DoubleT Deal",
		filters={"deal_owner": value},
		pluck="name",
		limit_page_length=1,
	)
	if not owned_deal:
		frappe.throw(_("Salesperson must be an owner on a Deal you can access."), frappe.ValidationError)
	return value


def _deal_map(deal_names, can_read_deals):
	if not deal_names or not can_read_deals:
		return {}
	rows = frappe.get_list(
		"DoubleT Deal",
		filters={"name": ["in", sorted(deal_names)]},
		fields=["name", "deal_title", "deal_owner"],
		limit_page_length=0,
	)
	return {row.name: row for row in rows}


def _owner_key(order, deals):
	if not order.deal:
		return "__unassigned__"
	deal = deals.get(order.deal)
	if not deal:
		return "__restricted__"
	return deal.deal_owner or "__unassigned__"


def _summarize(rows, deals):
	trend = defaultdict(lambda: {"booked_sales": 0.0, "order_count": 0})
	owners = defaultdict(lambda: {"booked_sales": 0.0, "order_count": 0})
	booked_sales = 0.0

	for order in rows:
		amount = flt(order.total, 2)
		booked_sales += amount
		date_key = str(order.order_date)
		trend[date_key]["booked_sales"] += amount
		trend[date_key]["order_count"] += 1
		owner = owners[_owner_key(order, deals)]
		owner["booked_sales"] += amount
		owner["order_count"] += 1

	order_count = len(rows)
	return {
		"booked_sales": flt(booked_sales, 2),
		"order_count": order_count,
		"average_order_value": flt(booked_sales / order_count, 2) if order_count else 0.0,
		"trend": [
			{"date": date, **values}
			for date, values in sorted(trend.items())
		],
		"by_salesperson": [
			{
				"salesperson": None if key.startswith("__") else key,
				"label": (
					_("Unassigned") if key == "__unassigned__"
					else _("Deal unavailable") if key == "__restricted__"
					else key
				),
				"assignment_state": (
					"unassigned" if key == "__unassigned__"
					else "restricted" if key == "__restricted__"
					else "assigned"
				),
				"booked_sales": flt(values["booked_sales"], 2),
				"order_count": values["order_count"],
				"average_order_value": flt(values["booked_sales"] / values["order_count"], 2),
			}
			for key, values in sorted(
				owners.items(),
				key=lambda item: (-item[1]["booked_sales"], item[0]),
			)
		],
	}


def _deal_lifecycle(deal, stage=None):
	stage_type = (stage.stage_type if stage else "") or ""
	stage_type = stage_type.upper()
	if stage_type in DEAL_LIFECYCLES:
		return stage_type
	if deal.won_on:
		return "WON"
	if deal.lost_on:
		return "LOST"
	return "OPEN"


def _summarize_pipeline(deals, stages):
	by_stage = {}
	lifecycle = {
		key: {"deal_count": 0, "deal_value": 0.0}
		for key in DEAL_LIFECYCLES
	}
	total_value = 0.0

	for deal in deals:
		stage = stages.get(deal.stage)
		stage_key = deal.stage or "__unassigned__"
		stage_type = _deal_lifecycle(deal, stage)
		amount = flt(deal.amount, 2)
		total_value += amount
		state = lifecycle[stage_type]
		state["deal_count"] += 1
		state["deal_value"] += amount

		group = by_stage.setdefault(
			stage_key,
			{
				"name": deal.stage,
				"label": stage.stage_name if stage else (deal.stage or _("Unassigned Stage")),
				"stage_type": stage_type,
				"color": stage.color if stage else None,
				"sort_order": stage.sort_order if stage else 999999,
				"deal_count": 0,
				"deal_value": 0.0,
			},
		)
		group["deal_count"] += 1
		group["deal_value"] += amount

	for values in lifecycle.values():
		values["deal_value"] = flt(values["deal_value"], 2)

	return {
		"deal_count": len(deals),
		"total_deal_value": flt(total_value, 2),
		"open_pipeline_value": lifecycle["OPEN"]["deal_value"],
		"lifecycle": lifecycle,
		"by_stage": [
			{**row, "deal_value": flt(row["deal_value"], 2)}
			for row in sorted(
				by_stage.values(),
				key=lambda row: (row["sort_order"], row["label"], row["stage_type"]),
			)
		],
	}


@frappe.whitelist()
def get_sales_performance(start_date, end_date, salesperson=None):
	"""Return booked sales analytics from readable Confirmed/Completed Orders."""
	frappe.has_permission("DoubleT Order", "read", throw=True)
	start, end = _validated_range(start_date, end_date)
	can_read_deals = bool(frappe.has_permission("DoubleT Deal", "read"))
	salesperson = _validated_salesperson(salesperson, can_read_deals)

	orders = frappe.get_list(
		"DoubleT Order",
		filters=[
			["order_date", "between", [start, end]],
			["status", "in", BOOKED_ORDER_STATUSES],
		],
		fields=["name", "order_date", "status", "total", "currency", "deal"],
		order_by="order_date asc, name asc",
		limit_page_length=0,
	)
	deals = _deal_map({row.deal for row in orders if row.deal}, can_read_deals)
	if salesperson:
		orders = [row for row in orders if deals.get(row.deal) and deals[row.deal].deal_owner == salesperson]

	summary = _summarize(orders, deals)
	owners = sorted({deal.deal_owner for deal in deals.values() if deal.deal_owner})
	if salesperson and salesperson not in owners:
		owners.append(salesperson)
	owners.sort()

	recent = sorted(orders, key=lambda row: (str(row.order_date), row.name), reverse=True)
	return {
		"filters": {
			"start_date": str(start),
			"end_date": str(end),
			"salesperson": salesperson,
		},
		"permissions": {"orders": True, "deals": can_read_deals},
		"currency": "USD",
		"business_definition": _(
			"Booked sales are totals from Confirmed and Completed Orders; they are not paid revenue."
		),
		"salespeople": [{"value": owner, "label": owner} for owner in owners],
		**summary,
		"recent_orders": [
			{
				"name": order.name,
				"order_date": order.order_date,
				"status": order.status,
				"total": flt(order.total, 2),
				"deal": order.deal if order.deal in deals else None,
				"deal_label": deals[order.deal].deal_title if order.deal in deals else None,
				"deal_restricted": bool(order.deal and order.deal not in deals),
			}
			for order in recent[:RECENT_ORDER_LIMIT]
		],
	}


@frappe.whitelist()
def get_pipeline_analytics(start_date, end_date, salesperson=None):
	"""Return permission-scoped Deal pipeline analytics by current stage."""
	frappe.has_permission("DoubleT Deal", "read", throw=True)
	start, end = _validated_range(start_date, end_date)
	salesperson = _validated_salesperson(salesperson, can_read_deals=True)

	deals = frappe.get_list(
		"DoubleT Deal",
		filters=[
			["creation", ">=", f"{start} 00:00:00"],
			["creation", "<", f"{add_days(end, 1)} 00:00:00"],
		],
		fields=[
			"name",
			"deal_title",
			"amount",
			"deal_owner",
			"stage",
			"creation",
			"expected_close_date",
			"won_on",
			"lost_on",
		],
		order_by="creation desc, name desc",
		limit_page_length=0,
	)
	owners = sorted({deal.deal_owner for deal in deals if deal.deal_owner})
	if salesperson:
		deals = [deal for deal in deals if deal.deal_owner == salesperson]

	can_read_stages = bool(frappe.has_permission("DoubleT Deal Stage", "read"))
	stages = {}
	stage_names = sorted({deal.stage for deal in deals if deal.stage})
	if can_read_stages and stage_names:
		stage_rows = frappe.get_list(
			"DoubleT Deal Stage",
			filters={"name": ["in", stage_names]},
			fields=["name", "stage_name", "stage_type", "color", "sort_order"],
			order_by="sort_order asc, name asc",
			limit_page_length=0,
		)
		stages = {stage.name: stage for stage in stage_rows}

	summary = _summarize_pipeline(deals, stages)
	return {
		"filters": {
			"start_date": str(start),
			"end_date": str(end),
			"salesperson": salesperson,
			"date_field": "creation",
		},
		"permissions": {"deals": True, "stages": can_read_stages},
		"currency": "USD",
		"business_definition": _(
			"Open pipeline value is the sum of Deal Amount for Open stages. Won and Lost values are "
			"recorded Deal amounts, not realized or paid revenue. Date filters use Deal creation date."
		),
		"salespeople": [{"value": owner, "label": owner} for owner in owners],
		**summary,
		"recent_deals": [
			{
				"name": deal.name,
				"deal_title": deal.deal_title,
				"amount": flt(deal.amount, 2),
				"deal_owner": deal.deal_owner,
				"stage": deal.stage,
				"stage_label": (
					stages[deal.stage].stage_name if deal.stage in stages else (deal.stage or _("Unassigned Stage"))
				),
				"stage_type": _deal_lifecycle(deal, stages.get(deal.stage)),
				"creation": deal.creation,
				"expected_close_date": deal.expected_close_date,
			}
			for deal in deals[:RECENT_DEAL_LIMIT]
		],
	}
