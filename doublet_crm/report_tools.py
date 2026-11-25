"""Safe CSV export and personal saved filters for live CRM reports."""

import csv
import io
import json
import re

import frappe
from frappe import _
from frappe.model.utils.user_settings import get_user_settings, update_user_settings
from frappe.utils import cint, now_datetime

from doublet_crm import reports
from doublet_crm.smart_insights import build_smart_insights


REPORTS = {
	"sales-performance": {
		"label": "Sales Performance", "sources": ("DoubleT Order", "DoubleT Deal"), "method": reports.get_sales_performance,
		"filters": {"start_date", "end_date", "salesperson", "compare_previous"},
	},
	"pipeline-analytics": {
		"label": "Pipeline Analytics", "sources": ("DoubleT Deal", "DoubleT Deal Stage"), "method": reports.get_pipeline_analytics,
		"filters": {"start_date", "end_date", "salesperson", "compare_previous"},
	},
	"customer-journey": {
		"label": "Customer Journey", "sources": ("DoubleT Lead", "DoubleT Deal", "DoubleT Quotation", "DoubleT Order"), "method": reports.get_customer_journey,
		"filters": {"start_date", "end_date", "salesperson", "source", "compare_previous"},
	},
	"quotation-order": {
		"label": "Quotation & Order", "sources": ("DoubleT Quotation", "DoubleT Order", "DoubleT Deal"), "method": reports.get_quotation_order,
		"filters": {"start_date", "end_date", "salesperson", "compare_previous"},
	},
	"activity-contact-center": {
		"label": "Activity & Contact Center", "sources": ("DoubleT Call Log", "DoubleT Task", "Communication", "DoubleT Conversation", "DoubleT Message"), "method": reports.get_activity_contact_center,
		"filters": {"start_date", "end_date", "employee", "channel"},
	},
	"smart-insights": {
		"label": "Smart Insights", "sources": ("DoubleT Deal", "DoubleT Quotation", "DoubleT Task", "DoubleT Call Log", "Communication"), "method": build_smart_insights,
		"filters": {"as_of_date", "salesperson", "alert_type"},
	},
}
USER_SETTINGS_DOCTYPE = "DoubleT CRM Reports"
MAX_SAVED_FILTERS = 25
FIELD_ALIASES = {
	"DoubleT Deal": {"label": "deal_title", "source_label": "deal_title", "owner": "deal_owner"},
	"DoubleT Task": {"source_label": "title", "owner": "assigned_to"},
}


def _report(report):
	value = (report or "").strip()
	if value not in REPORTS:
		frappe.throw(_("Report is invalid."), frappe.ValidationError)
	return value, REPORTS[value]


def _filters(report, value):
	if isinstance(value, str):
		try:
			value = json.loads(value or "{}")
		except (TypeError, ValueError):
			frappe.throw(_("Filters must be valid JSON."), frappe.ValidationError)
	if not isinstance(value, dict):
		frappe.throw(_("Filters must be an object."), frappe.ValidationError)
	unknown = set(value) - REPORTS[report]["filters"]
	if unknown:
		frappe.throw(_("Unsupported report filter: {0}").format(", ".join(sorted(unknown))), frappe.ValidationError)
	clean = {}
	for key, item in value.items():
		if item in (None, "", False):
			continue
		if key == "compare_previous":
			clean[key] = cint(item)
		elif isinstance(item, (str, int, float)) and len(str(item)) <= 140:
			clean[key] = item
		else:
			frappe.throw(_("Filter value is invalid."), frappe.ValidationError)
	return clean


def _dict(value):
	return dict(value) if isinstance(value, dict) else {"value": value}


def _source_permissions(config):
	return {doctype: bool(frappe.has_permission(doctype, "read") and frappe.has_permission(doctype, "export")) for doctype in config["sources"]}


def _permitted_fields(doctype):
	from frappe.model import get_permitted_fields
	meta = frappe.get_meta(doctype)
	return set(get_permitted_fields(doctype, permission_type="read")) | {"name"}, {field.fieldname for field in meta.fields}


def _export_rows(report, data, allowed):
	rows = []
	field_cache = {}
	def add(section, values, doctype=None, parent=None):
		if doctype and not allowed.get(doctype):
			return
		field_policy = field_cache.setdefault(doctype, _permitted_fields(doctype)) if doctype else None
		for value in values or []:
			row = {"section": section}
			if parent: row["parent"] = parent
			for key, item in _dict(value).items():
				if isinstance(item, (dict, list, tuple)):
					continue
				underlying = FIELD_ALIASES.get(doctype, {}).get(key, key)
				if field_policy and underlying in field_policy[1] and underlying not in field_policy[0]:
					continue
				if key in ("deal_label", "deal_title"):
					deal_policy = field_cache.setdefault("DoubleT Deal", _permitted_fields("DoubleT Deal")) if allowed.get("DoubleT Deal") else None
					if not deal_policy or "deal_title" not in deal_policy[0]:
						continue
				if key == "stage_label":
					stage_policy = field_cache.setdefault("DoubleT Deal Stage", _permitted_fields("DoubleT Deal Stage")) if allowed.get("DoubleT Deal Stage") else None
					if not stage_policy or "stage_name" not in stage_policy[0]:
						continue
				row[key] = item
			rows.append(row)
	def comparison(source_doctypes):
		if not all(allowed.get(doctype) for doctype in source_doctypes):
			return
		block = data.get("comparison") or {}
		metrics = block.get("metrics") or {}
		for key, value in metrics.items():
			value = value if isinstance(value, dict) else {"value": value}
			rows.append({"section": "comparison", "metric": key, **{k: v for k, v in value.items() if not isinstance(v, (dict, list, tuple))}})

	if report == "sales-performance":
		add("orders", data.get("order_drilldown"), "DoubleT Order"); add("won_deals", data.get("won_deals"), "DoubleT Deal"); add("lost_deals", data.get("lost_deals"), "DoubleT Deal"); comparison(("DoubleT Order", "DoubleT Deal"))
	elif report == "pipeline-analytics":
		add("pipeline_deals", data.get("created_deals"), "DoubleT Deal"); add("overdue_deals", data.get("overdue_deals"), "DoubleT Deal"); add("stale_deals", data.get("stale_deals"), "DoubleT Deal")
		for group in data.get("lost_reasons") or []: add("lost_deals", group.get("deals"), "DoubleT Deal")
		comparison(("DoubleT Deal", "DoubleT Deal Stage"))
	elif report == "customer-journey":
		for journey in data.get("journey_rows") or []:
			lead = {key: journey.get(key) for key in ("name", "lead_name", "lead_owner", "source", "creation")}
			add("leads", [lead], "DoubleT Lead")
			parent = journey.get("name") or journey.get("lead")
			add("journey_deals", journey.get("deals"), "DoubleT Deal", parent); add("journey_quotations", journey.get("quotations"), "DoubleT Quotation", parent); add("journey_orders", journey.get("orders"), "DoubleT Order", parent)
		comparison(("DoubleT Lead", "DoubleT Deal", "DoubleT Quotation", "DoubleT Order"))
	elif report == "quotation-order":
		add("quotations", data.get("quotation_drilldown"), "DoubleT Quotation"); add("orders", data.get("order_drilldown"), "DoubleT Order")
		for conversion in (data.get("conversion") or {}).get("accepted_conversion_drilldown") or []:
			add("accepted_quotations", [conversion], "DoubleT Quotation")
			add("accepted_orders", conversion.get("orders"), "DoubleT Order", conversion.get("quotation") or conversion.get("name"))
		comparison(("DoubleT Quotation", "DoubleT Order", "DoubleT Deal"))
	elif report == "activity-contact-center":
		sources = data.get("sources") or {}
		if (sources.get("calls") or {}).get("selected"): add("calls", (sources.get("calls") or {}).get("rows"), "DoubleT Call Log")
		if (sources.get("tasks") or {}).get("selected"): add("tasks", (sources.get("tasks") or {}).get("rows"), "DoubleT Task")
		if (sources.get("email") or {}).get("selected"): add("email", (sources.get("email") or {}).get("rows"), "Communication")
		if (sources.get("zalo") or {}).get("selected"):
			add("zalo_conversations", (sources.get("zalo") or {}).get("conversations"), "DoubleT Conversation")
			add("zalo_messages", (sources.get("zalo") or {}).get("messages"), "DoubleT Message")
	else:
		for alert in data.get("alerts") or []: add("alerts", [alert], alert.get("source_doctype"))
		if all(allowed.values()): add("deal_health", data.get("health"))
	if not rows:
		rows.append({"section": "empty", "message": "No authorized records matched the applied filters."})
	return rows


def _safe_cell(value):
	if value is None:
		return ""
	text = str(value)
	if re.match(r"^[\t\r\n ]*[=+\-@]", text):
		return "'" + text
	return text


@frappe.whitelist()
def export_report(report, filters=None):
	"""Re-run an allowlisted report and return an Excel-compatible authorized CSV."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required."), frappe.PermissionError)
	report, config = _report(report)
	allowed = _source_permissions(config)
	if not any(allowed.values()):
		frappe.throw(_("You do not have export permission for any report source."), frappe.PermissionError)
	applied = _filters(report, filters or {})
	data = config["method"](**applied, limit=None) if report == "smart-insights" else config["method"](**applied)
	rows = _export_rows(report, data, allowed)
	generated_at = str(now_datetime())
	actual_filters = dict(data.get("filters") or {})
	for key in ("start_date", "end_date", "as_of_date"):
		if data.get(key) is not None: actual_filters[key] = data[key]
	metadata = {
		"report": config["label"], "generated_at": generated_at,
		"currency": data.get("currency") or "",
		"period_start": actual_filters.get("start_date") or actual_filters.get("as_of_date") or "",
		"period_end": actual_filters.get("end_date") or actual_filters.get("as_of_date") or "",
		"applied_filters": json.dumps(actual_filters, ensure_ascii=False, sort_keys=True),
	}
	for row in rows:
		row.update({key: row.get(key, value) for key, value in metadata.items()})
	headers = list(metadata) + ["section"]
	for row in rows:
		for key in row:
			if key not in headers:
				headers.append(key)
	stream = io.StringIO(newline="")
	writer = csv.DictWriter(stream, fieldnames=headers, extrasaction="ignore")
	writer.writeheader()
	writer.writerows({key: _safe_cell(value) for key, value in row.items()} for row in rows)
	return {
		"filename": f"{report}-{generated_at[:10]}.csv",
		"mime_type": "text/csv;charset=utf-8",
		"content": "\ufeff" + stream.getvalue(),
		"row_count": len(rows), "filters": actual_filters,
	}


def _saved_settings():
	try:
		settings = json.loads(get_user_settings(USER_SETTINGS_DOCTYPE) or "{}")
	except (TypeError, ValueError):
		settings = {}
	return settings, settings.get("doublet_crm_saved_report_filters") or {}


@frappe.whitelist()
def get_saved_filters(report):
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required."), frappe.PermissionError)
	report, _config = _report(report)
	_settings, saved = _saved_settings()
	return saved.get(report) or []


@frappe.whitelist()
def save_filter(report, name, filters):
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required."), frappe.PermissionError)
	report, _config = _report(report)
	name = " ".join((name or "").strip().split())
	if not name or len(name) > 80:
		frappe.throw(_("Filter name is required and cannot exceed 80 characters."), frappe.ValidationError)
	clean = _filters(report, filters)
	settings, saved = _saved_settings()
	items = [item for item in saved.get(report, []) if item.get("name") != name]
	if len(items) >= MAX_SAVED_FILTERS:
		frappe.throw(_("You can save up to {0} filters per report.").format(MAX_SAVED_FILTERS), frappe.ValidationError)
	items.append({"name": name, "filters": clean})
	saved[report] = sorted(items, key=lambda item: item["name"].lower())
	settings["doublet_crm_saved_report_filters"] = saved
	update_user_settings(USER_SETTINGS_DOCTYPE, {"doublet_crm_saved_report_filters": saved})
	return saved[report]


@frappe.whitelist()
def delete_filter(report, name):
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required."), frappe.PermissionError)
	report, _config = _report(report)
	settings, saved = _saved_settings()
	saved[report] = [item for item in saved.get(report, []) if item.get("name") != (name or "").strip()]
	settings["doublet_crm_saved_report_filters"] = saved
	update_user_settings(USER_SETTINGS_DOCTYPE, {"doublet_crm_saved_report_filters": saved})
	return saved[report]
