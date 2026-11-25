"""Permission-scoped analytics APIs for the Reports Hub."""

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, get_datetime, getdate, now_datetime, nowdate

BOOKED_ORDER_STATUSES = ("Confirmed", "Completed")
MAX_REPORT_RANGE_DAYS = 366
RECENT_ORDER_LIMIT = 10
RECENT_DEAL_LIMIT = 20
DEAL_LIFECYCLES = ("OPEN", "WON", "LOST")
STALE_DEAL_DAYS = 30
MISSING_LOST_REASON = "No reason provided"


def _validated_range(start_date, end_date):
	if not start_date or not end_date:
		frappe.throw(_("Start Date and End Date are required."), frappe.ValidationError)
	try:
		start, end = getdate(start_date), getdate(end_date)
	except (TypeError, ValueError):
		frappe.throw(_("Start Date and End Date must be valid dates."), frappe.ValidationError)
	if start > end:
		frappe.throw(_("Start Date cannot be after End Date."), frappe.ValidationError)
	if (end - start).days > MAX_REPORT_RANGE_DAYS:
		frappe.throw(_("Date range cannot exceed {0} days.").format(MAX_REPORT_RANGE_DAYS), frappe.ValidationError)
	return start, end


def _previous_period(start, end):
	days = (end - start).days + 1
	return add_days(start, -days), add_days(start, -1)


def _validated_salesperson(salesperson, can_read_deals):
	value = (salesperson or "").strip()
	if not value:
		return None
	if len(value) > 140:
		frappe.throw(_("Salesperson is invalid."), frappe.ValidationError)
	if not can_read_deals:
		frappe.throw(_("You do not have permission to filter by Deal Owner."), frappe.PermissionError)
	if not frappe.get_list("DoubleT Deal", filters={"deal_owner": value}, pluck="name", limit_page_length=1):
		frappe.throw(_("Salesperson must be an owner on a Deal you can access."), frappe.ValidationError)
	return value


def _deal_map(deal_names, can_read_deals):
	if not deal_names or not can_read_deals:
		return {}
	rows = frappe.get_list(
		"DoubleT Deal", filters={"name": ["in", sorted(deal_names)]},
		fields=["name", "deal_title", "deal_owner"], limit_page_length=0,
	)
	return {row.name: row for row in rows}


def _owner_key(row, deals=None):
	if deals is None:
		return row.deal_owner or "__unassigned__"
	if not row.deal:
		return "__unassigned__"
	deal = deals.get(row.deal)
	return (deal.deal_owner or "__unassigned__") if deal else "__restricted__"


def _owner_label(key):
	return _("Unassigned") if key == "__unassigned__" else _("Deal unavailable") if key == "__restricted__" else key


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
		"booked_sales": flt(booked_sales, 2), "order_count": order_count,
		"average_order_value": flt(booked_sales / order_count, 2) if order_count else 0.0,
		"trend": [{"date": date, **values} for date, values in sorted(trend.items())],
		"by_salesperson": [{
			"salesperson": None if key.startswith("__") else key, "label": _owner_label(key),
			"assignment_state": key[2:-2] if key.startswith("__") else "assigned",
			"booked_sales": flt(values["booked_sales"], 2), "order_count": values["order_count"],
			"average_order_value": flt(values["booked_sales"] / values["order_count"], 2),
		} for key, values in sorted(owners.items(), key=lambda item: (-item[1]["booked_sales"], item[0]))],
	}


def _deal_row(deal, event_field=None):
	created = get_datetime(deal.creation) if deal.creation else None
	event_value = getattr(deal, event_field, None) if event_field else None
	event = get_datetime(event_value) if event_value else None
	duration = flt((event - created).total_seconds() / 86400, 2) if event_field == "won_on" and created and event and event >= created else None
	return {
		"name": deal.name, "deal_title": deal.deal_title, "deal_owner": deal.deal_owner,
		"amount": flt(deal.amount, 2), "creation": deal.creation, "event_date": event_value,
		"close_duration_days": duration,
		"lost_reason": (deal.lost_reason or "").strip() if hasattr(deal, "lost_reason") else None,
	}


def _summarize_outcomes(won_deals, lost_deals):
	closed_count = len(won_deals) + len(lost_deals)
	durations = [row["close_duration_days"] for row in (_deal_row(deal, "won_on") for deal in won_deals) if row["close_duration_days"] is not None]
	return {
		"won_count": len(won_deals), "lost_count": len(lost_deals), "closed_count": closed_count,
		"won_deal_value": flt(sum(flt(deal.amount, 2) for deal in won_deals), 2),
		"lost_deal_value": flt(sum(flt(deal.amount, 2) for deal in lost_deals), 2),
		"win_rate": flt(len(won_deals) * 100 / closed_count, 2) if closed_count else 0.0,
		"average_close_duration_days": flt(sum(durations) / len(durations), 2) if durations else None,
		"close_duration_denominator": len(durations),
	}


def _unavailable_outcomes():
	return {
		"won_count": None,
		"lost_count": None,
		"closed_count": None,
		"won_deal_value": None,
		"lost_deal_value": None,
		"win_rate": None,
		"average_close_duration_days": None,
		"close_duration_denominator": None,
	}


def _salesperson_breakdown(order_summary, won_deals, lost_deals, deal_metrics_available=True):
	owners = defaultdict(lambda: {"booked_sales": 0.0, "order_count": 0, "won_count": 0, "lost_count": 0, "won_deal_value": 0.0})
	for row in order_summary["by_salesperson"]:
		key = row["salesperson"] or f"__{row['assignment_state']}__"
		owners[key].update(booked_sales=row["booked_sales"], order_count=row["order_count"])
	for state, deals in (("won", won_deals), ("lost", lost_deals)):
		for deal in deals:
			owner = owners[_owner_key(deal)]
			owner[f"{state}_count"] += 1
			if state == "won":
				owner["won_deal_value"] += flt(deal.amount, 2)
	result = []
	for key, values in owners.items():
		closed = values["won_count"] + values["lost_count"]
		result.append({
			"salesperson": None if key.startswith("__") else key, "label": _owner_label(key), **values,
			"booked_sales": flt(values["booked_sales"], 2), "won_deal_value": flt(values["won_deal_value"], 2),
			"win_rate": flt(values["won_count"] * 100 / closed, 2) if closed else 0.0, "closed_count": closed,
		})
	if not deal_metrics_available:
		for row in result:
			for key in ("won_count", "lost_count", "won_deal_value", "win_rate", "closed_count"):
				row[key] = None
	return sorted(result, key=lambda row: (-(row["won_deal_value"] or 0), -row["booked_sales"], row["label"]))


def _deal_lifecycle(deal, stage=None):
	stage_type = ((stage.stage_type if stage else "") or "").upper()
	if stage_type in DEAL_LIFECYCLES:
		return stage_type
	return "WON" if deal.won_on else "LOST" if deal.lost_on else "OPEN"


def _summarize_pipeline(deals, stages):
	by_stage = {}
	lifecycle = {key: {"deal_count": 0, "deal_value": 0.0} for key in DEAL_LIFECYCLES}
	total_value = 0.0
	for deal in deals:
		stage = stages.get(deal.stage)
		stage_type = _deal_lifecycle(deal, stage)
		amount = flt(deal.amount, 2)
		total_value += amount
		lifecycle[stage_type]["deal_count"] += 1
		lifecycle[stage_type]["deal_value"] += amount
		group = by_stage.setdefault(deal.stage or "__unassigned__", {
			"name": deal.stage, "label": stage.stage_name if stage else (deal.stage or _("Unassigned Stage")),
			"stage_type": stage_type, "color": stage.color if stage else None,
			"sort_order": stage.sort_order if stage else 999999, "deal_count": 0, "deal_value": 0.0,
		})
		group["deal_count"] += 1
		group["deal_value"] += amount
	for values in lifecycle.values():
		values["deal_value"] = flt(values["deal_value"], 2)
	return {
		"deal_count": len(deals), "total_deal_value": flt(total_value, 2),
		"open_pipeline_value": lifecycle["OPEN"]["deal_value"], "lifecycle": lifecycle,
		"by_stage": [{**row, "deal_value": flt(row["deal_value"], 2)} for row in sorted(by_stage.values(), key=lambda row: (row["sort_order"], row["label"], row["stage_type"]))],
	}


def _summarize_lost_reasons(deals):
	groups = defaultdict(lambda: {"deal_count": 0, "deal_value": 0.0, "deals": []})
	for deal in deals:
		reason = (deal.lost_reason or "").strip() or MISSING_LOST_REASON
		groups[reason]["deal_count"] += 1
		groups[reason]["deal_value"] += flt(deal.amount, 2)
		groups[reason]["deals"].append(_deal_row(deal, "lost_on"))
	total_count, total_value = len(deals), sum(flt(deal.amount, 2) for deal in deals)
	return sorted([{
		"reason": reason, "deal_count": values["deal_count"], "deal_value": flt(values["deal_value"], 2),
		"count_percentage": flt(values["deal_count"] * 100 / total_count, 2) if total_count else 0.0,
		"value_percentage": flt(values["deal_value"] * 100 / total_value, 2) if total_value else 0.0,
		"deals": values["deals"],
	} for reason, values in groups.items()], key=lambda row: (-row["deal_count"], -row["deal_value"], row["reason"]))


def _comparison(current, previous, keys):
	return {key: {
		"current": current.get(key), "previous": previous.get(key),
		"change": flt(current.get(key) - previous.get(key), 2) if current.get(key) is not None and previous.get(key) is not None else None,
	} for key in keys}


def _orders_for_period(start, end):
	return frappe.get_list(
		"DoubleT Order", filters=[["order_date", "between", [start, end]], ["status", "in", BOOKED_ORDER_STATUSES]],
		fields=["name", "order_date", "status", "total", "currency", "deal"], order_by="order_date asc, name asc", limit_page_length=0,
	)


def _outcome_deals(start, end, event_field):
	filters = [[event_field, ">=", f"{start} 00:00:00"], [event_field, "<", f"{add_days(end, 1)} 00:00:00"]]
	return frappe.get_list(
		"DoubleT Deal", filters=filters,
		fields=["name", "deal_title", "deal_owner", "amount", "creation", "won_on", "lost_on", "lost_reason"],
		order_by=f"{event_field} desc, name desc", limit_page_length=0,
	)


def _sales_period(start, end, salesperson, can_read_deals):
	orders = _orders_for_period(start, end)
	deals = _deal_map({row.deal for row in orders if row.deal}, can_read_deals)
	won_deals = _outcome_deals(start, end, "won_on") if can_read_deals else []
	lost_deals = _outcome_deals(start, end, "lost_on") if can_read_deals else []
	available_owners = {deal.deal_owner for deal in deals.values() if deal.deal_owner}
	available_owners.update(deal.deal_owner for deal in won_deals + lost_deals if deal.deal_owner)
	if salesperson:
		orders = [row for row in orders if deals.get(row.deal) and deals[row.deal].deal_owner == salesperson]
		won_deals = [deal for deal in won_deals if deal.deal_owner == salesperson]
		lost_deals = [deal for deal in lost_deals if deal.deal_owner == salesperson]
	order_summary = _summarize(orders, deals)
	outcomes = _summarize_outcomes(won_deals, lost_deals) if can_read_deals else _unavailable_outcomes()
	return orders, deals, order_summary, won_deals, lost_deals, outcomes, available_owners


@frappe.whitelist()
def get_sales_performance(start_date, end_date, salesperson=None, compare_previous=0):
	"""Return booked Order metrics and Deal outcomes, each scoped by its own event date."""
	frappe.has_permission("DoubleT Order", "read", throw=True)
	start, end = _validated_range(start_date, end_date)
	can_read_deals = bool(frappe.has_permission("DoubleT Deal", "read"))
	salesperson = _validated_salesperson(salesperson, can_read_deals)
	orders, deals, order_summary, won_deals, lost_deals, outcomes, available_owners = _sales_period(start, end, salesperson, can_read_deals)
	comparison = None
	if cint(compare_previous):
		previous_start, previous_end = _previous_period(start, end)
		_previous_order_rows, _previous_deal_map, previous_orders, previous_won, previous_lost, previous_outcomes, _previous_owners = _sales_period(previous_start, previous_end, salesperson, can_read_deals)
		comparison = {
			"definition": _("Immediately preceding period with the same inclusive number of calendar days."),
			"start_date": str(previous_start), "end_date": str(previous_end),
			"metrics": _comparison({**order_summary, **outcomes}, {**previous_orders, **previous_outcomes}, (
				"booked_sales", "order_count", "average_order_value", "won_count", "lost_count", "won_deal_value", "win_rate", "average_close_duration_days",
			)),
			"won_deals": [_deal_row(deal, "won_on") for deal in previous_won],
			"lost_deals": [_deal_row(deal, "lost_on") for deal in previous_lost],
		}
	owners = set(available_owners)
	if salesperson:
		owners.add(salesperson)
	recent = sorted(orders, key=lambda row: (str(row.order_date), row.name), reverse=True)
	return {
		"filters": {"start_date": str(start), "end_date": str(end), "salesperson": salesperson},
		"permissions": {"orders": True, "deals": can_read_deals},
		"capabilities": {"team_filter": {"supported": False, "reason": _("Team filtering is unavailable because DoubleT Deal has no team field.")}},
		"currency": "USD",
		"business_definition": _("Booked Sales uses Confirmed/Completed Order totals by Order Date and is not paid revenue. Won/Lost counts use Won On/Lost On; Won Deal Value is recorded Deal Amount, not revenue. Win Rate = Won / (Won + Lost). Average close duration uses valid Won On minus Creation records."),
		"salespeople": [{"value": owner, "label": owner} for owner in sorted(owners)],
		**order_summary, **outcomes,
		"employee_breakdown": _salesperson_breakdown(order_summary, won_deals, lost_deals, can_read_deals),
		"won_deals": [_deal_row(deal, "won_on") for deal in won_deals],
		"lost_deals": [_deal_row(deal, "lost_on") for deal in lost_deals], "comparison": comparison,
		"recent_orders": [{
			"name": order.name, "order_date": order.order_date, "status": order.status, "total": flt(order.total, 2),
			"deal": order.deal if order.deal in deals else None,
			"deal_label": deals[order.deal].deal_title if order.deal in deals else None,
			"deal_restricted": bool(order.deal and order.deal not in deals),
		} for order in recent[:RECENT_ORDER_LIMIT]],
		"order_drilldown": [{
			"name": order.name, "order_date": order.order_date, "status": order.status,
			"total": flt(order.total, 2), "deal": order.deal if order.deal in deals else None,
			"deal_label": deals[order.deal].deal_title if order.deal in deals else None,
			"deal_restricted": bool(order.deal and order.deal not in deals),
		} for order in recent],
	}


DEAL_REPORT_FIELDS = ["name", "deal_title", "amount", "deal_owner", "stage", "creation", "modified", "expected_close_date", "won_on", "lost_on", "lost_reason"]


def _get_deals(filters, order_by):
	return frappe.get_list("DoubleT Deal", filters=filters, fields=DEAL_REPORT_FIELDS, order_by=order_by, limit_page_length=0)


def _stages_for(deal_groups, can_read_stages):
	if not can_read_stages:
		return {}
	stage_names = sorted({deal.stage for deals in deal_groups for deal in deals if deal.stage})
	if not stage_names:
		return {}
	rows = frappe.get_list(
		"DoubleT Deal Stage", filters={"name": ["in", stage_names]},
		fields=["name", "stage_name", "stage_type", "color", "sort_order"], order_by="sort_order asc, name asc", limit_page_length=0,
	)
	return {stage.name: stage for stage in rows}


def _pipeline_rows(start, end):
	created = _get_deals([["creation", ">=", f"{start} 00:00:00"], ["creation", "<", f"{add_days(end, 1)} 00:00:00"]], "creation desc, name desc")
	lost = _get_deals([["lost_on", ">=", f"{start} 00:00:00"], ["lost_on", "<", f"{add_days(end, 1)} 00:00:00"]], "lost_on desc, name desc")
	as_of = min(end, getdate(nowdate()))
	overdue_filters = [["expected_close_date", "between", [start, add_days(as_of, -1)]], ["creation", "<", f"{add_days(as_of, 1)} 00:00:00"]] if start < as_of else [["name", "=", "__no_overdue_deals__"]]
	overdue = _get_deals(overdue_filters, "expected_close_date asc, name asc")
	stale_cutoff = add_days(as_of, -STALE_DEAL_DAYS)
	stale = _get_deals([["creation", "<", f"{add_days(as_of, 1)} 00:00:00"], ["modified", "<=", f"{stale_cutoff} 23:59:59.999999"]], "modified asc, name asc")
	return created, lost, overdue, stale, as_of, stale_cutoff


def _pipeline_period(start, end, salesperson, can_read_stages):
	created, lost, overdue_candidates, stale_candidates, as_of, stale_cutoff = _pipeline_rows(start, end)
	stages = _stages_for((created, lost, overdue_candidates, stale_candidates), can_read_stages)
	overdue = [deal for deal in overdue_candidates if _deal_lifecycle(deal, stages.get(deal.stage)) == "OPEN"]
	stale = [deal for deal in stale_candidates if _deal_lifecycle(deal, stages.get(deal.stage)) == "OPEN"]
	available_owners = {
		deal.deal_owner
		for deals in (created, lost, overdue, stale)
		for deal in deals
		if deal.deal_owner
	}
	if salesperson:
		created = [deal for deal in created if deal.deal_owner == salesperson]
		lost = [deal for deal in lost if deal.deal_owner == salesperson]
		overdue = [deal for deal in overdue if deal.deal_owner == salesperson]
		stale = [deal for deal in stale if deal.deal_owner == salesperson]
	return {
		"created": created, "lost": lost,
		"overdue": overdue,
		"stale": stale,
		"as_of": as_of, "stale_cutoff": stale_cutoff, "stages": stages,
		"owners": available_owners, "summary": _summarize_pipeline(created, stages),
	}


def _risk_row(deal, stages):
	return {
		**_deal_row(deal), "stage": deal.stage,
		"stage_label": stages[deal.stage].stage_name if deal.stage in stages else (deal.stage or _("Unassigned Stage")),
		"expected_close_date": deal.expected_close_date, "modified": deal.modified,
	}


@frappe.whitelist()
def get_pipeline_analytics(start_date, end_date, salesperson=None, compare_previous=0):
	"""Return current-stage, Lost Reason and open-Deal risk analytics."""
	frappe.has_permission("DoubleT Deal", "read", throw=True)
	start, end = _validated_range(start_date, end_date)
	salesperson = _validated_salesperson(salesperson, can_read_deals=True)
	can_read_stages = bool(frappe.has_permission("DoubleT Deal Stage", "read"))
	period = _pipeline_period(start, end, salesperson, can_read_stages)
	owners = sorted(period["owners"])
	if salesperson and salesperson not in owners:
		owners.append(salesperson)
	owners.sort()
	comparison = None
	if cint(compare_previous):
		previous_start, previous_end = _previous_period(start, end)
		previous = _pipeline_period(previous_start, previous_end, salesperson, can_read_stages)
		current_metrics = {**period["summary"], "lost_reason_deal_count": len(period["lost"]), "overdue_open_count": len(period["overdue"]), "stale_open_count": len(period["stale"])}
		previous_metrics = {**previous["summary"], "lost_reason_deal_count": len(previous["lost"]), "overdue_open_count": len(previous["overdue"]), "stale_open_count": len(previous["stale"])}
		comparison = {
			"definition": _(
				"Immediately preceding period with the same inclusive number of calendar days. "
				"Created-cohort stage metrics use each Deal's current stage; they are not historical stage snapshots."
			),
			"start_date": str(previous_start), "end_date": str(previous_end),
			"metrics": _comparison(current_metrics, previous_metrics, ("deal_count", "total_deal_value", "open_pipeline_value", "lost_reason_deal_count", "overdue_open_count", "stale_open_count")),
		}
	stages = period["stages"]
	return {
		"filters": {
			"start_date": str(start), "end_date": str(end), "salesperson": salesperson,
			"stage_date_field": "creation", "lost_reason_date_field": "lost_on", "overdue_date_field": "expected_close_date",
		},
		"permissions": {"deals": True, "stages": can_read_stages},
		"capabilities": {"team_filter": {"supported": False, "reason": _("Team filtering is unavailable because DoubleT Deal has no team field.")}},
		"currency": "USD",
		"business_definition": _(
			"Current-stage metrics use Deal Creation. Lost Reason uses Lost On. Overdue means an Open Deal "
			"whose Expected Close Date falls within the selected range and is earlier than the report as-of date. "
			"Stale means an Open Deal last modified on or before the 30-day cutoff date as of End Date. "
			"Deal Amount is not paid revenue."
		),
		"rounding_definition": _("Reason percentages are rounded to two decimals; displayed shares can differ from 100% by rounding."),
		"salespeople": [{"value": owner, "label": owner} for owner in owners], **period["summary"],
		"lost_reason_count": len(period["lost"]), "lost_reason_value": flt(sum(flt(deal.amount, 2) for deal in period["lost"]), 2),
		"lost_reasons": _summarize_lost_reasons(period["lost"]),
		"overdue_open_count": len(period["overdue"]), "overdue_open_value": flt(sum(flt(deal.amount, 2) for deal in period["overdue"]), 2),
		"overdue_deals": [_risk_row(deal, stages) for deal in period["overdue"]],
		"stale_open_count": len(period["stale"]), "stale_open_value": flt(sum(flt(deal.amount, 2) for deal in period["stale"]), 2),
		"stale_days": STALE_DEAL_DAYS, "stale_cutoff": str(period["stale_cutoff"]),
		"stale_deals": [_risk_row(deal, stages) for deal in period["stale"]], "as_of_date": str(period["as_of"]),
		"created_deals": [_risk_row(deal, stages) for deal in period["created"]],
		"comparison": comparison,
		"recent_deals": [{**_risk_row(deal, stages), "stage_type": _deal_lifecycle(deal, stages.get(deal.stage))} for deal in period["created"][:RECENT_DEAL_LIMIT]],
	}


# ===== Customer Journey Report (REP-06) =====

JOURNEY_QUOTATION_STATUSES = ("Draft", "Sent", "Accepted", "Rejected")
JOURNEY_ORDER_STATUSES = ("Draft", "Confirmed", "Completed", "Cancelled")


def _journey_leads(start, end):
	"""Leads with creation in range."""
	return frappe.get_list(
		"DoubleT Lead", filters=[["creation", ">=", f"{start} 00:00:00"], ["creation", "<", f"{add_days(end, 1)} 00:00:00"]],
		fields=["name", "lead_name", "lead_owner", "source", "creation", "converted_deal"],
		order_by="creation desc, name desc", limit_page_length=0,
	)


def _journey_deals_from_leads(leads):
	"""Resolve both source_lead and converted_deal without duplicating Deals."""
	if not leads:
		return {}
	lead_names = {lead.name for lead in leads}
	fields = ["name", "deal_title", "deal_owner", "amount", "creation", "won_on", "lost_on", "source_lead"]
	rows = frappe.get_list(
		"DoubleT Deal", filters=[["source_lead", "in", sorted(lead_names)]], fields=fields,
		order_by="creation desc, name desc", limit_page_length=0,
	)
	converted_names = sorted({lead.converted_deal for lead in leads if lead.converted_deal})
	if converted_names:
		rows.extend(frappe.get_list(
			"DoubleT Deal", filters=[["name", "in", converted_names]], fields=fields,
			order_by="creation desc, name desc", limit_page_length=0,
		))
	by_name = {deal.name: deal for deal in rows}
	result = defaultdict(list)
	for deal in by_name.values():
		if deal.source_lead in lead_names:
			result[deal.source_lead].append(deal)
	for lead in leads:
		if lead.converted_deal and lead.converted_deal in by_name:
			if all(deal.name != lead.converted_deal for deal in result[lead.name]):
				result[lead.name].append(by_name[lead.converted_deal])
	for values in result.values():
		values.sort(key=lambda deal: (str(deal.creation or ""), deal.name), reverse=True)
	return dict(result)


def _journey_quotations_for_deals(deal_names):
	"""Quotations linked to the given deals."""
	if not deal_names:
		return {}
	quotations = frappe.get_list(
		"DoubleT Quotation", filters=[["deal", "in", deal_names]],
		fields=["name", "deal", "status", "grand_total", "creation"],
		order_by="creation desc, name desc", limit_page_length=0,
	)
	result = defaultdict(list)
	for q in quotations:
		result[q.deal].append(q)
	return dict(result)


def _journey_orders_for_quotations(quotation_names):
	"""Orders linked to the given quotations."""
	if not quotation_names:
		return {}
	orders = frappe.get_list(
		"DoubleT Order", filters=[["quotation", "in", quotation_names]],
		fields=["name", "quotation", "deal", "status", "total", "order_date"],
		order_by="order_date desc, name desc", limit_page_length=0,
	)
	result = defaultdict(list)
	for o in orders:
		result[o.quotation].append(o)
	return dict(result)


def _journey_orders_for_deals(deal_names):
	"""Orders directly linked to deals (via deal field)."""
	if not deal_names:
		return {}
	orders = frappe.get_list(
		"DoubleT Order", filters=[["deal", "in", deal_names]],
		fields=["name", "deal", "status", "total", "order_date"],
		order_by="order_date desc, name desc", limit_page_length=0,
	)
	result = defaultdict(list)
	for o in orders:
		result[o.deal].append(o)
	return dict(result)


def _journey_entities(lead, deals_for_leads, quotations, orders_by_quotation, orders_by_deal):
	deals = deals_for_leads.get(lead.name, [])
	quote_rows = {quote.name: quote for deal in deals for quote in quotations.get(deal.name, [])}
	order_rows = {}
	for deal in deals:
		for order in orders_by_deal.get(deal.name, []):
			order_rows[order.name] = order
	for quote in quote_rows.values():
		for order in orders_by_quotation.get(quote.name, []):
			order_rows[order.name] = order
	return deals, list(quote_rows.values()), list(order_rows.values())


def _journey_row(lead, deals=None, quotations=None, orders=None, permissions=None):
	"""Build the drill-down from the same deduplicated entities used by the funnel."""
	permissions = permissions or {"deals": True, "quotations": True, "orders": True}
	deals, quotations, orders = deals or [], quotations or [], orders or []
	booked_orders = [order for order in orders if order.status in BOOKED_ORDER_STATUSES]
	stage = "Lead"
	if permissions["deals"] and deals:
		stage = "Deal"
	if permissions["quotations"] and quotations:
		stage = "Quotation Accepted" if any(q.status == "Accepted" for q in quotations) else "Quotation Sent" if any(q.status == "Sent" for q in quotations) else "Quotation"
	if permissions["orders"] and booked_orders:
		stage = "Order"
	primary = deals[0] if deals else None
	deal_rows = [{
		"name": deal.name, "label": deal.deal_title or deal.name,
		"won": bool(deal.won_on), "amount": flt(deal.amount, 2),
	} for deal in deals] if permissions["deals"] else None
	quotation_rows = [{
		"name": quotation.name, "deal": quotation.deal, "status": quotation.status,
		"grand_total": flt(quotation.grand_total, 2),
	} for quotation in quotations] if permissions["quotations"] else None
	order_rows = [{
		"name": order.name, "deal": order.deal, "quotation": getattr(order, "quotation", None),
		"status": order.status, "total": flt(order.total, 2),
		"link_type": "Quotation" if getattr(order, "quotation", None) else "Direct Deal",
	} for order in orders] if permissions["orders"] else None
	return {
		"name": lead.name, "lead_name": lead.lead_name or lead.name, "lead_owner": lead.lead_owner,
		"source": lead.source, "creation": lead.creation, "stage": stage,
		"has_deal": bool(deals) if permissions["deals"] else None,
		"deal": primary.name if primary else None, "deal_title": primary.deal_title if primary else None,
		"deal_count": len(deals) if permissions["deals"] else None,
		"deal_amount": flt(sum(flt(deal.amount, 2) for deal in deals), 2) if permissions["deals"] else None,
		"quotation_count": len(quotations) if permissions["quotations"] else None,
		"quotation_value": flt(sum(flt(q.grand_total, 2) for q in quotations), 2) if permissions["quotations"] else None,
		"order_count": len(booked_orders) if permissions["orders"] else None,
		"order_value": flt(sum(flt(order.total, 2) for order in booked_orders), 2) if permissions["orders"] else None,
		"won_deal_count": sum(bool(deal.won_on) for deal in deals) if permissions["deals"] else None,
		"deals": deal_rows, "quotations": quotation_rows, "orders": order_rows,
	}


def _summarize_journey(leads, deals_for_leads, quotations, orders_by_quotation, orders_by_deal, permissions):
	"""Every funnel count is a unique Lead from the creation cohort."""
	owner_groups = defaultdict(list)
	contexts = []
	for lead in leads:
		deals, quote_rows, order_rows = _journey_entities(lead, deals_for_leads, quotations, orders_by_quotation, orders_by_deal)
		context = (lead, deals, quote_rows, order_rows)
		contexts.append(context)
		owner_groups[lead.lead_owner or "__unassigned__"].append(context)

	def metrics(rows):
		lead_count = len(rows)
		deal_reached = sum(bool(deals) for _lead, deals, _quotes, _orders in rows) if permissions["deals"] else None
		quotation_reached = sum(bool(quotes) for _lead, _deals, quotes, _orders in rows) if permissions["quotations"] else None
		order_reached = sum(any(order.status in BOOKED_ORDER_STATUSES for order in orders) for _lead, _deals, _quotes, orders in rows) if permissions["orders"] else None
		unique_deals = {deal.name: deal for _lead, deals, _quotes, _orders in rows for deal in deals}
		won_leads = sum(any(deal.won_on for deal in deals) for _lead, deals, _quotes, _orders in rows) if permissions["deals"] else None
		unique_quotes = {quote.name: quote for _lead, _deals, quotes, _orders in rows for quote in quotes}
		unique_orders = {order.name: order for _lead, _deals, _quotes, orders in rows for order in orders if order.status in BOOKED_ORDER_STATUSES}
		deal_value = flt(sum(flt(deal.amount, 2) for deal in unique_deals.values()), 2) if permissions["deals"] else None
		quotation_value = flt(sum(flt(quote.grand_total, 2) for quote in unique_quotes.values()), 2) if permissions["quotations"] else None
		order_value = flt(sum(flt(order.total, 2) for order in unique_orders.values()), 2) if permissions["orders"] else None
		return {
			"lead_count": lead_count, "deal_count": deal_reached, "won_lead_count": won_leads,
			"quotation_count": quotation_reached, "order_count": order_reached,
			"lead_value": deal_value, "deal_value": deal_value, "quotation_value": quotation_value, "order_value": order_value,
			"entity_totals": {
				"leads": lead_count, "deals": len(unique_deals) if permissions["deals"] else None,
				"quotations": len(unique_quotes) if permissions["quotations"] else None,
				"booked_orders": len(unique_orders) if permissions["orders"] else None,
			},
		}

	summary = metrics(contexts)
	summary["lead_to_deal_rate"] = flt(summary["deal_count"] * 100 / summary["lead_count"], 2) if summary["deal_count"] is not None and summary["lead_count"] else (0.0 if summary["deal_count"] is not None else None)
	summary["lead_to_won_rate"] = flt(summary["won_lead_count"] * 100 / summary["lead_count"], 2) if summary["won_lead_count"] is not None and summary["lead_count"] else (0.0 if summary["won_lead_count"] is not None else None)
	summary["deal_to_order_rate"] = flt(summary["order_count"] * 100 / summary["deal_count"], 2) if summary["order_count"] is not None and summary["deal_count"] else (0.0 if summary["order_count"] is not None and summary["deal_count"] == 0 else None)
	summary["funnel"] = [
		{"stage": "Lead", "count": summary["lead_count"], "value": summary["lead_value"]},
		{"stage": "Deal", "count": summary["deal_count"], "value": summary["deal_value"]},
		{"stage": "Quotation", "count": summary["quotation_count"], "value": summary["quotation_value"]},
		{"stage": "Order", "count": summary["order_count"], "value": summary["order_value"]},
	]
	summary["by_owner"] = []
	for key, rows in owner_groups.items():
		values = metrics(rows)
		summary["by_owner"].append({"owner": None if key == "__unassigned__" else key, "label": _("Unassigned") if key == "__unassigned__" else key, **{name: values[name] for name in ("lead_count", "deal_count", "won_lead_count", "quotation_count", "order_count", "lead_value", "deal_value", "quotation_value", "order_value")}})
	summary["by_owner"].sort(key=lambda row: (-row["lead_count"], row["label"]))
	return summary, contexts


def _journey_comparison(current, previous):
	"""Build period-over-period comparison for journey metrics."""
	keys = ("lead_count", "deal_count", "won_lead_count", "quotation_count", "order_count", "lead_value", "deal_value", "quotation_value", "order_value", "lead_to_deal_rate", "lead_to_won_rate", "deal_to_order_rate")
	return {key: {
		"current": current.get(key),
		"previous": previous.get(key),
		"change": flt(current.get(key) - previous.get(key), 2) if current.get(key) is not None and previous.get(key) is not None else None,
	} for key in keys}


def _journey_period(start, end, salesperson, permissions, source=None):
	"""Lead-creation cohort, consistently owned and filtered by Lead Owner."""
	cohort_leads = _journey_leads(start, end)
	available_owners = {lead.lead_owner for lead in cohort_leads if lead.lead_owner}
	available_sources = {lead.source for lead in cohort_leads if lead.source}
	leads = [
		lead for lead in cohort_leads
		if (not salesperson or lead.lead_owner == salesperson) and (not source or lead.source == source)
	]
	deals_for_leads = _journey_deals_from_leads(leads) if leads and permissions["deals"] else {}
	deal_names = sorted({deal.name for deals in deals_for_leads.values() for deal in deals})
	quotations = _journey_quotations_for_deals(deal_names) if deal_names and permissions["quotations"] else {}
	quotation_names = sorted({quote.name for values in quotations.values() for quote in values})
	orders_by_quotation = _journey_orders_for_quotations(quotation_names) if quotation_names and permissions["orders"] else {}
	orders_by_deal = _journey_orders_for_deals(deal_names) if deal_names and permissions["orders"] else {}
	summary, contexts = _summarize_journey(leads, deals_for_leads, quotations, orders_by_quotation, orders_by_deal, permissions)
	journey_rows = [_journey_row(lead, deals, quote_rows, order_rows, permissions) for lead, deals, quote_rows, order_rows in contexts]
	return {
		"leads": leads,
		"deals": deals_for_leads,
		"quotations": quotations,
		"orders_by_deal": orders_by_deal,
		"available_owners": available_owners,
		"available_sources": available_sources,
		"summary": summary,
		"journey_rows": journey_rows,
	}


@frappe.whitelist()
def get_customer_journey(start_date, end_date, salesperson=None, source=None, compare_previous=0):
	"""Return Lead→Deal→Quotation→Order funnel with unique counts and conversion rates."""
	frappe.has_permission("DoubleT Lead", "read", throw=True)
	start, end = _validated_range(start_date, end_date)
	salesperson = (salesperson or "").strip() or None
	source = (source or "").strip() or None
	if salesperson and (len(salesperson) > 140 or not frappe.get_list("DoubleT Lead", filters={"lead_owner": salesperson}, pluck="name", limit_page_length=1)):
		frappe.throw(_("Salesperson must be a Lead Owner on a Lead you can access."), frappe.ValidationError)
	if source and (len(source) > 140 or not frappe.get_list("DoubleT Lead", filters={"source": source}, pluck="name", limit_page_length=1)):
		frappe.throw(_("Source must be present on a Lead you can access."), frappe.ValidationError)
	source_permissions = {
		"leads": True,
		"deals": bool(frappe.has_permission("DoubleT Deal", "read")),
		"quotations": bool(frappe.has_permission("DoubleT Quotation", "read")),
		"orders": bool(frappe.has_permission("DoubleT Order", "read")),
	}
	permissions = {
		"leads": True,
		"deals": source_permissions["deals"],
		"quotations": source_permissions["deals"] and source_permissions["quotations"],
		"orders": source_permissions["deals"] and source_permissions["orders"],
	}
	period = _journey_period(start, end, salesperson, permissions, source)
	owners = sorted(period["available_owners"])
	if salesperson and salesperson not in owners:
		owners.append(salesperson)
	owners.sort()
	comparison = None
	if cint(compare_previous):
		previous_start, previous_end = _previous_period(start, end)
		previous = _journey_period(previous_start, previous_end, salesperson, permissions, source)
		comparison = {
			"definition": _("Immediately preceding period with the same inclusive number of calendar days."),
			"start_date": str(previous_start), "end_date": str(previous_end),
			"metrics": _journey_comparison(period["summary"], previous["summary"]),
		}
	return {
		"filters": {"start_date": str(start), "end_date": str(end), "salesperson": salesperson, "source": source},
		"permissions": permissions,
		"source_permissions": source_permissions,
		"capabilities": {"team_filter": {"supported": False, "reason": _("Team filtering is unavailable because DoubleT Deal has no team field.")}},
		"currency": "USD",
		"business_definition": _(
			"Cohort is readable Leads created in the selected period and ownership always means Lead Owner. "
			"Each funnel stage counts unique cohort Leads reaching it; entity totals are shown separately. "
			"Lead-to-Deal and Lead-to-Won rates use all unique cohort Leads as their denominator; Won is the current linked Deal outcome, not a historical cohort event. "
			"Deals resolve source_lead and converted_deal; Orders resolve exact Quotation and Deal links without duplication. Order stage includes Confirmed/Completed Orders."
		),
		"salespeople": [{"value": owner, "label": owner} for owner in owners],
		"sources": [{"value": value, "label": value} for value in sorted(period.get("available_sources", set()))],
		**period["summary"],
		"journey_rows": period["journey_rows"],
		"comparison": comparison,
	}


# ===== Quotation & Order Report (REP-04) =====

QUOTATION_STATUSES = ("Draft", "Sent", "Accepted", "Rejected")
ORDER_STATUSES = ("Draft", "Confirmed", "Completed", "Cancelled")
BOOKED_ORDER_STATUSES = ("Confirmed", "Completed")


def _quotation_order_quotations(start, end):
	"""Quotations with quotation_date in range."""
	return frappe.get_list(
		"DoubleT Quotation", filters=[["quotation_date", ">=", start], ["quotation_date", "<=", end]],
		fields=["name", "deal", "status", "grand_total", "quotation_date", "creation"],
		order_by="quotation_date desc, name desc", limit_page_length=0,
	)


def _quotation_order_deals(deal_names):
	"""Deals for the given deal names to get owner info."""
	if not deal_names:
		return {}
	deals = frappe.get_list(
		"DoubleT Deal", filters={"name": ["in", deal_names]},
		fields=["name", "deal_title", "deal_owner"], limit_page_length=0,
	)
	return {d.name: d for d in deals}


def _quotation_order_orders(start, end):
	"""All readable Orders in the Order Date range, including standalone Orders."""
	return frappe.get_list(
		"DoubleT Order", filters=[["order_date", ">=", start], ["order_date", "<=", end]],
		fields=["name", "deal", "quotation", "status", "total", "order_date"],
		order_by="order_date desc, name desc", limit_page_length=0,
	)


def _quotation_order_conversion_orders(quotation_names):
	"""Orders for the quotation-date cohort; Order Date does not change conversion."""
	if not quotation_names:
		return []
	return frappe.get_list(
		"DoubleT Order", filters=[["quotation", "in", sorted(quotation_names)]],
		fields=["name", "deal", "quotation", "status", "total", "order_date"],
		order_by="order_date desc, name desc", limit_page_length=0,
	)


def _summarize_quotations(quotations, deals):
	"""Build quotation summary by status."""
	status_groups = defaultdict(lambda: {"count": 0, "value": 0.0, "quotations": []})
	for q in quotations:
		status = q.status or "Draft"
		status_groups[status]["count"] += 1
		status_groups[status]["value"] += flt(q.grand_total, 2)
		readable_deal = deals.get(q.deal) if q.deal else None
		status_groups[status]["quotations"].append({
			"name": q.name, "deal": readable_deal.name if readable_deal else None,
			"deal_restricted": bool(q.deal and not readable_deal),
			"deal_title": deals.get(q.deal).deal_title if q.deal and q.deal in deals else None,
			"status": status, "quotation_date": q.quotation_date,
			"grand_total": flt(q.grand_total, 2),
		})
	total_count = len(quotations)
	total_value = sum(flt(q.grand_total, 2) for q in quotations)
	accepted_count = status_groups.get("Accepted", {}).get("count", 0)
	acceptance_rate = flt(accepted_count * 100 / total_count, 2) if total_count else 0.0
	return {
		"quotation_count": total_count,
		"quotation_value": flt(total_value, 2),
		"accepted_count": accepted_count,
		"acceptance_rate": acceptance_rate,
		"by_status": sorted([
			{
				"status": status,
				"count": values["count"],
				"value": flt(values["value"], 2),
				"count_percentage": flt(values["count"] * 100 / total_count, 2) if total_count else 0.0,
				"value_percentage": flt(values["value"] * 100 / total_value, 2) if total_value else 0.0,
				"quotations": values["quotations"],
			}
			for status, values in status_groups.items()
		], key=lambda r: (-r["count"], -r["value"], r["status"])),
	}


def _summarize_orders(orders, deals):
	"""Build order summary by status, only counting booked sales from Confirmed/Completed."""
	status_groups = defaultdict(lambda: {"count": 0, "booked_value": 0.0, "total_value": 0.0, "orders": []})
	booked_orders = [o for o in orders if o.status in BOOKED_ORDER_STATUSES]
	for o in orders:
		status = o.status or "Draft"
		total_val = flt(o.total, 2)
		is_booked = o.status in BOOKED_ORDER_STATUSES
		status_groups[status]["count"] += 1
		status_groups[status]["total_value"] += total_val
		if is_booked:
			status_groups[status]["booked_value"] += total_val
		readable_deal = deals.get(o.deal) if o.deal else None
		status_groups[status]["orders"].append({
			"name": o.name, "deal": readable_deal.name if readable_deal else None,
			"deal_restricted": bool(o.deal and not readable_deal),
			"quotation": o.quotation,
			"deal_title": deals.get(o.deal).deal_title if o.deal and o.deal in deals else None,
			"status": status, "order_date": o.order_date,
			"total": total_val, "is_booked": is_booked,
		})
	total_booked = sum(flt(o.total, 2) for o in booked_orders)
	total_count = len(orders)
	return {
		"order_count": total_count,
		"booked_sales": flt(total_booked, 2),
		"total_order_value": flt(sum(flt(o.total, 2) for o in orders), 2),
		"booked_order_count": len(booked_orders),
		"by_status": sorted([
			{
				"status": status,
				"count": values["count"],
				"booked_value": flt(values["booked_value"], 2),
				"total_value": flt(values["total_value"], 2),
				"orders": values["orders"],
			}
			for status, values in status_groups.items()
		], key=lambda r: (-r["booked_value"], -r["count"], r["status"])),
	}


def _summarize_conversion(quotations, conversion_orders):
	"""Quotation-date cohort converted only by exact booked Order.quotation links."""
	booked_orders_by_quotation = defaultdict(list)
	for order in conversion_orders:
		if order.quotation and order.status in BOOKED_ORDER_STATUSES:
			booked_orders_by_quotation[order.quotation].append(order)
	booked_quotation_names = set(booked_orders_by_quotation)
	converted = [quotation for quotation in quotations if quotation.name in booked_quotation_names]
	accepted = [quotation for quotation in quotations if quotation.status == "Accepted"]
	accepted_converted = [quotation for quotation in accepted if quotation.name in booked_quotation_names]
	quotations_with_orders = len(converted)
	quotation_value_converted = sum(flt(quotation.grand_total, 2) for quotation in converted)
	quotation_count = len(quotations)
	conversion_rate = flt(quotations_with_orders * 100 / quotation_count, 2) if quotation_count else 0.0
	return {
		"quotations_with_orders": quotations_with_orders,
		"quotation_value_converted": flt(quotation_value_converted, 2),
		"quotation_to_order_rate": conversion_rate,
		"accepted_quotation_count": len(accepted),
		"accepted_quotations_with_orders": len(accepted_converted),
		"accepted_to_booked_order_rate": flt(len(accepted_converted) * 100 / len(accepted), 2) if accepted else 0.0,
		"accepted_conversion_drilldown": [{
			"name": quotation.name,
			"status": quotation.status,
			"quotation_date": quotation.quotation_date,
			"grand_total": flt(quotation.grand_total, 2),
			"converted": quotation.name in booked_quotation_names,
			"orders": [{
				"name": order.name, "status": order.status, "order_date": order.order_date,
				"total": flt(order.total, 2),
			} for order in booked_orders_by_quotation.get(quotation.name, [])],
		} for quotation in accepted],
	}


def _quotation_order_period(start, end, salesperson, permissions):
	"""Gather all quotation and order data for a period."""
	quotations = _quotation_order_quotations(start, end) if permissions["quotations"] else []
	orders = _quotation_order_orders(start, end) if permissions["orders"] else []
	deal_names = sorted({row.deal for row in quotations + orders if row.deal})
	deals = _quotation_order_deals(deal_names) if deal_names and permissions["deals"] else {}
	available_owners = {deal.deal_owner for deal in deals.values() if deal.deal_owner}
	if salesperson:
		quotations = [row for row in quotations if row.deal in deals and deals[row.deal].deal_owner == salesperson]
		orders = [row for row in orders if row.deal in deals and deals[row.deal].deal_owner == salesperson]
	quotation_summary = _summarize_quotations(quotations, deals) if permissions["quotations"] else None
	order_summary = _summarize_orders(orders, deals) if permissions["orders"] else None
	conversion_orders = _quotation_order_conversion_orders([q.name for q in quotations]) if permissions["quotations"] and permissions["orders"] else []
	conversion_summary = _summarize_conversion(quotations, conversion_orders) if permissions["quotations"] and permissions["orders"] else None
	return {
		"quotations": quotations,
		"orders": orders,
		"deals": deals,
		"available_owners": available_owners,
		"quotation_summary": quotation_summary,
		"order_summary": order_summary,
		"conversion": conversion_summary,
	}


def _qo_comparison(current, previous):
	"""Build period-over-period comparison for Quotation & Order metrics."""
	keys = (
		"quotation_count", "quotation_value", "accepted_count", "acceptance_rate",
		"order_count", "booked_sales", "booked_order_count",
		"quotations_with_orders", "quotation_to_order_rate", "quotation_value_converted",
		"accepted_quotation_count", "accepted_quotations_with_orders", "accepted_to_booked_order_rate",
	)
	return {key: {
		"current": current.get(key),
		"previous": previous.get(key),
		"change": flt(current.get(key) - previous.get(key), 2) if current.get(key) is not None and previous.get(key) is not None else None,
	} for key in keys}


@frappe.whitelist()
def get_quotation_order(start_date, end_date, salesperson=None, compare_previous=0):
	"""Return Quotation and Order metrics with status breakdown and conversion tracking."""
	start, end = _validated_range(start_date, end_date)
	permissions = {
		"quotations": bool(frappe.has_permission("DoubleT Quotation", "read")),
		"orders": bool(frappe.has_permission("DoubleT Order", "read")),
		"deals": bool(frappe.has_permission("DoubleT Deal", "read")),
	}
	if not permissions["quotations"] and not permissions["orders"]:
		frappe.throw(_("You do not have permission to view Quotations or Orders."), frappe.PermissionError)
	if salesperson and len(salesperson) > 140:
		frappe.throw(_("Salesperson is invalid."), frappe.ValidationError)
	if salesperson and not permissions["deals"]:
		frappe.throw(_("You do not have permission to filter by Deal Owner."), frappe.PermissionError)
	if salesperson:
		valid_deals = frappe.get_list("DoubleT Deal", filters={"deal_owner": salesperson}, pluck="name", limit_page_length=1)
		if not valid_deals:
			frappe.throw(_("Salesperson must be an owner on a Deal you can access."), frappe.ValidationError)
	period = _quotation_order_period(start, end, salesperson, permissions)
	owners = sorted(period["available_owners"])
	if salesperson and salesperson not in owners:
		owners.append(salesperson)
	owners.sort()
	comparison = None
	if cint(compare_previous):
		previous_start, previous_end = _previous_period(start, end)
		previous = _quotation_order_period(previous_start, previous_end, salesperson, permissions)
		current_metrics = {**(period["quotation_summary"] or {}), **(period["order_summary"] or {}), **(period["conversion"] or {})}
		previous_metrics = {**(previous["quotation_summary"] or {}), **(previous["order_summary"] or {}), **(previous["conversion"] or {})}
		comparison = {
			"definition": _("Immediately preceding period with the same inclusive number of calendar days."),
			"start_date": str(previous_start), "end_date": str(previous_end),
			"metrics": _qo_comparison(current_metrics, previous_metrics),
		}
	# Flatten drill-down data
	quotation_drilldown = []
	for status_row in (period["quotation_summary"] or {}).get("by_status", []):
		quotation_drilldown.extend(status_row["quotations"])
	order_drilldown = []
	for status_row in (period["order_summary"] or {}).get("by_status", []):
		order_drilldown.extend(status_row["orders"])
	return {
		"filters": {"start_date": str(start), "end_date": str(end), "salesperson": salesperson},
		"permissions": permissions,
		"capabilities": {"team_filter": {"supported": False, "reason": _("Team filtering is unavailable because DoubleT Deal has no team field.")}},
		"currency": "USD",
		"business_definition": _(
			"Quotation metrics use Quotation Date. Order metrics use Order Date. "
			"Booked Sales includes only Confirmed/Completed orders. "
			"Quotation-to-Order cohort is Quotations dated in the selected range; conversion requires an exact Confirmed/Completed Order.quotation link, regardless of Order Date. "
			"Accepted-to-Booked conversion uses unique Quotations whose current status is Accepted as the denominator and deduplicates exact linked booked Orders; it is current status, not a historical acceptance event. "
			"Deal Owner filtering excludes standalone records because they have no owner-bearing Deal."
		),
		"salespeople": [{"value": owner, "label": owner} for owner in owners],
		"quotation_summary": period["quotation_summary"],
		"order_summary": period["order_summary"],
		"conversion": period["conversion"],
		"quotation_drilldown": quotation_drilldown,
		"order_drilldown": order_drilldown,
		"comparison": comparison,
	}


def _activity_date_filters(fieldname, start, end):
	return [
		[fieldname, ">=", f"{start} 00:00:00"],
		[fieldname, "<", f"{add_days(end, 1)} 00:00:00"],
	]


def _activity_rows(doctype, date_field, fields, start, end, order_by, extra_filters=None):
	return frappe.get_list(
		doctype,
		filters=_activity_date_filters(date_field, start, end) + (extra_filters or []),
		fields=fields,
		order_by=order_by,
		limit_page_length=0,
	)


def _activity_source_permission(doctype):
	"""Check each report source independently; a restricted source must not zero-fill metrics."""
	return bool(frappe.has_permission(doctype, "read"))


CRM_EMAIL_REFERENCE_DOCTYPES = (
	"DoubleT Lead", "DoubleT Deal", "DoubleT Contact", "DoubleT Company",
	"DoubleT Quotation", "DoubleT Order",
)


def _activity_trend(start, end, sources):
	series = {}
	day = start
	while day <= end:
		series[str(day)] = {
			"date": str(day),
			"calls": 0 if sources["calls"]["available"] else None,
			"tasks": 0 if sources["tasks"]["available"] else None,
			"emails": 0 if sources["email"]["available"] else None,
			"zalo_messages": 0 if sources["zalo"]["messages_available"] else None,
		}
		day = getdate(add_days(day, 1))
	for key, date_field in (("calls", "start_time"), ("tasks", "creation"), ("email", "creation")):
		for row in sources[key]["rows"]:
			series[str(getdate(row.get(date_field)))][key if key != "email" else "emails"] += 1
	for row in sources["zalo"]["messages"]:
		series[str(getdate(row.sent_at))]["zalo_messages"] += 1
	return list(series.values())


@frappe.whitelist()
def get_activity_contact_center(start_date, end_date, employee=None, channel=None):
	"""Return permission-scoped activity metrics and the exact records behind them."""
	start, end = _validated_range(start_date, end_date)
	employee = (employee or "").strip() or None
	channel = (channel or "").strip().title() or None
	if employee and len(employee) > 140:
		frappe.throw(_("Employee is invalid."), frappe.ValidationError)
	if channel not in (None, "Call", "Task", "Email", "Zalo"):
		frappe.throw(_("Channel must be Call, Task, Email or Zalo."), frappe.ValidationError)

	permissions = {
		"calls": _activity_source_permission("DoubleT Call Log"),
		"tasks": _activity_source_permission("DoubleT Task"),
		"email": _activity_source_permission("Communication"),
		"zalo_conversations": _activity_source_permission("DoubleT Conversation"),
		"zalo_messages": _activity_source_permission("DoubleT Message"),
	}
	enabled = {
		"calls": channel in (None, "Call"), "tasks": channel in (None, "Task"),
		"email": channel in (None, "Email"), "zalo": channel in (None, "Zalo"),
	}

	call_rows = _activity_rows(
		"DoubleT Call Log", "start_time",
		["name", "agent", "assigned_to", "call_type", "duration", "status", "start_time", "from_number", "to_number"],
		start, end, "start_time desc, name desc",
	) if permissions["calls"] and enabled["calls"] else []
	task_rows = _activity_rows(
		"DoubleT Task", "creation",
		["name", "title", "status", "priority", "due_date", "assigned_to", "reference_doctype", "reference_docname", "creation"],
		start, end, "creation desc, name desc",
	) if permissions["tasks"] and enabled["tasks"] else []
	email_rows = _activity_rows(
		"Communication", "creation",
		["name", "subject", "sender", "recipients", "sent_or_received", "reference_doctype", "reference_name", "creation"],
		start, end, "creation desc, name desc",
		[["communication_medium", "=", "Email"], ["communication_type", "=", "Communication"], ["sent_or_received", "in", ["Sent", "Received"]], ["reference_doctype", "in", CRM_EMAIL_REFERENCE_DOCTYPES]],
	) if permissions["email"] and enabled["email"] else []

	conversation_rows = _activity_rows(
		"DoubleT Conversation", "creation",
		["name", "source", "oa_id", "external_user_id", "lead", "creation"],
		start, end, "creation desc, name desc",
	) if permissions["zalo_conversations"] and enabled["zalo"] else []
	message_rows = _activity_rows(
		"DoubleT Message", "sent_at",
		["name", "conversation", "source", "direction", "content", "sent_at", "is_simulated"],
		start, end, "sent_at desc, name desc",
	) if permissions["zalo_messages"] and enabled["zalo"] else []

	employee_values = {row.agent for row in call_rows if row.agent} | {row.assigned_to for row in task_rows if row.assigned_to}
	if employee:
		employee_values.add(employee)
	employees = sorted(employee_values)
	if employee:
		call_rows = [row for row in call_rows if row.agent == employee]
		task_rows = [row for row in task_rows if row.assigned_to == employee]

	pending_statuses = {"Backlog", "Todo", "In Progress"}
	pending_tasks = [row for row in task_rows if row.status in pending_statuses]
	as_of = now_datetime()
	overdue_tasks = [row for row in pending_tasks if row.due_date and get_datetime(row.due_date) < as_of]
	readable_conversations = set()
	if permissions["zalo_conversations"]:
		for conversation in {row.conversation for row in message_rows if row.conversation}:
			if frappe.has_permission("DoubleT Conversation", "read", doc=conversation):
				readable_conversations.add(conversation)
	for row in message_rows:
		if row.conversation not in readable_conversations:
			row.conversation = None

	sources = {
		"calls": {
			"available": permissions["calls"] and enabled["calls"], "permitted": permissions["calls"], "selected": enabled["calls"], "date_field": "start_time", "employee_filter_supported": True,
			"total": len(call_rows) if permissions["calls"] and enabled["calls"] else None,
			"missed": sum(row.status == "Missed" for row in call_rows) if permissions["calls"] and enabled["calls"] else None,
			"duration_seconds": sum(cint(row.duration) for row in call_rows) if permissions["calls"] and enabled["calls"] else None,
			"rows": call_rows,
		},
		"tasks": {
			"available": permissions["tasks"] and enabled["tasks"], "permitted": permissions["tasks"], "selected": enabled["tasks"], "date_field": "creation", "employee_filter_supported": True,
			"overdue_definition": _("Pending tasks created in the selected range whose Due Date is before the report run time."),
			"total": len(task_rows) if permissions["tasks"] and enabled["tasks"] else None,
			"completed": sum(row.status == "Done" for row in task_rows) if permissions["tasks"] and enabled["tasks"] else None,
			"pending": len(pending_tasks) if permissions["tasks"] and enabled["tasks"] else None,
			"overdue": len(overdue_tasks) if permissions["tasks"] and enabled["tasks"] else None,
			"rows": task_rows,
		},
		"email": {
			"available": permissions["email"] and enabled["email"], "permitted": permissions["email"], "selected": enabled["email"], "date_field": "creation", "employee_filter_supported": False,
			"unsupported_filter_reason": _("Employee filter is not applied: Communication has no verified employee field."),
			"incoming": sum(row.sent_or_received == "Received" for row in email_rows) if permissions["email"] and enabled["email"] else None,
			"outgoing": sum(row.sent_or_received == "Sent" for row in email_rows) if permissions["email"] and enabled["email"] else None,
			"rows": email_rows,
		},
		"zalo": {
			"available": enabled["zalo"] and (permissions["zalo_conversations"] or permissions["zalo_messages"]),
			"permitted": permissions["zalo_conversations"] or permissions["zalo_messages"], "selected": enabled["zalo"],
			"conversations_available": permissions["zalo_conversations"], "messages_available": permissions["zalo_messages"],
			"conversation_date_field": "creation", "message_date_field": "sent_at", "employee_filter_supported": False,
			"unsupported_filter_reason": _("Employee filter is not applied: Zalo conversations and messages have no employee field."),
			"conversations": conversation_rows,
			"conversation_count": len(conversation_rows) if permissions["zalo_conversations"] and enabled["zalo"] else None,
			"messages": message_rows,
			"message_count": len(message_rows) if permissions["zalo_messages"] and enabled["zalo"] else None,
			"simulated_message_count": sum(cint(row.is_simulated) for row in message_rows) if permissions["zalo_messages"] and enabled["zalo"] else None,
			"real_message_count": sum(not cint(row.is_simulated) for row in message_rows) if permissions["zalo_messages"] and enabled["zalo"] else None,
		},
	}
	return {
		"filters": {"start_date": str(start), "end_date": str(end), "employee": employee, "channel": channel},
		"permissions": permissions,
		"channel_options": [{"value": value, "label": value} for value in ("Call", "Task", "Email", "Zalo")],
		"employees": [{"value": value, "label": value} for value in employees],
		"source_definitions": _("Calls use Start Time; Tasks and Email use Creation; Zalo conversations use Creation and messages use Sent At. Employee applies only to Call Agent and Task Assignee; Email and Zalo have no verified employee attribution."),
		"as_of": str(as_of),
		"sources": sources,
		"trend": _activity_trend(start, end, sources),
	}
