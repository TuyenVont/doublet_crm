"""Permission-scoped current-stage aging derived from tracked Version history."""

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


def _stage_label(deal, stages):
	stage = stages.get(deal.stage)
	return stage.stage_name if stage else (deal.stage or _("Unassigned Stage"))


def _stage_entry(deal, versions, as_of, tracking_enabled=True):
	"""Return the latest evidenced entry into the current stage, or an honest Unknown."""
	changes = []
	for version in sorted(versions, key=lambda row: (str(row.creation or ""), row.name or "")):
		try:
			data = frappe.parse_json(version.data or "{}")
		except (TypeError, ValueError):
			return None, None, _("Version history contains unreadable data.")
		if not isinstance(data, dict) or not isinstance(data.get("changed", []), list):
			return None, None, _("Version history is incomplete.")
		for change in data.get("changed", []):
			if not isinstance(change, (list, tuple)) or len(change) < 3:
				continue
			if change[0] == "stage":
				changes.append((version.creation, change[1], change[2]))
	if changes:
		entry, _old_stage, new_stage = changes[-1]
		if new_stage != deal.stage:
			return None, None, _("Stage history does not reconcile with the current stage.")
	else:
		if not tracking_enabled:
			return None, None, _("Change tracking was not available to establish the initial stage.")
		entry = deal.creation
		if not entry:
			return None, None, _("Deal creation time is unavailable.")
	if getdate(entry) > as_of:
		return None, None, _("Stage entry is later than the report as-of date.")
	return entry, (as_of - getdate(entry)).days, None


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
	history_available = bool(frappe.has_permission("Version", "read"))
	version_fields = set()
	if history_available:
		version_fields = set(get_permitted_fields("Version", permission_type="read")) | {"name"}
		history_available = {"name", "creation", "data", "docname", "ref_doctype"}.issubset(version_fields)
	deal_names = [deal.name for deal in deals]
	versions = []
	if history_available and deal_names:
		versions = frappe.get_list(
			"Version",
			filters={"ref_doctype": "DoubleT Deal", "docname": ["in", deal_names]},
			fields=["name", "docname", "creation", "data"],
			order_by="creation asc, name asc", limit_page_length=0,
		)
	versions_by_deal = defaultdict(list)
	for version in versions:
		versions_by_deal[version.docname].append(version)
	tracking_enabled = bool(frappe.get_meta("DoubleT Deal").track_changes) if history_available else False
	rows = []
	for deal in deals:
		if history_available:
			entry, days, unknown_reason = _stage_entry(deal, versions_by_deal[deal.name], as_of, tracking_enabled)
		else:
			entry, days = None, None
			unknown_reason = _("Version history is unavailable with your permissions.")
		rows.append({
			"name": deal.name, "deal_title": deal.deal_title, "deal_owner": deal.deal_owner,
			"stage": deal.stage, "stage_label": _stage_label(deal, stages),
			"stage_entry_date": entry, "days_in_stage": days,
			"history_status": "Known" if days is not None else "Unknown",
			"unknown_reason": unknown_reason,
		})
	return {
		"available": True, "history_available": history_available,
		"reason": None if history_available else _("Version history is unavailable; stage duration remains Unknown."),
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
		"definition": _("Days in current stage uses tracked stage transitions. Deal creation is used only when readable complete Version history contains no stage transition while change tracking is enabled. Unrelated edits do not reset aging."),
		"average_days_in_stage": flt(sum(row["days_in_stage"] for row in known) / len(known), 2) if known else None,
		"known_count": len(known), "unknown_count": len(rows) - len(known),
		"by_stage": sorted(by_stage, key=lambda row: (row["stage_label"], row["stage"] or "")),
		"buckets": buckets,
	}
