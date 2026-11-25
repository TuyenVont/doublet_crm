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
		"label": "Pipeline Analytics", "sources": ("DoubleT Deal", "DoubleT Deal Stage", "Version"), "method": reports.get_pipeline_analytics,
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
		"label": "Activity & Contact Center", "sources": ("DoubleT Call Log", "DoubleT Task", "Communication", "DoubleT Conversation", "DoubleT Message", "DoubleT Lead", "DoubleT Deal", "DoubleT Contact", "DoubleT Company", "DoubleT Quotation", "DoubleT Order"), "method": reports.get_activity_contact_center,
		"filters": {"start_date", "end_date", "employee", "channel"},
	},
	"smart-insights": {
		"label": "Smart Insights", "sources": ("DoubleT Deal", "DoubleT Deal Stage", "DoubleT Quotation", "DoubleT Task", "DoubleT Call Log", "Communication", "DoubleT Lead", "DoubleT Contact", "DoubleT Company", "Version"), "method": build_smart_insights,
		"filters": {"as_of_date", "salesperson", "alert_type"},
	},
}
USER_SETTINGS_DOCTYPE = "DoubleT CRM Reports"
MAX_SAVED_FILTERS = 25
LINKED_FIELDS = {
	("DoubleT Deal", "stage"): "DoubleT Deal Stage",
	("DoubleT Quotation", "deal"): "DoubleT Deal",
	("DoubleT Order", "deal"): "DoubleT Deal",
	("DoubleT Order", "quotation"): "DoubleT Quotation",
	("DoubleT Message", "conversation"): "DoubleT Conversation",
	("DoubleT Conversation", "lead"): "DoubleT Lead",
}
DYNAMIC_LINK_FIELDS = {
	"DoubleT Task": ("reference_doctype", "reference_docname"),
	"Communication": ("reference_doctype", "reference_name"),
}
DERIVED_FIELDS = {
	"DoubleT Deal": {
		"label": (("DoubleT Deal", "deal_title"),), "deal": (("DoubleT Deal", "name"),), "source_doctype": (), "source_id": (("DoubleT Deal", "name"),),
		"source_label": (("DoubleT Deal", "deal_title"),), "owner": (("DoubleT Deal", "deal_owner"),),
		"event_date": (("DoubleT Deal", "won_on"), ("DoubleT Deal", "lost_on")),
		"close_duration_days": (("DoubleT Deal", "creation"), ("DoubleT Deal", "won_on")),
		"stage_label": (("DoubleT Deal", "stage"), ("DoubleT Deal Stage", "stage_name")),
		"won": (("DoubleT Deal", "won_on"),),
		"type": (("DoubleT Deal", "modified"), ("DoubleT Deal", "expected_close_date"), ("DoubleT Deal", "won_on"), ("DoubleT Deal", "lost_on")),
		"severity": (("DoubleT Deal", "modified"), ("DoubleT Deal", "expected_close_date")),
		"reason": (("DoubleT Deal", "modified"), ("DoubleT Deal", "expected_close_date")),
		"relevant_date": (("DoubleT Deal", "modified"), ("DoubleT Deal", "expected_close_date")),
		"days": (("DoubleT Deal", "modified"), ("DoubleT Deal", "expected_close_date")),
		"score": (), "category": (), "definition": (),
		"weighted_value": (("DoubleT Deal", "amount"),), "probability_source": (),
		"stage_entry_date": (("DoubleT Deal", "stage"), ("DoubleT Deal", "creation"), ("Version", "ref_doctype"), ("Version", "docname"), ("Version", "creation"), ("Version", "data")),
		"days_in_stage": (("DoubleT Deal", "stage"), ("DoubleT Deal", "creation"), ("Version", "ref_doctype"), ("Version", "docname"), ("Version", "creation"), ("Version", "data")),
		"history_status": (("DoubleT Deal", "stage"), ("DoubleT Deal", "creation"), ("Version", "ref_doctype"), ("Version", "docname"), ("Version", "creation"), ("Version", "data")),
		"unknown_reason": (("DoubleT Deal", "stage"), ("DoubleT Deal", "creation"), ("Version", "ref_doctype"), ("Version", "docname"), ("Version", "creation"), ("Version", "data")),
	},
	"DoubleT Quotation": {
		"source_doctype": (), "source_id": (("DoubleT Quotation", "name"),), "source_label": (("DoubleT Quotation", "name"),),
		"type": (("DoubleT Quotation", "status"), ("DoubleT Quotation", "valid_until")),
		"severity": (("DoubleT Quotation", "valid_until"),), "reason": (("DoubleT Quotation", "valid_until"),),
		"relevant_date": (("DoubleT Quotation", "valid_until"),), "days": (("DoubleT Quotation", "valid_until"),),
		"owner": (("DoubleT Quotation", "deal"), ("DoubleT Deal", "deal_owner")),
		"linked_deal": (("DoubleT Quotation", "deal"), ("DoubleT Deal", "name")),
		"deal_title": (("DoubleT Quotation", "deal"), ("DoubleT Deal", "deal_title")),
		"converted": (("DoubleT Quotation", "name"), ("DoubleT Order", "quotation"), ("DoubleT Order", "status")),
		"deal_restricted": (("DoubleT Quotation", "deal"), ("DoubleT Deal", "name")),
	},
	"DoubleT Task": {
		"source_doctype": (), "source_id": (("DoubleT Task", "name"),), "source_label": (("DoubleT Task", "title"),),
		"type": (("DoubleT Task", "status"), ("DoubleT Task", "due_date")), "severity": (("DoubleT Task", "due_date"),),
		"reason": (("DoubleT Task", "status"), ("DoubleT Task", "due_date")), "relevant_date": (("DoubleT Task", "due_date"),),
		"days": (("DoubleT Task", "due_date"),), "owner": (("DoubleT Task", "assigned_to"),),
	},
	"DoubleT Order": {
		"deal_label": (("DoubleT Order", "deal"), ("DoubleT Deal", "deal_title")),
		"deal_title": (("DoubleT Order", "deal"), ("DoubleT Deal", "deal_title")),
		"is_booked": (("DoubleT Order", "status"),),
		"link_type": (("DoubleT Order", "deal"), ("DoubleT Order", "quotation"), ("DoubleT Deal", "name"), ("DoubleT Quotation", "name")),
		"deal_restricted": (("DoubleT Order", "deal"), ("DoubleT Deal", "name")),
	},
	"DoubleT Lead": {
		"owner": (("DoubleT Lead", "lead_owner"),), "label": (("DoubleT Lead", "lead_owner"),),
	},
}

HEALTH_SCORE_DEPENDENCIES = (
	("DoubleT Deal", "modified"), ("DoubleT Deal", "expected_close_date"), ("DoubleT Deal", "won_on"),
	("DoubleT Deal", "lost_on"), ("DoubleT Deal", "stage"), ("DoubleT Deal Stage", "stage_type"),
	("DoubleT Task", "status"), ("DoubleT Task", "due_date"), ("DoubleT Task", "reference_docname"),
	("DoubleT Quotation", "status"), ("DoubleT Quotation", "valid_until"), ("DoubleT Quotation", "deal"),
	("DoubleT Call Log", "start_time"), ("DoubleT Call Log", "reference_name"),
	("Communication", "creation"), ("Communication", "reference_name"),
)
ALERT_ROW_DEPENDENCIES = {
	"DoubleT Deal": (("DoubleT Deal", "modified"), ("DoubleT Deal", "expected_close_date"), ("DoubleT Deal", "won_on"), ("DoubleT Deal", "lost_on"), ("DoubleT Deal", "stage"), ("DoubleT Deal Stage", "stage_type")),
	"DoubleT Quotation": (("DoubleT Quotation", "status"), ("DoubleT Quotation", "valid_until")),
	"DoubleT Task": (("DoubleT Task", "status"), ("DoubleT Task", "due_date")),
}
STAGE_AGING_DEPENDENCIES = (
	("DoubleT Deal", "stage"), ("DoubleT Deal", "creation"),
	("Version", "ref_doctype"), ("Version", "docname"), ("Version", "creation"), ("Version", "data"),
)

COMPARISON_FIELDS = {
	"sales-performance": {
		"booked_sales": (("DoubleT Order", "order_date"), ("DoubleT Order", "status"), ("DoubleT Order", "total")),
		"order_count": (("DoubleT Order", "order_date"), ("DoubleT Order", "status")),
		"average_order_value": (("DoubleT Order", "order_date"), ("DoubleT Order", "status"), ("DoubleT Order", "total")),
		"won_count": (("DoubleT Deal", "won_on"),), "lost_count": (("DoubleT Deal", "lost_on"),),
		"won_deal_value": (("DoubleT Deal", "won_on"), ("DoubleT Deal", "amount")),
		"win_rate": (("DoubleT Deal", "won_on"), ("DoubleT Deal", "lost_on")),
		"average_close_duration_days": (("DoubleT Deal", "won_on"), ("DoubleT Deal", "creation")),
	},
	"pipeline-analytics": {
		"deal_count": (("DoubleT Deal", "creation"),), "total_deal_value": (("DoubleT Deal", "creation"), ("DoubleT Deal", "amount")),
		"open_pipeline_value": (("DoubleT Deal", "creation"), ("DoubleT Deal", "amount"), ("DoubleT Deal", "stage"), ("DoubleT Deal Stage", "stage_type")),
		"lost_reason_deal_count": (("DoubleT Deal", "lost_on"),),
		"overdue_open_count": (("DoubleT Deal", "expected_close_date"), ("DoubleT Deal", "stage"), ("DoubleT Deal Stage", "stage_type")),
		"stale_open_count": (("DoubleT Deal", "modified"), ("DoubleT Deal", "stage"), ("DoubleT Deal Stage", "stage_type")),
	},
	"customer-journey": {
		"lead_count": (("DoubleT Lead", "creation"),),
		"deal_count": (("DoubleT Lead", "converted_deal"), ("DoubleT Deal", "source_lead")),
		"won_lead_count": (("DoubleT Lead", "converted_deal"), ("DoubleT Deal", "source_lead"), ("DoubleT Deal", "won_on")),
		"quotation_count": (("DoubleT Deal", "source_lead"), ("DoubleT Quotation", "deal")),
		"order_count": (("DoubleT Deal", "source_lead"), ("DoubleT Order", "deal"), ("DoubleT Order", "quotation"), ("DoubleT Order", "status")),
		"lead_value": (("DoubleT Deal", "source_lead"), ("DoubleT Deal", "amount")),
		"deal_value": (("DoubleT Deal", "source_lead"), ("DoubleT Deal", "amount")),
		"quotation_value": (("DoubleT Quotation", "deal"), ("DoubleT Quotation", "grand_total")),
		"order_value": (("DoubleT Order", "deal"), ("DoubleT Order", "quotation"), ("DoubleT Order", "status"), ("DoubleT Order", "total")),
		"lead_to_deal_rate": (("DoubleT Lead", "creation"), ("DoubleT Lead", "converted_deal"), ("DoubleT Deal", "source_lead")),
		"lead_to_won_rate": (("DoubleT Lead", "creation"), ("DoubleT Deal", "source_lead"), ("DoubleT Deal", "won_on")),
		"deal_to_order_rate": (("DoubleT Deal", "source_lead"), ("DoubleT Order", "deal"), ("DoubleT Order", "quotation"), ("DoubleT Order", "status")),
	},
	"quotation-order": {
		"quotation_count": (("DoubleT Quotation", "quotation_date"),),
		"quotation_value": (("DoubleT Quotation", "quotation_date"), ("DoubleT Quotation", "grand_total")),
		"accepted_count": (("DoubleT Quotation", "quotation_date"), ("DoubleT Quotation", "status")),
		"acceptance_rate": (("DoubleT Quotation", "quotation_date"), ("DoubleT Quotation", "status")),
		"order_count": (("DoubleT Order", "order_date"),),
		"booked_sales": (("DoubleT Order", "order_date"), ("DoubleT Order", "status"), ("DoubleT Order", "total")),
		"booked_order_count": (("DoubleT Order", "order_date"), ("DoubleT Order", "status")),
		"quotations_with_orders": (("DoubleT Quotation", "name"), ("DoubleT Order", "quotation"), ("DoubleT Order", "status")),
		"quotation_to_order_rate": (("DoubleT Quotation", "name"), ("DoubleT Order", "quotation"), ("DoubleT Order", "status")),
		"quotation_value_converted": (("DoubleT Quotation", "name"), ("DoubleT Quotation", "grand_total"), ("DoubleT Order", "quotation"), ("DoubleT Order", "status")),
		"accepted_quotation_count": (("DoubleT Quotation", "status"),),
		"accepted_quotations_with_orders": (("DoubleT Quotation", "name"), ("DoubleT Quotation", "status"), ("DoubleT Order", "quotation"), ("DoubleT Order", "status")),
		"accepted_to_booked_order_rate": (("DoubleT Quotation", "name"), ("DoubleT Quotation", "status"), ("DoubleT Order", "quotation"), ("DoubleT Order", "status")),
	},
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
	document_cache = {}

	def field_policy(doctype):
		return field_cache.setdefault(doctype, _permitted_fields(doctype))

	def authorized(dependencies):
		for doctype, fieldname in dependencies:
			if not allowed.get(doctype) or fieldname not in field_policy(doctype)[0]:
				return False
		return True

	def document_allowed(doctype, name):
		if not name or not allowed.get(doctype):
			return False
		key = (doctype, str(name))
		if key not in document_cache:
			document_cache[key] = bool(frappe.has_permission(doctype, "read", doc=name))
		return document_cache[key]

	def dependencies_allow_links(doctype, value, dependencies):
		dependency_set = set(dependencies or ())
		for (source_doctype, link_field), target_doctype in LINKED_FIELDS.items():
			if source_doctype != doctype or not any(dependency_doctype == target_doctype for dependency_doctype, _fieldname in dependency_set):
				continue
			if not document_allowed(target_doctype, value.get(link_field)):
				return False
		return True

	def add(section, values, doctype=None, parent=None, parent_doctype=None, extra_dependencies=None):
		if doctype and not allowed.get(doctype):
			return
		policy = field_policy(doctype) if doctype else None
		for value in values or []:
			value = _dict(value)
			row = {"section": section}
			if parent and parent_doctype and authorized(((parent_doctype, "name"),)) and document_allowed(parent_doctype, parent):
				row["parent"] = parent
			dynamic_fields = DYNAMIC_LINK_FIELDS.get(doctype)
			dynamic_link_allowed = True
			if dynamic_fields:
				doctype_field, name_field = dynamic_fields
				target_doctype = value.get(doctype_field)
				dynamic_link_allowed = bool(target_doctype and authorized(((doctype, doctype_field), (doctype, name_field), (target_doctype, "name"))) and document_allowed(target_doctype, value.get(name_field)))
			for key, item in value.items():
				if isinstance(item, (dict, list, tuple)):
					continue
				if dynamic_fields and key in dynamic_fields and not dynamic_link_allowed:
					continue
				target = LINKED_FIELDS.get((doctype, key))
				if target and (not authorized(((doctype, key), (target, "name"))) or (item and not document_allowed(target, item))):
					continue
				if policy and key in policy[0]:
					row[key] = item
					continue
				if policy and key in policy[1]:
					continue
				dependencies = (extra_dependencies or {}).get(key, DERIVED_FIELDS.get(doctype, {}).get(key))
				if dependencies is None or not authorized(dependencies) or not dependencies_allow_links(doctype, value, dependencies):
					continue
				row[key] = item
			rows.append(row)

	def comparison():
		block = data.get("comparison") or {}
		metrics = block.get("metrics") or {}
		for key, value in metrics.items():
			dependencies = COMPARISON_FIELDS.get(report, {}).get(key)
			if dependencies is None or not authorized(dependencies):
				continue
			value = value if isinstance(value, dict) else {"value": value}
			rows.append({"section": "comparison", "metric": key, **{k: v for k, v in value.items() if not isinstance(v, (dict, list, tuple))}})

	if report == "sales-performance":
		add("orders", data.get("order_drilldown"), "DoubleT Order"); add("won_deals", data.get("won_deals"), "DoubleT Deal"); add("lost_deals", data.get("lost_deals"), "DoubleT Deal"); comparison()
	elif report == "pipeline-analytics":
		add("pipeline_deals", data.get("created_deals"), "DoubleT Deal"); add("overdue_deals", data.get("overdue_deals"), "DoubleT Deal"); add("stale_deals", data.get("stale_deals"), "DoubleT Deal")
		for group in data.get("lost_reasons") or []: add("lost_deals", group.get("deals"), "DoubleT Deal")
		forecast = data.get("forecast") or {}
		probability_fields = forecast.get("probability_fields") or {}
		probability_dependencies = tuple(
			(doctype, probability_fields.get(key))
			for key, doctype in (("deal", "DoubleT Deal"), ("stage", "DoubleT Deal Stage"))
			if probability_fields.get(key)
		)
		probability_authorized = bool(probability_dependencies) and authorized(probability_dependencies)
		if forecast.get("available") and authorized((("DoubleT Deal", "amount"), ("DoubleT Deal", "expected_close_date"), ("DoubleT Deal", "stage"))):
			summary = {"section": "forecast_summary"}
			for key in (
				"open_deal_count", "total_unweighted_pipeline_value", "forecast_deal_count", "unweighted_forecast_value",
				"missing_close_date_count", "missing_close_date_value", "overdue_count", "overdue_value",
				"outside_period_count", "outside_period_value",
			):
				summary[key] = forecast.get(key)
			if probability_authorized:
				for key in ("weighted_forecast_value", "missing_probability_count", "missing_probability_value"):
					summary[key] = forecast.get(key)
			rows.append(summary)
		for month in forecast.get("months") or []:
			if authorized((("DoubleT Deal", "amount"), ("DoubleT Deal", "expected_close_date"), ("DoubleT Deal", "stage"))):
				month_row = {"section": "forecast_months", **{key: month.get(key) for key in ("month", "deal_count", "unweighted_value")}}
				if probability_authorized:
					month_row.update({key: month.get(key) for key in ("weighted_value", "weighted_deal_count", "missing_probability_count")})
				rows.append(month_row)
		for section, values in (
			("forecast_deals", forecast.get("deals")), ("forecast_missing_close_date", forecast.get("missing_close_date_deals")),
			("forecast_overdue", forecast.get("overdue_deals")), ("forecast_outside_period", forecast.get("outside_period_deals")),
		):
			for value in values or []:
				row = dict(value)
				fieldname = probability_fields.get("deal") if row.get("probability_source", "").startswith("DoubleT Deal.") else probability_fields.get("stage")
				probability_doctype = "DoubleT Deal" if row.get("probability_source", "").startswith("DoubleT Deal.") else "DoubleT Deal Stage"
				if not fieldname or not authorized(((probability_doctype, fieldname),)):
					for key in ("probability", "probability_source", "weighted_value"):
						row.pop(key, None)
				probability_dependency = ((probability_doctype, fieldname),) if fieldname else ()
				add(section, [row], "DoubleT Deal", extra_dependencies={
					"probability": probability_dependency,
					"probability_source": probability_dependency,
					"weighted_value": (("DoubleT Deal", "amount"),) + probability_dependency,
				})
		stage_aging = data.get("stage_aging") or {}
		if stage_aging.get("available") and authorized(STAGE_AGING_DEPENDENCIES):
			rows.append({"section": "stage_aging_summary", **{key: stage_aging.get(key) for key in ("average_days_in_stage", "known_count", "unknown_count")}})
			for bucket in stage_aging.get("buckets") or []:
				rows.append({"section": "stage_aging_buckets", **{key: bucket.get(key) for key in ("key", "label", "deal_count")}})
			if authorized(STAGE_AGING_DEPENDENCIES + (("DoubleT Deal Stage", "name"), ("DoubleT Deal Stage", "stage_name"))):
				for stage in stage_aging.get("by_stage") or []:
					if stage.get("stage") and not document_allowed("DoubleT Deal Stage", stage["stage"]):
						continue
					rows.append({"section": "stage_aging_by_stage", **{key: stage.get(key) for key in ("stage", "stage_label", "deal_count", "known_count", "unknown_count", "average_days_in_stage")}})
			add("stage_aging_deals", stage_aging.get("rows"), "DoubleT Deal")
		comparison()
	elif report == "customer-journey":
		for journey in data.get("journey_rows") or []:
			lead = {key: journey.get(key) for key in ("name", "lead_name", "lead_owner", "source", "creation")}
			add("leads", [lead], "DoubleT Lead")
			parent = journey.get("name") or journey.get("lead")
			add("journey_deals", journey.get("deals"), "DoubleT Deal", parent, "DoubleT Lead"); add("journey_quotations", journey.get("quotations"), "DoubleT Quotation", parent, "DoubleT Lead"); add("journey_orders", journey.get("orders"), "DoubleT Order", parent, "DoubleT Lead")
		for owner in data.get("by_owner") or []:
			owner_row = {"owner": owner.get("owner"), "label": owner.get("label")}
			owner_dependencies = {}
			for key, dependencies in COMPARISON_FIELDS["customer-journey"].items():
				if key in owner and authorized(dependencies):
					owner_row[key] = owner[key]
					owner_dependencies[key] = dependencies
			add("journey_owners", [owner_row], "DoubleT Lead", extra_dependencies=owner_dependencies)
		comparison()
	elif report == "quotation-order":
		add("quotations", data.get("quotation_drilldown"), "DoubleT Quotation"); add("orders", data.get("order_drilldown"), "DoubleT Order")
		for conversion in (data.get("conversion") or {}).get("accepted_conversion_drilldown") or []:
			add("accepted_quotations", [conversion], "DoubleT Quotation")
			add("accepted_orders", conversion.get("orders"), "DoubleT Order", conversion.get("quotation") or conversion.get("name"), "DoubleT Quotation")
		comparison()
	elif report == "activity-contact-center":
		sources = data.get("sources") or {}
		if (sources.get("calls") or {}).get("selected"): add("calls", (sources.get("calls") or {}).get("rows"), "DoubleT Call Log")
		if (sources.get("tasks") or {}).get("selected"): add("tasks", (sources.get("tasks") or {}).get("rows"), "DoubleT Task")
		if (sources.get("email") or {}).get("selected"): add("email", (sources.get("email") or {}).get("rows"), "Communication")
		if (sources.get("zalo") or {}).get("selected"):
			add("zalo_conversations", (sources.get("zalo") or {}).get("conversations"), "DoubleT Conversation")
			add("zalo_messages", (sources.get("zalo") or {}).get("messages"), "DoubleT Message")
	else:
		for alert in data.get("alerts") or []:
			doctype = alert.get("source_doctype")
			dependencies = STAGE_AGING_DEPENDENCIES if alert.get("type") == "prolonged_stage" else ALERT_ROW_DEPENDENCIES.get(doctype)
			if dependencies is not None and authorized(dependencies):
				extra_dependencies = None
				if alert.get("type") == "prolonged_stage":
					extra_dependencies = {key: STAGE_AGING_DEPENDENCIES for key in ("type", "severity", "reason", "relevant_date", "days")}
				add("alerts", [alert], doctype, extra_dependencies=extra_dependencies)
		for health in data.get("health") or []:
			eligibility = (("DoubleT Deal", "name"), ("DoubleT Deal", "won_on"), ("DoubleT Deal", "lost_on"), ("DoubleT Deal", "stage"), ("DoubleT Deal Stage", "stage_type"))
			if not authorized(eligibility):
				continue
			row = _dict(health).copy()
			if not authorized(HEALTH_SCORE_DEPENDENCIES):
				for key in ("score", "category", "definition"):
					row.pop(key, None)
			add("deal_health", [row], "DoubleT Deal")
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
