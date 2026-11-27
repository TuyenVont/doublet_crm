"""Permission-scoped current-stage aging from explicit and legacy transition evidence."""

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt, getdate


AGING_BUCKETS = (
	("0_7", "0–7 days", 0, 7),
	("8_14", "8–14 days", 8, 14),
	("15_30", "15–30 days", 15, 30),
	("over_30", "Over 30 days", 31, None),
)
STAGE_EVIDENCE_FIELDS = ("stage_entered_on", "stage_entered_by")


def readable_stage_evidence_fields():
	"""Return installed transition fields the current user may read."""
	from frappe.model import get_permitted_fields

	installed = {field.fieldname for field in frappe.get_meta("DoubleT Deal").fields}
	permitted = set(get_permitted_fields("DoubleT Deal", permission_type="read"))
	return [fieldname for fieldname in STAGE_EVIDENCE_FIELDS if fieldname in installed and fieldname in permitted]


def _stage_label(deal, stages):
	stage = stages.get(deal.stage)
	return stage.stage_name if stage else (deal.stage or _("Unassigned Stage"))


def _stage_evidence(deal, versions, as_of, version_history_available=True):
	"""Return current-stage timestamp, duration, actor, reason and evidence source."""
	explicit_entry = getattr(deal, "stage_entered_on", None)
	if explicit_entry not in (None, ""):
		if getdate(explicit_entry) > as_of:
			return None, None, None, _("Stage entry is later than the report as-of date."), "deal_transition"
		return (
			explicit_entry,
			(as_of - getdate(explicit_entry)).days,
			getattr(deal, "stage_entered_by", None) or None,
			None,
			"deal_transition",
		)
	if not version_history_available:
		return None, None, None, _("No explicit Stage transition is recorded, and Version history is unavailable."), None

	changes = []
	for version in sorted(versions, key=lambda row: (str(row.creation or ""), row.name or "")):
		try:
			data = frappe.parse_json(version.data or "{}")
		except (TypeError, ValueError):
			return None, None, None, _("Version history contains unreadable data."), "version"
		if not isinstance(data, dict) or not isinstance(data.get("changed", []), list):
			return None, None, None, _("Version history is incomplete."), "version"
		for change in data.get("changed", []):
			if not isinstance(change, (list, tuple)) or len(change) < 3:
				return None, None, None, _("Version history is incomplete."), "version"
			if change[0] == "stage":
				changes.append((version.creation, change[1], change[2], getattr(version, "owner", None)))
	if changes:
		entry, _old_stage, new_stage, actor = changes[-1]
		if new_stage != deal.stage:
			return None, None, None, _("Stage history does not reconcile with the current stage."), "version"
	else:
		return None, None, None, _("No recorded transition establishes when the Deal entered its current Stage."), "version"
	if getdate(entry) > as_of:
		return None, None, None, _("Stage entry is later than the report as-of date."), "version"
	return entry, (as_of - getdate(entry)).days, actor or None, None, "version"


def _stage_entry(deal, versions, as_of, tracking_enabled=True):
	"""Backward-compatible duration helper; never infers an entry from Deal creation."""
	entry, days, _actor, reason, _source = _stage_evidence(deal, versions, as_of)
	return entry, days, reason


def stage_aging_for_deals(deals, stages, as_of):
	"""Build aging rows for already permission-scoped readable Open Deals."""
	from frappe.model import get_permitted_fields

	deal_fields = set(get_permitted_fields("DoubleT Deal", permission_type="read")) | {"name"}
	required_deal_fields = {"name", "deal_title", "deal_owner", "stage", "creation"}
	if not required_deal_fields.issubset(deal_fields):
		return {
			"available": False,
			"reason": _("Stage Aging is unavailable because required Deal fields are restricted."),
			"rows": [],
		}
	explicit_fields = set(readable_stage_evidence_fields())
	explicit_evidence_available = "stage_entered_on" in explicit_fields
	version_history_available = bool(frappe.has_permission("Version", "read"))
	version_fields = set()
	if version_history_available:
		version_fields = set(get_permitted_fields("Version", permission_type="read")) | {"name"}
		version_history_available = {"name", "creation", "data", "docname", "ref_doctype"}.issubset(version_fields)
	deal_names = [deal.name for deal in deals]
	versions = []
	if version_history_available and deal_names:
		fields = ["name", "docname", "creation", "data"]
		if "owner" in version_fields:
			fields.append("owner")
		versions = frappe.get_list(
			"Version",
			filters={"ref_doctype": "DoubleT Deal", "docname": ["in", deal_names]},
			fields=fields,
			order_by="creation asc, name asc", limit_page_length=0,
		)
	versions_by_deal = defaultdict(list)
	for version in versions:
		versions_by_deal[version.docname].append(version)
	rows = []
	for deal in deals:
		if explicit_evidence_available or version_history_available:
			entry, days, actor, unknown_reason, evidence_source = _stage_evidence(
				deal, versions_by_deal[deal.name] if version_history_available else [], as_of, version_history_available
			)
		else:
			entry, days, actor, evidence_source = None, None, None, None
			unknown_reason = _("Stage transition evidence is unavailable with your permissions.")
		rows.append({
			"name": deal.name, "deal_title": deal.deal_title, "deal_owner": deal.deal_owner,
			"stage": deal.stage, "stage_label": _stage_label(deal, stages),
			"stage_entry_date": entry, "stage_entry_actor": actor, "days_in_stage": days,
			"evidence_source": evidence_source,
			"history_status": "Known" if days is not None else "Unknown",
			"unknown_reason": unknown_reason,
		})
	evidence_available = explicit_evidence_available or version_history_available
	return {
		"available": True, "history_available": evidence_available,
		"explicit_evidence_available": explicit_evidence_available,
		"version_history_available": version_history_available,
		"reason": None if evidence_available else _("Stage transition evidence is unavailable; stage duration remains Unknown."),
		"rows": rows,
	}


def summarize_stage_aging(result):
	if not result.get("available"):
		return {**result, "average_days_in_stage": None, "known_count": 0, "unknown_count": 0, "by_stage": [], "buckets": []}
	rows = result.get("rows") or []
	known = [row for row in rows if row.get("days_in_stage") is not None]
	groups = defaultdict(list)
	for row in rows:
		groups[(row.get("stage"), row.get("stage_label"))].append(row)
	by_stage = []
	for (stage, label), items in groups.items():
		known_items = [item for item in items if item.get("days_in_stage") is not None]
		by_stage.append({
			"stage": stage, "stage_label": label, "deal_count": len(items),
			"known_count": len(known_items), "unknown_count": len(items) - len(known_items),
			"average_days_in_stage": flt(sum(item["days_in_stage"] for item in known_items) / len(known_items), 2) if known_items else None,
		})
	buckets = []
	for key, label, minimum, maximum in AGING_BUCKETS:
		items = [row for row in known if row["days_in_stage"] >= minimum and (maximum is None or row["days_in_stage"] <= maximum)]
		buckets.append({"key": key, "label": label, "deal_count": len(items)})
	buckets.append({"key": "unknown", "label": _("Unknown"), "deal_count": len(rows) - len(known)})
	return {
		**result,
		"definition": _("Days in current Stage uses an explicitly recorded Stage entry, with readable Version transitions as a legacy fallback. Missing legacy transitions remain Unknown; Deal creation and unrelated edits never reset or invent aging."),
		"average_days_in_stage": flt(sum(row["days_in_stage"] for row in known) / len(known), 2) if known else None,
		"known_count": len(known), "unknown_count": len(rows) - len(known),
		"by_stage": sorted(by_stage, key=lambda row: (row["stage_label"], row["stage"] or "")),
		"buckets": buckets,
	}
