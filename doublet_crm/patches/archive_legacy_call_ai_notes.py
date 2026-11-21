"""Separate legacy AI blocks and preserve handwritten Call Log notes and Versions."""

import json
import re
from collections import defaultdict

import frappe

from doublet_crm.call_log.ai_summary import SUMMARY
from doublet_crm.patches.protect_call_case_history import CALL_EVENT, CALL_LOG, _archive_revision

SEPARATOR = "\n\n---\n"
NOTE_SEPARATOR = re.compile(r"(\r?\n\r?\n---\r?\n)")
AI_HEADER = re.compile(r"\[(?:AI Tóm tắt|Next Step)\]\r?\n")
FIRST_AI_BLOCK = re.compile(r"(?:\A|\r?\n\r?\n---\r?\n)(?=" + AI_HEADER.pattern + r")")


def _blocks(note):
	parts = NOTE_SEPARATOR.split(note or "")
	return zip(["", *parts[1::2]], parts[::2])


def _join(blocks):
	return "".join((sep if index else "") + text for index, (sep, text) in enumerate(blocks))


def _split_note(note):
	public, archived = [], []
	for sep, text in _blocks(note):
		destination = archived if AI_HEADER.match(text) else public
		destination.append((sep, text))
	return (_join(public), _join(archived)) if archived else (note, None)


def _note_change(data):
	return next((entry for entry in (data.get("changed") or ()) if len(entry) == 3 and entry[0] == "note"), None)


def _record_manual_append(known, old, new):
	# Legacy AI wrote via db_set, so an append recorded in a Version can identify
	# handwritten text even when the author did not use the old separator.
	if not isinstance(old, str) or not isinstance(new, str) or not new.startswith(old):
		return
	tail = new[len(old):]
	if not tail.startswith(("\n", "\r\n")) or NOTE_SEPARATOR.match(tail) or not tail.strip():
		return
	if _split_note(tail.lstrip("\r\n"))[1]:
		return
	public, archived = known.get(old, _split_note(old))
	if archived and _split_note(new)[0] == _split_note(old)[0]:
		known[new] = (public + tail if public else tail.lstrip("\r\n"), archived)


def _sanitize_versions():
	archives = {}
	for event in frappe.get_all(
		CALL_EVENT,
		filters={"source_version": ["is", "set"], "revision_data": ["like", '%"note"%']},
		fields=["source_version", "revision_data"],
	):
		original = json.loads(event.revision_data)
		if original.get("ref_doctype") == CALL_LOG:
			archives[event.source_version] = original["data"]

	known = defaultdict(dict)
	for revision in frappe.get_all(
		"Version",
		filters={"ref_doctype": CALL_LOG, "data": ["like", '%"note"%']},
		fields=["name", "docname", "owner", "creation", "data"],
		order_by="creation asc, name asc",
	):
		data = json.loads(revision.data)
		visible_note = _note_change(data)
		original_note = _note_change(archives.get(revision.name, data))
		if not visible_note or not original_note:
			continue
		snapshots = known[revision.docname]
		_record_manual_append(snapshots, *original_note[1:])
		public = [
			snapshots.get(value, _split_note(value))[0] if isinstance(value, str) else value
			for value in original_note[1:]
		]
		if visible_note[1:] != public and frappe.db.exists(CALL_LOG, revision.docname):
			visible_note[1:] = public
			_archive_revision(revision, revision.docname, CALL_LOG, data)
	return known


def _append_missing(existing, additional):
	# Use explicit legacy boundaries and preserve text already on the record.
	present = {text for _sep, text in _blocks(existing)}
	blocks = []
	for sep, text in _blocks(additional):
		if text and text not in present:
			blocks.append((sep, text))
			present.add(text)
	return SEPARATOR.join(filter(None, (existing, _join(blocks))))


def _repair_previous_archives(known):
	for row in frappe.get_all(
		SUMMARY, filters={"legacy_note": ["is", "set"]}, fields=["name", "call_log", "legacy_note"],
	):
		manual, archive = _split_note(row.legacy_note)
		for raw_note, (public_note, ai_note) in known.get(row.call_log, {}).items():
			start = FIRST_AI_BLOCK.search(raw_note)
			if start and raw_note[start.end():] == row.legacy_note:
				prefix = raw_note[:start.start()]
				if public_note.startswith(prefix):
					suffix = public_note[len(prefix):]
					separator = NOTE_SEPARATOR.match(suffix)
					manual = suffix[separator.end():] if separator else suffix.lstrip("\r\n")
					archive = ai_note
					break
		if not manual or not archive or not frappe.db.exists(CALL_LOG, row.call_log):
			continue
		note = frappe.db.get_value(CALL_LOG, row.call_log, "note")
		public_note = _append_missing(note, manual)
		if public_note != note:
			frappe.db.set_value(CALL_LOG, row.call_log, "note", public_note, update_modified=False)
		frappe.db.set_value(SUMMARY, row.name, "legacy_note", archive, update_modified=False)


def execute():
	known = _sanitize_versions()
	_repair_previous_archives(known)

	for row in frappe.get_all(
		CALL_LOG,
		or_filters=[["note", "like", f"%{marker}%"] for marker in ("[AI Tóm tắt]", "[Next Step]")],
		fields=["name", "note"],
	):
		note, legacy = known.get(row.name, {}).get(row.note, _split_note(row.note))
		if not legacy:
			continue
		if frappe.db.exists(SUMMARY, row.name):
			previous = frappe.db.get_value(SUMMARY, row.name, "legacy_note")
			archive = _append_missing(previous, legacy)
			if archive != previous:
				frappe.db.set_value(SUMMARY, row.name, "legacy_note", archive, update_modified=False)
		else:
			frappe.get_doc({"doctype": SUMMARY, "call_log": row.name, "legacy_note": legacy}).insert(
				ignore_permissions=True,
			)
		frappe.db.set_value(CALL_LOG, row.name, "note", note, update_modified=False)
