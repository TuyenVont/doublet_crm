"""Call history, queue management and callback tasks for Contact Center."""

from datetime import date, datetime, time
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlsplit

import frappe
from frappe import _
from frappe.utils import cint, cstr, getdate, now_datetime

from doublet_crm.api import CALL_LOG_TYPES, _assignable_user_names
from doublet_crm.calls_demo import is_recording_demo

from doublet_crm.doublet_crm.doctype.doublet_call_log.doublet_call_log import (
	ALLOWED_REFERENCE_DOCTYPES,
	HANDLING_STATUSES,
	INCOMING_CALL_TYPES,
	find_phone_matches,
	get_contact_number,
	is_missed_incoming,
	normalize_phone_number,
)
from doublet_crm.permissions import CALL_MANAGER_ROLES, can_handle_call, can_manage_calls, can_use_call_summary

CALL_LOG = "DoubleT Call Log"
CALL_EVENT = "DoubleT Call Event"
EVENT_FIELDS = ("action", "actor", "occurred_at", "previous_assignee", "new_assignee", "details")
TASK = "DoubleT Task"
OPEN_TASK_STATUSES = {"Backlog", "Todo", "In Progress"}
CALLBACK_RESULTS = {"No Answer", "Reached"}
CALL_SUMMARY_FIELDS = [
	"name", "agent", "call_type", "status", "start_time", "duration",
	"from_number", "to_number", "reference_doctype", "reference_name", "handling_status", "assigned_to",
]
PAGE_SIZE = 25
SEARCH_SCAN_LIMIT = 150
QUEUE_ORDER = "queue_priority desc, start_time desc, name desc"
AUDIO_EXTENSIONS = {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav", ".webm"}


def _read_call(name, *, for_update=False):
	call = frappe.get_doc(CALL_LOG, name, for_update=for_update)
	call.check_permission("read")
	return call


def _read_customer(doctype, name):
	if doctype not in ALLOWED_REFERENCE_DOCTYPES or not name:
		frappe.throw(_("Select a Lead or Contact."))
	customer = frappe.get_doc(doctype, name)
	customer.check_permission("read")
	return customer


def _customer_links(calls, *, with_phone=False):
	customers = {}
	fields = ["name", "first_name", "last_name"]
	if with_phone:
		fields.append("phone")
	for doctype in ALLOWED_REFERENCE_DOCTYPES:
		names = {row.reference_name for row in calls if row.reference_doctype == doctype and row.reference_name}
		if not names or not frappe.has_permission(doctype, "read"):
			continue
		for row in frappe.get_list(
			doctype, filters={"name": ["in", list(names)]},
			fields=fields, limit_page_length=len(names),
		):
			label = " ".join(filter(None, (row.first_name, row.last_name))) or row.name
			customers[(doctype, row.name)] = frappe._dict(
				doctype=doctype, name=row.name, label=label, phone=row.get("phone"),
			)
	return customers


def _call_summary(call, customers):
	row = {field: call.get(field) for field in CALL_SUMMARY_FIELDS}
	row.pop("reference_doctype")
	row.pop("reference_name")
	number_field = "from_number" if call.call_type in INCOMING_CALL_TYPES else "to_number"
	row["customer_number"] = call.get(number_field)
	row["assignee_label"] = _user_label(call.assigned_to)
	customer = customers.get((call.reference_doctype, call.reference_name))
	row["customer"] = {key: customer[key] for key in ("doctype", "name", "label")} if customer else None
	return row


def _private_recording_pointer(value):
	try:
		url = urlsplit(value)
	except ValueError:
		return None, None
	path = unquote(url.path)
	if url.scheme or url.netloc or not path.startswith("/private/files/"):
		return None, None
	return path, parse_qs(url.query, keep_blank_values=True).get("fid")


def _select_recording(call):
	# A declared private recording may only resolve to a File on this call.
	recording_url = call.recording_url or ""
	path, file_ids = _private_recording_pointer(recording_url)
	filters = {"attached_to_doctype": CALL_LOG, "attached_to_name": call.name}
	if path:
		filters.update(file_url=path, is_private=1)
	files = [
		row for row in frappe.get_all(
			"File", filters=filters, order_by="name asc",
			fields=["name", "file_name", "file_url", "is_private", "content_hash"],
		)
		if row.file_url and Path(row.file_name or "").suffix.lower() in AUDIO_EXTENSIONS
		and (file_ids is None or file_ids == [row.name])
	]
	private_files = [row for row in files if row.is_private and row.file_url.startswith("/private/files/")]
	if not private_files:
		if path:
			return "Missing", None
		return ("Legacy" if recording_url or files else "None"), None

	# Treat a legacy public File and its byte-identical private copy as one
	# recording. Different sources require a selection, even if one is missing.
	if not path and len({row.content_hash or row.file_url for row in files}) > 1:
		return "Ambiguous", None
	for row in private_files:
		file = frappe.get_doc("File", row.name)
		if file.is_downloadable() and Path(file.get_full_path()).is_file():
			return "Available", file
	return "Missing", None



def _recording(call):
	state, file = _select_recording(call)
	if not file:
		return {"state": state}
	return {
		"state": state,
		"label": file.file_name,
		"url": f"{quote(file.file_url)}?fid={quote(file.name, safe='')}",
	}

def _link_state(call, customer):
	if call.reference_name:
		return "Linked" if customer else "Restricted"
	number = get_contact_number(call.call_type, call.from_number, call.to_number)
	return "Ambiguous" if len(find_phone_matches(number)) > 1 else "Unmatched"


@frappe.whitelist(methods=["GET", "POST"])
def get_call(name: str):
	call = _read_call(name)
	task = _get_callback(call) if can_handle_call(call.assigned_to) else None
	return _call_details(call, task)


def _call_details(call, task):
	can_handle = can_handle_call(call.assigned_to)
	row = _call_summary(call, _customer_links([call]))
	row.update({
		"end_time": call.end_time,
		"line_number": call.line_number,
		"external_call_id": call.external_call_id,
		"note": call.note,
		"recording": _recording(call),
		"is_recording_demo": is_recording_demo(call),
		"link_state": _link_state(call, row["customer"]),
		"history": _history(call) if can_handle else [],
		"callback_required": is_missed_incoming(call),
		"callback_task": _callback_summary(task) if can_handle else None,
		"can_manage": can_manage_calls(),
		"can_handle": can_handle,
		"can_use_ai_summary": can_use_call_summary(call),
		"can_link": call.handling_status != "Resolved" and can_handle,
	})
	return row


@frappe.whitelist(methods=["GET", "POST"])
def get_record_calls(doctype: str, name: str, start: int = 0):
	_read_customer(doctype, name)
	frappe.has_permission(CALL_LOG, "read", throw=True)
	rows = frappe.get_list(
		CALL_LOG,
		filters={"reference_doctype": doctype, "reference_name": name},
		fields=CALL_SUMMARY_FIELDS,
		order_by="start_time desc, name desc",
		limit_start=max(0, cint(start)),
		limit_page_length=PAGE_SIZE + 1,
	)
	return {
		"rows": [_call_summary(row, {}) for row in rows[:PAGE_SIZE]],
		"has_more": len(rows) > PAGE_SIZE,
	}


@frappe.whitelist(methods=["POST"])
def link_customer(name: str, doctype: str, customer_name: str):
	call = _read_call(name, for_update=True)
	if not can_handle_call(call.assigned_to) or call.handling_status == "Resolved":
		frappe.throw(_("You cannot link a customer to this call."), frappe.PermissionError)
	customer = _read_customer(doctype, customer_name)
	_require_assignee_access(call.assigned_to, doctype, customer.name)
	task = _get_callback(call, for_update=True)
	task_updated = task and (task.reference_doctype, task.reference_docname) != (doctype, customer.name)
	if task_updated:
		task.reference_doctype = doctype
		task.reference_docname = customer.name
		_save_callback(task)
	if (call.reference_doctype, call.reference_name) != (doctype, customer.name):
		call.reference_doctype = doctype
		call.reference_name = customer.name
		_event(call, "Customer linked")
		_save_case(call)
	elif task_updated:
		_publish_case_change(call)
	return _call_details(call, task)


def _user_label(user):
	if not user:
		return None
	return frappe.get_cached_value("User", user, "full_name") or user


def _require_handler(call):
	if not can_handle_call(call.assigned_to):
		frappe.throw(_("You cannot update this case."), frappe.PermissionError)


def _require_open(call):
	_require_handler(call)
	if call.handling_status not in HANDLING_STATUSES[:2]:
		frappe.throw(_("This case is outside the open queue."))


def _save_case(call, previous_assignee=None):
	# Case operations check the actor, record and requested transition before saving.
	call.flags.call_case_workflow = True
	call.save(ignore_permissions=True, ignore_version=True)
	_publish_case_change(call, previous_assignee)


def _publish_case_change(call, previous_assignee=None):
	managers = frappe.get_all(
		"Has Role",
		filters={"parenttype": "User", "role": ["in", sorted(CALL_MANAGER_ROLES)]},
		pluck="parent",
	)
	recipients = set(managers) | {"Administrator", call.assigned_to, previous_assignee}
	for user in recipients - {None, ""}:
		# The former handler needs an invalidation to drop this case from open views.
		if user == previous_assignee or frappe.has_permission(CALL_LOG, "read", doc=call, user=user):
			frappe.publish_realtime(
				"doublet_calls_changed", message={"name": call.name}, user=user, after_commit=True,
			)


def _event(call, action, **fields):
	frappe.get_doc({
		"doctype": CALL_EVENT,
		"call_log": call.name,
		"action": action,
		"actor": frappe.session.user,
		"occurred_at": now_datetime(),
		**fields,
	}).insert(ignore_permissions=True)


def _history(call):
	events = frappe.get_list(
		CALL_EVENT,
		filters={"call_log": call.name},
		fields=["name", *EVENT_FIELDS],
		order_by="occurred_at desc, creation desc, name desc",
		limit_page_length=0,
	)
	for event in events:
		event.update({
			"actor_label": _user_label(event.actor),
			"previous_label": _user_label(event.previous_assignee),
			"new_label": _user_label(event.new_assignee),
		})
	return events


def _require_assignee_access(assignee, doctype, name):
	if assignee and name and not frappe.has_permission(doctype, "read", doc=name, user=assignee):
		frappe.throw(_("The assignee must have read access to the linked customer."))


def _queue_rows(filters, start, limit, *, or_filters=None):
	return frappe.get_list(
		CALL_LOG, filters=filters, or_filters=or_filters,
		fields=[*CALL_SUMMARY_FIELDS, "external_call_id"], order_by=QUEUE_ORDER,
		limit_start=start, limit_page_length=limit,
	)


def _matches_search(row, customer, term, number):
	values = (row.name, row.from_number, row.to_number, row.external_call_id)
	if customer:
		values += (customer.label, customer.phone)
	if any(term in cstr(value).casefold() for value in values):
		return True
	return bool(number and (
		number in (row.from_number, row.to_number)
		or (customer and number == normalize_phone_number(customer.phone))
	))


def _search_call_page(filters, term, start):
	# Both ID columns are indexed. An exact ID can go straight to a visible call.
	exact = _queue_rows(
		filters, 0, 2, or_filters=[["name", "=", term], ["external_call_id", "=", term]],
	)
	if exact:
		page = exact[start:]
		return page, _customer_links(page), None

	# Only look up profiles referenced by this bounded window of visible Calls.
	# Use the inspected Call offset even when there are no matches in the window.
	window = _queue_rows(filters, start, SEARCH_SCAN_LIMIT + 1)
	candidates = window[:SEARCH_SCAN_LIMIT]
	customers = _customer_links(candidates, with_phone=True)
	number = normalize_phone_number(term)
	term = term.casefold()
	page = []
	inspected = 0
	for inspected, row in enumerate(candidates, 1):
		customer = customers.get((row.reference_doctype, row.reference_name))
		if _matches_search(row, customer, term, number):
			page.append(row)
			if len(page) == PAGE_SIZE:
				break
	return page, customers, start + inspected if inspected < len(window) else None


def _queue_counts(filters):
	rows = frappe.get_list(
		CALL_LOG, filters={**filters, "handling_status": ["in", HANDLING_STATUSES]},
		fields=["handling_status", "count(*) as total"], group_by="handling_status",
		order_by="handling_status", limit_page_length=len(HANDLING_STATUSES),
	)
	return {row.handling_status: cint(row.total) for row in rows}


@frappe.whitelist(methods=["GET", "POST"])
def get_calls(
	scope: str | None = None,
	handling_status: str | None = None,
	call_type: str | None = None,
	search: str | None = None,
	start: int = 0,
):
	frappe.has_permission(CALL_LOG, "read", throw=True)
	can_manage = can_manage_calls()
	scope = scope or ("all" if can_manage else "mine")
	if scope not in ("all", "mine", "unassigned"):
		frappe.throw(_("Invalid call queue scope."))
	if scope != "mine" and not can_manage:
		frappe.throw(_("This call queue is outside your access."), frappe.PermissionError)
	if handling_status and handling_status not in HANDLING_STATUSES:
		frappe.throw(_("Invalid handling status."))
	if call_type and call_type not in CALL_LOG_TYPES:
		frappe.throw(_("Invalid call type."))

	filters = {}
	if scope == "mine":
		filters["assigned_to"] = frappe.session.user
	elif scope == "unassigned":
		filters["assigned_to"] = ["is", "not set"]
	if call_type:
		filters["call_type"] = call_type
	status_filters = {**filters, "handling_status": handling_status or ["in", HANDLING_STATUSES[:2]]}
	offset = max(0, cint(start))
	term = " ".join(cstr(search).strip()[:100].split())
	if term:
		page, customers, next_start = _search_call_page(status_filters, term, offset)
	else:
		rows = _queue_rows(status_filters, offset, PAGE_SIZE + 1)
		page = rows[:PAGE_SIZE]
		customers = _customer_links(page)
		next_start = offset + PAGE_SIZE if len(rows) > PAGE_SIZE else None

	return {
		"rows": [_call_summary(row, customers) for row in page],
		"has_more": next_start is not None,
		"next_start": next_start,
		"can_manage": can_manage,
		"counts": _queue_counts(filters) if offset == 0 else None,
	}


@frappe.whitelist(methods=["POST"])
def assign_call(name: str, assignee: str | None = None):
	call = _read_call(name, for_update=True)
	if not can_manage_calls():
		frappe.throw(_("Only a manager can assign this case."), frappe.PermissionError)
	_require_open(call)
	assignee = cstr(assignee).strip() or None
	task = _get_callback(call, for_update=True)
	if assignee == (call.assigned_to or None):
		return _call_details(call, task)

	if assignee:
		if assignee not in _assignable_user_names() or not frappe.db.exists("User", {
			"name": assignee, "enabled": 1, "user_type": "System User",
		}):
			frappe.throw(_("Select an active CRM user."))
		_require_assignee_access(assignee, call.reference_doctype, call.reference_name)
	elif call.handling_status != "Waiting":
		frappe.throw(_("An in-progress case needs an assignee."))

	previous = call.assigned_to
	_event(call, "Assignment changed", previous_assignee=previous, new_assignee=assignee)
	call.assigned_to = assignee
	if task:
		task.assigned_to = assignee
		_save_callback(task)
	_save_case(call, previous_assignee=previous)
	return _call_details(call, task)


@frappe.whitelist(methods=["POST"])
def start_call(name: str):
	call = _read_call(name, for_update=True)
	_require_open(call)
	if not call.assigned_to:
		frappe.throw(_("Assign this case before starting it."))
	if _mark_started(call):
		_save_case(call)
	return _call_details(call, _get_callback(call, for_update=True))


def _mark_started(call):
	if call.handling_status != "Waiting":
		return False
	call.handling_status = "In Progress"
	_event(call, "Started")
	return True


def _get_callback(call, *, for_update=False):
	name = frappe.db.get_value(
		TASK, {"callback_call_log": call.name}, "name", for_update=for_update,
	)
	return frappe.get_doc(TASK, name, for_update=for_update) if name else None


def _save_callback(task):
	task.flags.call_case_workflow = True
	task.save(ignore_permissions=True, ignore_version=True)
	task.flags.ignore_permissions = False


def _callback_summary(task):
	if not task or not task.has_permission("read"):
		return None
	summary = {
		field: task.get(field)
		for field in ("name", "status", "assigned_to", "callback_result", "callback_notes")
	}
	summary["due_date"] = getdate(task.due_date).isoformat() if task.due_date else None
	return summary


@frappe.whitelist(methods=["POST"])
def open_callback(name: str, due_date: str | None = None):
	# All callback operations lock the Call Log first. The unique Task link also
	# protects the one-task invariant at the database level.
	call = _read_call(name, for_update=True)
	_require_handler(call)
	if not is_missed_incoming(call):
		frappe.throw(_("Callback tasks are available for missed incoming calls."))
	task = _get_callback(call, for_update=True)
	if task and (task.status in OPEN_TASK_STATUSES or call.handling_status == "Resolved"):
		return _call_details(call, task)

	_require_open(call)
	if not call.assigned_to:
		frappe.throw(_("Assign this case before opening a callback task."))
	if not task:
		task = frappe.new_doc(TASK)
		task.title = _("Return missed call")
		task.priority = "High"
		task.callback_call_log = call.name

	if due_date or not task.due_date:
		try:
			due_day = date.fromisoformat(due_date) if due_date else getdate()
		except (TypeError, ValueError):
			frappe.throw(_("Choose a valid callback due date."))
		if not task.due_date or getdate(task.due_date) != due_day:
			task.due_date = datetime.combine(due_day, time(23, 59, 59))
	task.status = "In Progress"
	task.assigned_to = call.assigned_to
	task.reference_doctype = call.reference_doctype
	task.reference_docname = call.reference_name
	_save_callback(task)
	_mark_started(call)
	_event(call, "Callback task opened")
	_save_case(call)
	return _call_details(call, task)


@frappe.whitelist(methods=["POST"])
def record_callback_result(name: str, outcome: str, notes: str | None = None):
	call = _read_call(name, for_update=True)
	_require_open(call)
	task = _get_callback(call, for_update=True)
	if not task or task.status not in OPEN_TASK_STATUSES:
		frappe.throw(_("Open the callback task before saving an outcome."))
	if outcome not in CALLBACK_RESULTS:
		frappe.throw(_("Select a callback outcome."))
	notes = cstr(notes).strip()
	if len(notes) > 2000:
		frappe.throw(_("Callback notes must be 2000 characters or fewer."))

	task.callback_result = outcome
	task.callback_notes = notes
	_save_callback(task)
	_event(call, "Callback result", details=f"{outcome}\n{notes}".strip())
	_save_case(call)
	return _call_details(call, task)


@frappe.whitelist(methods=["POST"])
def resolve_call(name: str):
	call = _read_call(name, for_update=True)
	_require_handler(call)
	task = _get_callback(call, for_update=True)
	if call.handling_status == "Resolved":
		return _call_details(call, task)
	if call.handling_status != "In Progress":
		frappe.throw(_("Start the case before closing it."))
	if is_missed_incoming(call):
		if call.reference_doctype not in ALLOWED_REFERENCE_DOCTYPES or not call.reference_name:
			frappe.throw(_("Link a Lead or Contact before resolving this missed call."))
		customer = _read_customer(call.reference_doctype, call.reference_name)
		_require_assignee_access(call.assigned_to, customer.doctype, customer.name)
		if not task or task.status not in OPEN_TASK_STATUSES or task.callback_result != "Reached":
			frappe.throw(_("Record a successful callback before closing the case."))
		if (task.reference_doctype, task.reference_docname) != (customer.doctype, customer.name):
			frappe.throw(_("Confirm the linked customer before resolving this missed call."))
		task.status = "Done"
		_save_callback(task)

	call.handling_status = "Resolved"
	_event(call, "Resolved")
	_save_case(call)
	return _call_details(call, task)
