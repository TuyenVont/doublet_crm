import json

import frappe

from doublet_crm.doublet_crm.doctype.doublet_task.doublet_task import revoke_callback_task_shares

CALL_LOG = "DoubleT Call Log"
CALL_EVENT = "DoubleT Call Event"
TASK = "DoubleT Task"
PRIVATE_CASE_FIELDS = {"case_events", "assigned_to", "handling_status"}


def execute():
	# Older installs stored the events as child rows on the readable Call Log.
	if frappe.db.has_column(CALL_EVENT, "parent"):
		event = frappe.qb.DocType(CALL_EVENT)
		(
			frappe.qb.update(event)
			.set(event.call_log, event.parent)
			.where(event.parenttype == CALL_LOG)
			.where(event.parentfield == "case_events")
			.where(event.call_log.isnull() | (event.call_log == ""))
		).run()

	_archive_call_log_versions()
	_archive_callback_versions()
	_disable_event_shares()
	revoke_callback_task_shares()


def _disable_event_shares():
	share = frappe.qb.DocType("DocShare")
	(
		frappe.qb.update(share)
		.set(share.read, 0)
		.set(share.write, 0)
		.set(share.share, 0)
		.set(share.submit, 0)
		.where(share.share_doctype == CALL_EVENT)
	).run()


def _archive_call_log_versions():
	# Keep the public changes in Desk and retain the original under case permissions.
	revisions = frappe.get_all(
		"Version",
		filters={"ref_doctype": CALL_LOG},
		or_filters=[["data", "like", f'%"{field}"%'] for field in sorted(PRIVATE_CASE_FIELDS)],
		fields=["name", "docname", "owner", "creation", "data"],
	)
	for revision in revisions:
		original = json.loads(revision.data)
		data = dict(original)
		for key in ("changed", "added", "removed", "row_changed"):
			if key in data:
				data[key] = [entry for entry in data[key] if entry[0] not in PRIVATE_CASE_FIELDS]
		if data != original:
			_archive_revision(revision, revision.docname, CALL_LOG, data)


def _archive_callback_versions():
	version = frappe.qb.DocType("Version")
	task = frappe.qb.DocType(TASK)
	revisions = (
		frappe.qb.from_(version)
		.join(task)
		.on(version.docname == task.name)
		.select(version.name, version.docname, version.owner, version.creation, version.data, task.callback_call_log)
		.where(version.ref_doctype == TASK)
		.where(task.callback_call_log.notnull() & (task.callback_call_log != ""))
		.where(version.data.notnull() & (version.data != "{}"))
	).run(as_dict=True)
	for revision in revisions:
		if revision.data and json.loads(revision.data):
			_archive_revision(revision, revision.callback_call_log, TASK, {})


def _archive_revision(revision, call_log, source_doctype, public_data):
	if not frappe.db.exists(CALL_EVENT, {"source_version": revision.name}):
		frappe.get_doc({
			"doctype": CALL_EVENT,
			"call_log": call_log,
			"action": "Legacy case revision",
			"actor": revision.owner,
			"occurred_at": revision.creation,
			"source_version": revision.name,
			"revision_data": frappe.as_json({
				"ref_doctype": source_doctype,
				"docname": revision.docname,
				"data": json.loads(revision.data),
			}, indent=None),
		}).insert(ignore_permissions=True)
	frappe.db.set_value(
		"Version", revision.name, "data", frappe.as_json(public_data, indent=None), update_modified=False,
	)
