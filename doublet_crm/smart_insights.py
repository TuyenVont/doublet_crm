"""Permission-scoped current alerts and deterministic Deal health scores."""

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, get_datetime, getdate, nowdate

from doublet_crm.doublet_crm.doctype.doublet_task.doublet_task import ALLOWED_REFERENCES
from doublet_crm.stage_aging import readable_stage_evidence_fields, stage_aging_for_deals


ALERT_THRESHOLDS = {
	"deal_unchanged_days": 7,
	"quotation_expiry_days": 3,
	"stage_aging_days": 30,
}
HEALTH_FACTORS = {
	"update_recency": 25,
	"expected_close": 25,
	"overdue_tasks": 25,
	"quotation": 25,
}
HEALTH_CATEGORIES = ((70, "Healthy"), (40, "Needs Attention"), (0, "At Risk"))
MIN_HEALTH_COVERAGE_WEIGHT = 75
OPEN_TASK_STATUSES = ("Backlog", "Todo", "In Progress")
SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


def _as_of(value=None):
	try:
		day = getdate(value or nowdate())
	except (TypeError, ValueError):
		frappe.throw(_("As-of Date must be a valid date."), frappe.ValidationError)
	if day > getdate(nowdate()):
		frappe.throw(_("As-of Date cannot be in the future."), frappe.ValidationError)
	return day


def _days_since(value, as_of):
	return (as_of - getdate(value)).days if value else None


def _days_until(value, as_of):
	return (getdate(value) - as_of).days if value else None


def _route(doctype, name):
	routes = {
		"DoubleT Deal": ("DealDetail", "dealId"),
		"DoubleT Quotation": ("QuotationDetail", "quotationId"),
		"DoubleT Task": ("Tasks", None),
	}
	route_name, param = routes[doctype]
	return {"name": route_name, "params": {param: name} if param else {}, "query": {} if param else {"task": name}}


def _stage_map(deals):
	if not frappe.has_permission("DoubleT Deal Stage", "read"):
		return {}
	names = sorted({row.stage for row in deals if row.stage})
	if not names:
		return {}
	rows = frappe.get_list(
		"DoubleT Deal Stage", filters={"name": ["in", names]},
		fields=["name", "stage_name", "stage_type"], limit_page_length=0,
	)
	return {row.name: row for row in rows}


def _is_open(deal, stages):
	if deal.won_on or deal.lost_on:
		return False
	stage = stages.get(deal.stage)
	return not stage or (stage.stage_type or "OPEN").upper() == "OPEN"


def _health_score(deal, tasks, quotations, as_of, permissions, interactions=None):
	factors = []

	interactions = interactions or []
	latest_interaction = max((get_datetime(value) for value in interactions if value), default=None)
	recency_value = latest_interaction or deal.modified
	unchanged_days = _days_since(recency_value, as_of)
	if unchanged_days is None:
		factors.append({"key": "update_recency", "label": _("Interaction / update recency"), "weight": 25, "points": None, "status": "Unknown", "reason": _("No readable interaction timestamp or Modified date is available.")})
	else:
		points = 25 if unchanged_days < 7 else 15 if unchanged_days < 14 else 0
		reason = _("Latest readable linked Call/Email interaction was {0} day(s) ago.").format(unchanged_days) if latest_interaction else _("No readable linked interaction was found; CRM update recency is {0} day(s) and is not claimed as customer interaction.").format(unchanged_days)
		factors.append({"key": "update_recency", "label": _("Interaction / update recency"), "weight": 25, "points": points, "status": "Known", "reason": reason})

	if not deal.expected_close_date:
		factors.append({"key": "expected_close", "label": _("Expected close"), "weight": 25, "points": None, "status": "Unknown", "reason": _("Expected Close Date is missing.")})
	else:
		days = _days_until(deal.expected_close_date, as_of)
		points = 0 if days < 0 else 15 if days <= 7 else 25
		factors.append({"key": "expected_close", "label": _("Expected close"), "weight": 25, "points": points, "status": "Known", "reason": _("Expected Close Date is {0} day(s) from the as-of date.").format(days)})

	if not permissions["tasks"]:
		factors.append({"key": "overdue_tasks", "label": _("Overdue tasks"), "weight": 25, "points": None, "status": "Unknown", "reason": _("Task data is unavailable with your permissions.")})
	else:
		overdue = [task for task in tasks if task.status in OPEN_TASK_STATUSES and task.due_date and getdate(task.due_date) < as_of]
		if overdue:
			factors.append({"key": "overdue_tasks", "label": _("Overdue tasks"), "weight": 25, "points": 0, "status": "Known", "reason": _("{0} readable unfinished linked Task(s) are past due.").format(len(overdue)), "sources": [{"id": task.name, "route": _route("DoubleT Task", task.name)} for task in overdue]})
		else:
			factors.append({"key": "overdue_tasks", "label": _("Overdue tasks"), "weight": 25, "points": None, "status": "Unknown", "reason": _("No overdue Task was found among readable linked Tasks; restricted Tasks, if any, remain unknown.")})

	if not permissions["quotations"]:
		factors.append({"key": "quotation", "label": _("Linked quotation"), "weight": 25, "points": None, "status": "Unknown", "reason": _("Quotation data is unavailable with your permissions.")})
	elif not quotations:
		factors.append({"key": "quotation", "label": _("Linked quotation"), "weight": 25, "points": None, "status": "Unknown", "reason": _("No readable linked Quotation supplies evidence.")})
	else:
		accepted = [row for row in quotations if row.status == "Accepted"]
		sent = [row for row in quotations if row.status == "Sent"]
		if accepted:
			points, reason = 25, _("At least one linked Quotation is currently Accepted.")
		elif sent:
			best_days = max((_days_until(row.valid_until, as_of) for row in sent if row.valid_until), default=None)
			points = None if best_days is None else 0 if best_days < 0 else 10 if best_days <= 3 else 20
			reason = _("Sent Quotation validity is unavailable.") if best_days is None else _("Best readable Sent Quotation is valid for {0} more day(s).").format(best_days)
		else:
			points, reason = 5, _("Readable linked Quotations are neither Sent nor Accepted.")
		factors.append({"key": "quotation", "label": _("Linked quotation"), "weight": 25, "points": points, "status": "Known" if points is not None else "Unknown", "reason": reason, "sources": [{"id": row.name, "route": _route("DoubleT Quotation", row.name)} for row in quotations]})

	known = [factor for factor in factors if factor["points"] is not None]
	known_weight = sum(factor["weight"] for factor in known)
	score = round(sum(factor["points"] for factor in known) * 100 / known_weight) if known_weight else None
	coverage_sufficient = known_weight >= MIN_HEALTH_COVERAGE_WEIGHT
	category = "Unknown" if score is None else "Insufficient Evidence" if not coverage_sufficient else next(label for threshold, label in HEALTH_CATEGORIES if score >= threshold)
	return {
		"score": score, "category": category,
		"coverage": {"known_weight": known_weight, "total_weight": sum(HEALTH_FACTORS.values()), "known_factors": len(known), "total_factors": len(factors), "sufficient": coverage_sufficient, "minimum_weight": MIN_HEALTH_COVERAGE_WEIGHT},
		"factors": factors,
		"definition": _("Deterministic 0–100 score normalized over known factors only. It is not a Won probability; missing or restricted evidence stays Unknown."),
	}


def build_smart_insights(as_of_date=None, salesperson=None, alert_type=None, severity=None, limit=100):
	"""Build current alerts and Deal health using only permission-filtered source lists."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required."), frappe.PermissionError)
	as_of = _as_of(as_of_date)
	salesperson = (salesperson or "").strip() or None
	alert_type = (alert_type or "").strip() or None
	severity = (severity or "").strip().lower() or None
	allowed_types = {"stale_deal", "past_expected_close", "quotation_expiry", "overdue_task", "prolonged_stage"}
	if alert_type and alert_type not in allowed_types:
		frappe.throw(_("Alert Type is invalid."), frappe.ValidationError)
	if severity and severity not in {"critical", "warning"}:
		frappe.throw(_("Severity is invalid."), frappe.ValidationError)
	bounded_limit = None if limit is None else max(1, min(cint(limit) or 100, 500))
	permissions = {
		"deals": bool(frappe.has_permission("DoubleT Deal", "read")),
		"quotations": bool(frappe.has_permission("DoubleT Quotation", "read")),
		"tasks": bool(frappe.has_permission("DoubleT Task", "read")),
		"calls": bool(frappe.has_permission("DoubleT Call Log", "read")),
		"email": bool(frappe.has_permission("Communication", "read")),
	}
	can_create_follow_up = bool(frappe.has_permission("DoubleT Task", "create"))
	if not any(permissions.values()):
		frappe.throw(_("You do not have permission to view Smart Insights sources."), frappe.PermissionError)

	deal_fields = ["name", "deal_title", "deal_owner", "amount", "stage", "creation", "modified", "expected_close_date", "won_on", "lost_on"]
	deal_fields.extend(field for field in readable_stage_evidence_fields() if field not in deal_fields)
	deals = frappe.get_list(
		"DoubleT Deal", fields=deal_fields,
		order_by="modified asc, name asc", limit_page_length=0,
	) if permissions["deals"] else []
	stages = _stage_map(deals)
	open_deals = [row for row in deals if _is_open(row, stages)]
	owners = sorted({row.deal_owner for row in open_deals if row.deal_owner})
	if salesperson:
		if len(salesperson) > 140 or salesperson not in owners:
			frappe.throw(_("Salesperson must own a Deal you can access."), frappe.ValidationError)
		open_deals = [row for row in open_deals if row.deal_owner == salesperson]
	stage_aging = stage_aging_for_deals(open_deals, stages, as_of)
	permissions["stage_history"] = bool(stage_aging.get("history_available"))
	deal_names = [row.name for row in open_deals]

	quotation_filters = {"deal": ["in", deal_names]} if salesperson else None
	quotations = frappe.get_list(
		"DoubleT Quotation", filters=quotation_filters,
		fields=["name", "deal", "status", "valid_until", "grand_total", "modified"],
		order_by="modified desc, name desc", limit_page_length=0,
	) if permissions["quotations"] and (deal_names or not salesperson) else []
	tasks = frappe.get_list(
		"DoubleT Task", filters={"reference_doctype": "DoubleT Deal", "reference_docname": ["in", deal_names]},
		fields=["name", "title", "status", "priority", "due_date", "assigned_to", "reference_doctype", "reference_docname"],
		order_by="due_date asc, name asc", limit_page_length=0,
	) if permissions["tasks"] and deal_names else []
	standalone_tasks = frappe.get_list(
		"DoubleT Task", filters={"status": ["in", OPEN_TASK_STATUSES]},
		fields=["name", "title", "status", "priority", "due_date", "assigned_to", "reference_doctype", "reference_docname"],
		order_by="due_date asc, name asc", limit_page_length=0,
	) if permissions["tasks"] and not salesperson else []
	call_rows = frappe.get_list(
		"DoubleT Call Log", filters={"reference_doctype": "DoubleT Deal", "reference_name": ["in", deal_names]},
		fields=["name", "reference_name", "start_time"], order_by="start_time desc", limit_page_length=0,
	) if permissions["calls"] and deal_names else []
	email_rows = frappe.get_list(
		"Communication", filters={"reference_doctype": "DoubleT Deal", "reference_name": ["in", deal_names], "communication_medium": "Email"},
		fields=["name", "reference_name", "creation"], order_by="creation desc", limit_page_length=0,
	) if permissions["email"] and deal_names else []

	deal_by_name = {row.name: row for row in deals}
	quotations_by_deal = defaultdict(list)
	for row in quotations:
		if row.deal in deal_by_name:
			quotations_by_deal[row.deal].append(row)
	tasks_by_deal = defaultdict(list)
	for row in tasks:
		tasks_by_deal[row.reference_docname].append(row)
	interactions_by_deal = defaultdict(list)
	for row in call_rows:
		interactions_by_deal[row.reference_name].append(row.start_time)
	for row in email_rows:
		interactions_by_deal[row.reference_name].append(row.creation)

	alerts = []
	for deal in open_deals:
		unchanged = _days_since(deal.modified, as_of)
		if unchanged is not None and unchanged >= ALERT_THRESHOLDS["deal_unchanged_days"]:
			alerts.append({"type": "stale_deal", "severity": "warning" if unchanged < 14 else "critical", "reason": _("Open Deal has not been updated for {0} day(s).").format(unchanged), "relevant_date": deal.modified, "days": unchanged, "owner": deal.deal_owner, "source_doctype": "DoubleT Deal", "source_id": deal.name, "source_label": deal.deal_title or deal.name, "route": _route("DoubleT Deal", deal.name)})
		if deal.expected_close_date and getdate(deal.expected_close_date) < as_of:
			days = _days_since(deal.expected_close_date, as_of)
			alerts.append({"type": "past_expected_close", "severity": "critical", "reason": _("Open Deal is {0} day(s) past Expected Close Date.").format(days), "relevant_date": deal.expected_close_date, "days": days, "owner": deal.deal_owner, "source_doctype": "DoubleT Deal", "source_id": deal.name, "source_label": deal.deal_title or deal.name, "route": _route("DoubleT Deal", deal.name)})
	for aging in stage_aging.get("rows") or []:
		if aging["days_in_stage"] is None or aging["days_in_stage"] < ALERT_THRESHOLDS["stage_aging_days"]:
			continue
		alerts.append({
			"type": "prolonged_stage", "severity": "critical" if aging["days_in_stage"] >= ALERT_THRESHOLDS["stage_aging_days"] * 2 else "warning",
			"reason": _("Open Deal has remained in {0} for {1} day(s).").format(aging["stage_label"], aging["days_in_stage"]),
			"relevant_date": aging["stage_entry_date"], "days": aging["days_in_stage"], "owner": aging["deal_owner"],
			"source_doctype": "DoubleT Deal", "source_id": aging["name"], "source_label": aging["deal_title"] or aging["name"],
			"stage": aging["stage"], "stage_label": aging["stage_label"], "route": _route("DoubleT Deal", aging["name"]),
			"stage_entry_actor": aging.get("stage_entry_actor"), "evidence_source": aging.get("evidence_source"),
		})
	for quotation in quotations:
		if quotation.status != "Sent" or not quotation.valid_until:
			continue
		days = _days_until(quotation.valid_until, as_of)
		if days <= ALERT_THRESHOLDS["quotation_expiry_days"]:
			deal = deal_by_name.get(quotation.deal)
			alerts.append({"type": "quotation_expiry", "severity": "critical" if days < 0 else "warning", "reason": _("Sent Quotation expired {0} day(s) ago.").format(abs(days)) if days < 0 else _("Sent Quotation expires in {0} day(s).").format(days), "relevant_date": quotation.valid_until, "days": days, "owner": deal.deal_owner if deal else None, "source_doctype": "DoubleT Quotation", "source_id": quotation.name, "source_label": quotation.name, "linked_deal": quotation.deal if quotation.deal in deal_by_name else None, "route": _route("DoubleT Quotation", quotation.name)})
	seen_tasks = {row.name: row for row in tasks + standalone_tasks}
	for task in seen_tasks.values():
		if task.status in OPEN_TASK_STATUSES and task.due_date and getdate(task.due_date) < as_of:
			days = _days_since(task.due_date, as_of)
			alerts.append({"type": "overdue_task", "severity": "critical" if days >= 7 else "warning", "reason": _("Unfinished Task is {0} day(s) past due.").format(days), "relevant_date": task.due_date, "days": days, "owner": task.assigned_to, "source_doctype": "DoubleT Task", "source_id": task.name, "source_label": task.title or task.name, "reference_doctype": task.reference_doctype, "reference_docname": task.reference_docname, "route": _route("DoubleT Task", task.name)})

	if alert_type:
		alerts = [row for row in alerts if row["type"] == alert_type]
	if severity:
		alerts = [row for row in alerts if row["severity"] == severity]
	for alert in alerts:
		reference_doctype = reference_docname = None
		if alert["source_doctype"] == "DoubleT Deal":
			reference_doctype, reference_docname = "DoubleT Deal", alert["source_id"]
		elif alert["source_doctype"] == "DoubleT Quotation" and alert.get("linked_deal"):
			reference_doctype, reference_docname = "DoubleT Deal", alert["linked_deal"]
		elif alert["source_doctype"] == "DoubleT Task" and alert.get("reference_doctype") in ALLOWED_REFERENCES and alert.get("reference_docname"):
			if frappe.has_permission(alert["reference_doctype"], "read", alert["reference_docname"]):
				reference_doctype, reference_docname = alert["reference_doctype"], alert["reference_docname"]
		available = bool(can_create_follow_up and reference_doctype and reference_docname)
		alert["follow_up"] = {
			"available": available, "reference_doctype": reference_doctype, "reference_docname": reference_docname,
			"reason": None if available else _("Task creation permission or a readable supported reference is unavailable."),
		}
	alerts.sort(key=lambda row: (SEVERITY_ORDER[row["severity"]], -abs(row["days"]), row["source_id"]))
	health = [{
		"deal": deal.name, "deal_title": deal.deal_title or deal.name, "owner": deal.deal_owner,
		"amount": flt(deal.amount, 2), "route": _route("DoubleT Deal", deal.name),
		**_health_score(deal, tasks_by_deal[deal.name], quotations_by_deal[deal.name], as_of, permissions, interactions_by_deal[deal.name]),
	} for deal in open_deals]
	health.sort(key=lambda row: (row["score"] is None, row["score"] if row["score"] is not None else 101, row["deal"]))
	return {
		"as_of_date": str(as_of), "semantics": _("Current readable records evaluated as of the stated date; this is not a historical snapshot or period aggregate."),
		"thresholds": ALERT_THRESHOLDS, "health_weights": HEALTH_FACTORS, "permissions": permissions,
		"capabilities": {
			"follow_up_task": {"available": can_create_follow_up, "reason": None if can_create_follow_up else _("You do not have permission to create DoubleT Tasks.")},
			"stage_aging": {
				"available": bool(stage_aging.get("history_available")),
				"unknown_count": sum(row.get("days_in_stage") is None for row in stage_aging.get("rows") or []),
				"reason": stage_aging.get("reason") if not stage_aging.get("history_available") else None,
			},
		},
		"filters": {"salesperson": salesperson, "alert_type": alert_type, "severity": severity},
		"salespeople": [{"value": owner, "label": owner} for owner in owners],
		"alerts": alerts if bounded_limit is None else alerts[:bounded_limit], "alert_total": len(alerts), "health": health,
		"summary": {
			"total": len(alerts), "critical": sum(row["severity"] == "critical" for row in alerts),
			"warning": sum(row["severity"] == "warning" for row in alerts),
			"needs_attention": sum(row["category"] in ("Needs Attention", "At Risk") for row in health),
		},
	}


@frappe.whitelist()
def get_smart_insights(as_of_date=None, salesperson=None, alert_type=None, severity=None, limit=100):
	return build_smart_insights(as_of_date, salesperson, alert_type, severity, limit)


def _task_reference(alert):
	if alert["source_doctype"] == "DoubleT Deal":
		return "DoubleT Deal", alert["source_id"]
	if alert["source_doctype"] == "DoubleT Quotation":
		rows = frappe.get_list("DoubleT Quotation", filters={"name": alert["source_id"]}, fields=["deal"], limit_page_length=1)
		if rows and rows[0].deal and frappe.has_permission("DoubleT Deal", "read", rows[0].deal):
			return "DoubleT Deal", rows[0].deal
	if alert["source_doctype"] == "DoubleT Task":
		rows = frappe.get_list("DoubleT Task", filters={"name": alert["source_id"]}, fields=["reference_doctype", "reference_docname"], limit_page_length=1)
		if rows and rows[0].reference_doctype in ALLOWED_REFERENCES and rows[0].reference_docname and frappe.has_permission(rows[0].reference_doctype, "read", rows[0].reference_docname):
			return rows[0].reference_doctype, rows[0].reference_docname
	return None, None


def _transaction_lock(name):
	lock = frappe.cache.lock(name, timeout=120, blocking_timeout=10)
	if not lock.acquire(blocking=True):
		frappe.throw(_("Another follow-up request is already in progress. Please retry."), frappe.ValidationError)
	state = {"released": False}

	def release():
		if state["released"]:
			return
		state["released"] = True
		try:
			lock.release()
		except Exception:
			frappe.log_error(title="Smart Insights lock release failed")

	frappe.db.after_commit.add(release)
	frappe.db.after_rollback.add(release)
	return release


@frappe.whitelist(methods=["POST"])
def create_follow_up_task(alert_type, source_id, title=None, due_date=None, assigned_to=None):
	"""Explicitly create one active follow-up Task for a currently authorized alert."""
	frappe.has_permission("DoubleT Task", "create", throw=True)
	insights = build_smart_insights(alert_type=alert_type, limit=None)
	alert = next((row for row in insights["alerts"] if row["type"] == alert_type and row["source_id"] == source_id), None)
	if not alert:
		frappe.throw(_("Alert is unavailable, resolved, or not permitted."), frappe.PermissionError)
	assigned_to = (assigned_to or frappe.session.user or "").strip() or None
	if assigned_to:
		allowed = frappe.get_list("User", filters={"name": assigned_to, "enabled": 1}, pluck="name", limit_page_length=1)
		if not allowed:
			frappe.throw(_("Assignee must be an active User you can access."), frappe.ValidationError)
	reference_doctype, reference_docname = _task_reference(alert)
	if not reference_doctype or not reference_docname or reference_doctype not in ALLOWED_REFERENCES:
		frappe.throw(_("A readable supported reference is required for a follow-up Task."), frappe.PermissionError)
	frappe.has_permission(reference_doctype, "read", reference_docname, throw=True)
	marker = f"[Smart Insight:{alert['source_doctype']}:{alert['source_id']}]"
	lock_name = f"doublet_crm:smart_insight_task:{alert['source_doctype']}:{alert['source_id']}"
	release_lock = _transaction_lock(lock_name)
	try:
		existing_name = frappe.db.get_value(
			"DoubleT Task", {"description": ["like", f"%{marker}%"], "status": ["in", OPEN_TASK_STATUSES]}, "name",
		)
		if existing_name:
			release_lock()
			return {"created": False, "duplicate": True, "task": existing_name if frappe.has_permission("DoubleT Task", "read", existing_name) else None}
		doc = frappe.get_doc({
			"doctype": "DoubleT Task", "title": (title or _("Follow up: {0}").format(alert["source_label"]))[:140],
			"description": f"{marker}\n{alert['reason']}", "status": "Todo", "priority": "High" if alert["severity"] == "critical" else "Medium",
			"due_date": due_date or str(add_days(getdate(nowdate()), 1)), "assigned_to": assigned_to,
			"reference_doctype": reference_doctype, "reference_docname": reference_docname,
		})
		doc.insert()
	except Exception:
		release_lock()
		raise
	return {"created": True, "duplicate": False, "task": doc.name}
