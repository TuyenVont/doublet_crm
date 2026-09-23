"""Native Frappe dashboard records and Deal lifecycle number cards."""

import frappe
from frappe import _


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
