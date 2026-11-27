"""Native Frappe dashboard records and Deal lifecycle number cards."""

import frappe
from frappe import _
from frappe.utils import add_days, flt, now_datetime

from doublet_crm.smart_insights import build_smart_insights


DASHBOARD_NAME = "DoubleT CRM"
MODULE = "DoubleT CRM"

CARD_DEFINITIONS = (
	("Total Leads", {"type": "Document Type", "document_type": "DoubleT Lead", "function": "Count"}),
	("New Leads", {"type": "Document Type", "document_type": "DoubleT Lead", "function": "Count", "filters_json": frappe.as_json([["DoubleT Lead", "status", "=", "NEW"]])}),
	("Qualified Leads", {"type": "Document Type", "document_type": "DoubleT Lead", "function": "Count", "filters_json": frappe.as_json([["DoubleT Lead", "status", "=", "QUALIFIED"]])}),
	("Converted Leads", {"type": "Document Type", "document_type": "DoubleT Lead", "function": "Count", "filters_json": frappe.as_json([["DoubleT Lead", "status", "=", "CONVERTED"]])}),
	("Open Deals", {"type": "Custom", "document_type": "DoubleT Deal", "method": "doublet_crm.dashboard.get_open_deals"}),
	("Won Deals", {"type": "Custom", "document_type": "DoubleT Deal", "method": "doublet_crm.dashboard.get_won_deals"}),
	("Lost Deals", {"type": "Custom", "document_type": "DoubleT Deal", "method": "doublet_crm.dashboard.get_lost_deals"}),
	("Total Deal Amount", {"type": "Document Type", "document_type": "DoubleT Deal", "function": "Sum", "aggregate_function_based_on": "amount"}),
)

CHART_DEFINITIONS = (
	("Lead Status Distribution", {"chart_type": "Group By", "document_type": "DoubleT Lead", "group_by_based_on": "status", "group_by_type": "Count", "type": "Donut"}),
	("Deal Pipeline by Stage", {"chart_type": "Group By", "document_type": "DoubleT Deal", "group_by_based_on": "stage", "group_by_type": "Count", "type": "Bar"}),
	("Lead Source Distribution", {"chart_type": "Group By", "document_type": "DoubleT Lead", "group_by_based_on": "source", "group_by_type": "Count", "type": "Donut"}),
	("Monthly Deal Revenue", {"chart_type": "Sum", "document_type": "DoubleT Deal", "based_on": "won_on", "value_based_on": "amount", "timeseries": 1, "timespan": "Last Year", "time_interval": "Monthly", "type": "Bar"}),
)


def _sync_record(doctype, name, values):
	doc = frappe.db.exists(doctype, {"name": name})

	if doc:
		doc = frappe.get_doc(doctype, doc)
		doc.update(values)
		doc.save(ignore_permissions=True)
		return doc

	values["name"] = name
	values["doctype"] = doctype

	return frappe.get_doc(values).insert(ignore_permissions=True)

def sync_dashboard():
	"""Create or update the CRM dashboard without changing unrelated dashboards."""
	card_names = []
	for label, definition in CARD_DEFINITIONS:
		name = label
		_sync_record("Number Card", name, {
			"label": label,
			"module": MODULE,
			"is_public": 1,
			"show_percentage_stats": 0,
			"filters_json": "[]",
			**definition,
		})
		card_names.append(name)

	chart_names = []
	for label, definition in CHART_DEFINITIONS:
		name = label
		_sync_record("Dashboard Chart", name, {
			"chart_name": name,
			"module": MODULE,
			"is_public": 1,
			"filters_json": "[]",
			**definition,
		})
		chart_names.append(name)

	if frappe.db.exists("Dashboard", DASHBOARD_NAME):
		dashboard = frappe.get_doc("Dashboard", DASHBOARD_NAME)
		if dashboard.module != MODULE:
			frappe.throw(_("The DoubleT CRM dashboard name is already in use."), frappe.ValidationError)
	else:
		dashboard = frappe.get_doc({
			"doctype": "Dashboard",
			"dashboard_name": DASHBOARD_NAME,
			"module": MODULE,
			"is_default": 0,
		})

	if [row.card for row in dashboard.cards] != card_names or [row.chart for row in dashboard.charts] != chart_names:
		dashboard.set("cards", [])
		for name in card_names:
			dashboard.append("cards", {"card": name})
		dashboard.set("charts", [])
		for name in chart_names:
			dashboard.append("charts", {"chart": name, "width": "Half"})
		if dashboard.is_new():
			dashboard.insert(ignore_permissions=True)
		else:
			dashboard.save(ignore_permissions=True)
	return dashboard


def _deal_count(stage_type):
	frappe.has_permission("DoubleT Deal", "read", throw=True)
	stage_names = frappe.get_list("DoubleT Deal Stage", filters={"stage_type": stage_type}, pluck="name")
	if not stage_names:
		count = 0
	else:
		result = frappe.get_list(
			"DoubleT Deal",
			fields=["count(*) as count"],
			filters={"stage": ["in", stage_names]},
			order_by=None,
		)
		count = result[0].count if result else 0
	return {"value": count, "fieldtype": "Int", "route": ["List", "DoubleT Deal"]}


@frappe.whitelist()
def get_open_deals(filters=None):
	return _deal_count("OPEN")


@frappe.whitelist()
def get_won_deals(filters=None):
	return _deal_count("WON")


@frappe.whitelist()
def get_lost_deals(filters=None):
	return _deal_count("LOST")


def _can_read(doctype):
	return bool(frappe.has_permission(doctype, "read"))


def _readable_labels(doctype, names, fields, formatter):
	if not names or not _can_read(doctype):
		return {}
	rows = frappe.get_list(
		doctype,
		filters={"name": ["in", list(names)]},
		fields=["name", *fields],
		limit_page_length=0,
	)
	return {row.name: formatter(row) for row in rows}


@frappe.whitelist()
def get_overview():
	"""Return the permission-scoped data used by the custom CRM overview."""
	result = {"permissions": {}, "kpis": {}, "lead_sources": [], "deal_stages": [], "quotations": [], "upcoming_activities": [], "needs_attention": None}

	for doctype, key in (("DoubleT Lead", "leads"), ("DoubleT Deal", "deals"), ("DoubleT Quotation", "quotations"), ("DoubleT Deal Stage", "stages"), ("DoubleT Order", "orders"), ("DoubleT Appointment", "appointments"), ("DoubleT Task", "tasks")):
		result["permissions"][key] = _can_read(doctype)

	if result["permissions"]["leads"]:
		leads = frappe.get_list("DoubleT Lead", fields=["name", "source"], limit_page_length=0)
		result["kpis"]["leads"] = len(leads)
		counts = {}
		for row in leads:
			label = row.source or _("No source")
			counts[label] = counts.get(label, 0) + 1
		result["lead_sources"] = [{"label": label, "count": count} for label, count in counts.items()]
	else:
		result["kpis"]["leads"] = None

	if result["permissions"]["deals"] and result["permissions"]["stages"]:
		stages = frappe.get_list("DoubleT Deal Stage", filters={"enabled": 1}, fields=["name", "stage_name", "stage_type", "sort_order"], order_by="sort_order asc", limit_page_length=0)
		deals = frappe.get_list("DoubleT Deal", fields=["name", "stage"], limit_page_length=0)
		counts = {stage.name: 0 for stage in stages}
		for deal in deals:
			if deal.stage in counts:
				counts[deal.stage] += 1
		result["deal_stages"] = [{"name": stage.name, "label": stage.stage_name, "stage_type": stage.stage_type, "count": counts[stage.name]} for stage in stages]
		result["kpis"]["open_deals"] = sum(item["count"] for item in result["deal_stages"] if item["stage_type"] == "OPEN")
		result["kpis"]["won_deals"] = sum(item["count"] for item in result["deal_stages"] if item["stage_type"] == "WON")
	else:
		result["kpis"]["open_deals"] = None
		result["kpis"]["won_deals"] = None

	if result["permissions"]["quotations"]:
		filters = [["status", "in", ["Draft", "Sent"]]]
		rows = frappe.get_list("DoubleT Quotation", filters=filters, fields=["name", "contact", "company", "deal", "status", "valid_until"], order_by="modified desc", limit_page_length=0)
		today = frappe.utils.getdate()
		rows = [row for row in rows if row.status == "Draft" or (row.status == "Sent" and row.valid_until and frappe.utils.getdate(row.valid_until) >= today)]
		contact_labels = _readable_labels(
			"DoubleT Contact",
			{row.contact for row in rows if row.contact},
			["first_name", "last_name"],
			lambda row: " ".join(filter(None, [row.first_name, row.last_name])) or row.name,
		)
		company_labels = _readable_labels(
			"DoubleT Company",
			{row.company for row in rows if row.company},
			["company_name"],
			lambda row: row.company_name or row.name,
		)
		deal_labels = _readable_labels(
			"DoubleT Deal",
			{row.deal for row in rows if row.deal},
			["deal_title"],
			lambda row: row.deal_title or row.name,
		)
		result["kpis"]["draft_quotations"] = sum(row.status == "Draft" for row in rows)
		result["quotations"] = [
			{
				"name": row.name,
				"status": row.status,
				"display_status": "Expired" if row.status == "Draft" and row.valid_until and frappe.utils.getdate(row.valid_until) < today else row.status,
				"valid_until": row.valid_until,
				"customer_label": company_labels.get(row.company) if row.company else contact_labels.get(row.contact),
				"customer_restricted": bool((row.company or row.contact) and not (company_labels.get(row.company) if row.company else contact_labels.get(row.contact))),
				"deal": row.deal if row.deal in deal_labels else None,
				"deal_label": deal_labels.get(row.deal),
				"deal_restricted": bool(row.deal and row.deal not in deal_labels),
			}
			for row in rows[:10]
		]
	else:
		result["kpis"]["draft_quotations"] = None

	if result["permissions"]["orders"]:
		orders = frappe.get_list(
			"DoubleT Order", filters={"status": ["in", ["Confirmed", "Completed"]]},
			fields=["name", "total"], limit_page_length=0,
		)
		result["kpis"]["booked_orders"] = len(orders)
		result["kpis"]["booked_sales"] = flt(sum(flt(row.total) for row in orders), 2)
	else:
		result["kpis"]["booked_orders"] = None
		result["kpis"]["booked_sales"] = None

	now = now_datetime()
	if result["permissions"]["appointments"]:
		appointments = frappe.get_list(
			"DoubleT Appointment", filters={"status": "Scheduled", "starts_on": [">=", now]},
			fields=["name", "title", "starts_on", "assigned_to", "reference_doctype", "reference_docname"],
			order_by="starts_on asc", limit_page_length=10,
		)
		result["kpis"]["upcoming_appointments"] = frappe.get_list(
			"DoubleT Appointment", filters={"status": "Scheduled", "starts_on": ["between", [now, add_days(now, 7)]]},
			fields=["count(*) as total"], order_by=None, limit_page_length=1,
		)[0].total
		result["upcoming_activities"].extend({
			"type": "Appointment", "name": row.name, "title": row.title or row.name, "due_at": row.starts_on,
			"assigned_to": row.assigned_to, "related": row.reference_docname,
			"route": {"name": "AppointmentDetail", "params": {"appointmentId": row.name}},
		} for row in appointments)
	else:
		result["kpis"]["upcoming_appointments"] = None

	if result["permissions"]["tasks"]:
		tasks = frappe.get_list(
			"DoubleT Task", filters={"status": ["in", ["Backlog", "Todo", "In Progress"]], "due_date": [">=", now]},
			fields=["name", "title", "due_date", "assigned_to", "reference_docname"],
			order_by="due_date asc", limit_page_length=10,
		)
		result["upcoming_activities"].extend({
			"type": "Task", "name": row.name, "title": row.title or row.name, "due_at": row.due_date,
			"assigned_to": row.assigned_to, "related": row.reference_docname,
			"route": {"name": "Tasks", "query": {"task": row.name}},
		} for row in tasks)
	result["upcoming_activities"] = sorted(result["upcoming_activities"], key=lambda row: (row["due_at"], row["name"]))[:10]

	try:
		insights = build_smart_insights(limit=25)
		grouped = {}
		for alert in insights["alerts"]:
			deal_key = alert["source_id"] if alert["source_doctype"] == "DoubleT Deal" else alert.get("linked_deal")
			key = ("deal", deal_key) if deal_key else (alert["source_doctype"], alert["source_id"], alert["type"])
			if key not in grouped:
				grouped[key] = {**alert, "alert_count": 1, "reasons": [alert["reason"]]}
			else:
				grouped[key]["alert_count"] += 1
				grouped[key]["reasons"].append(alert["reason"])
				if alert["severity"] == "critical":
					grouped[key]["severity"] = "critical"
		result["permissions"]["insights"] = True
		result["kpis"]["critical_alerts"] = insights["summary"]["critical"]
		result["needs_attention"] = {
			"as_of_date": insights["as_of_date"], "semantics": insights["semantics"],
			"summary": insights["summary"], "alerts": list(grouped.values())[:6],
		}
	except Exception:
		try:
			frappe.log_error(title="Dashboard Smart Insights failed")
		except Exception:
			pass
		result["permissions"]["insights"] = False
		result["kpis"]["critical_alerts"] = None
		result["insights_error"] = True

	return result
