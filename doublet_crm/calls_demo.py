"""Seed a repeatable Contact Center demo on a developer or test site."""

import io
import math
import struct
import wave

import frappe
from frappe.utils import add_to_date, now_datetime
from frappe.utils.file_manager import save_file

DEMO_USERS = {
	"manager": ("calls-demo-manager@example.com", "Calls Demo Manager", "Sales Manager"),
	"a": ("calls-demo-a@example.com", "Calls Demo A", "Sales User"),
	"b": ("calls-demo-b@example.com", "Calls Demo B", "Sales User"),
}
RECORDING_NAME = "DEMO - Sample call recording.wav"
LINE = "+12025550100"


def seed():
	if not (frappe.conf.developer_mode or frappe.conf.allow_tests):
		frappe.throw("Run this demo on a developer or test site.")
	if frappe.session.user != "Administrator":
		frappe.throw("Run this demo with bench execute.", frappe.PermissionError)

	users = {key: _user(*values) for key, values in DEMO_USERS.items()}
	lead = _customer("DoubleT Lead", "Calls Demo Lead", "+12025550101")
	contact = _customer("DoubleT Contact", "Calls Demo Contact", "+12025550102")
	now = now_datetime()
	calls = {}
	for key, call_type, status, number, minutes, duration in (
		("incoming", "Incoming", "Completed", "+12025550101", 30, 42),
		("outgoing", "Outgoing", "Completed", "+12025550102", 20, 27),
		("missed", "Incoming", "Missed", "+12025550103", 10, 0),
	):
		external_id = f"doublet-calls-demo-{key}"
		name = frappe.db.get_value("DoubleT Call Log", {"external_call_id": external_id}, "name")
		if not name:
			start = add_to_date(now, minutes=-minutes)
			from_number, to_number = (LINE, number) if call_type == "Outgoing" else (number, LINE)
			name = frappe.get_doc({
				"doctype": "DoubleT Call Log",
				"agent": users["manager"],
				"call_type": call_type,
				"status": status,
				"start_time": start,
				"end_time": add_to_date(start, seconds=duration),
				"duration": duration,
				"from_number": from_number,
				"to_number": to_number,
				"external_call_id": external_id,
				"note": "DEMO - Simulated call",
			}).insert().name
		if not frappe.db.get_value("DoubleT Call Log", name, "handling_status"):
			# Seeded calls represent new work even when a demo log predates the queue.
			frappe.db.set_value("DoubleT Call Log", name, "handling_status", "Waiting", update_modified=False)
		calls[key] = name

	if not frappe.db.exists("File", {
		"attached_to_doctype": "DoubleT Call Log", "attached_to_name": calls["incoming"],
		"file_name": RECORDING_NAME, "is_private": 1,
	}):
		save_file(RECORDING_NAME, _recording(), "DoubleT Call Log", calls["incoming"], is_private=1)

	return {"calls": calls, "lead": lead, "contact": contact, "users": users}


def _user(email, first_name, role):
	if not frappe.db.exists("User", email):
		frappe.get_doc({
			"doctype": "User",
			"email": email,
			"first_name": first_name,
			"user_type": "System User",
			"send_welcome_email": 0,
			"roles": [{"role": role}],
		}).insert()
	return email


def _customer(doctype, first_name, phone):
	return frappe.db.get_value(doctype, {"first_name": first_name, "phone": phone}, "name") or (
		frappe.get_doc({"doctype": doctype, "first_name": first_name, "phone": phone}).insert().name
	)


def _recording():
	buffer = io.BytesIO()
	rate = 8000
	with wave.open(buffer, "wb") as audio:
		audio.setparams((1, 2, rate, 0, "NONE", "not compressed"))
		for frequency in (440, 0, 620):
			frames = (
				int(3500 * math.sin(2 * math.pi * frequency * frame / rate))
				for frame in range(rate // 3)
			)
			audio.writeframes(b"".join(struct.pack("<h", frame) for frame in frames))
	return buffer.getvalue()
