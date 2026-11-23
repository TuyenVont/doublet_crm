"""Permission-scoped analytics APIs for the Reports Hub."""

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt, getdate


BOOKED_ORDER_STATUSES = ("Confirmed", "Completed")
MAX_REPORT_RANGE_DAYS = 366
RECENT_ORDER_LIMIT = 10


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
