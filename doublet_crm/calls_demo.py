"""Seed a repeatable Contact Center demo on a developer or test site."""

import hashlib
import io
import json
import math
import struct
import wave
from datetime import timedelta
from pathlib import Path

import frappe
from frappe.utils import add_to_date, get_datetime, now_datetime
from frappe.utils.file_manager import save_file

DEMO_USERS = {
	"manager": ("calls-demo-manager@example.com", "Calls Demo Manager", "Sales Manager"),
	"a": ("calls-demo-a@example.com", "Calls Demo A", "Sales User"),
	"b": ("calls-demo-b@example.com", "Calls Demo B", "Sales User"),
}
RECORDING_NAME = "DEMO - Sample call recording.wav"
LINE = "+12025550100"
MAX_DEMO_RECORDING_BYTES = 25 * 1024 * 1024
MAX_DEMO_MANIFEST_BYTES = 128 * 1024
RECORDING_DEMO_MARKER = "DEMO - Recording and AI Summary sample"
RECORDING_DEMO_MANIFEST_NAME = "DEMO - Call Summary Manifest.json"
RECORDING_DEMOS = (
	(
		"incoming", "Incoming", "Calls Recording Demo Incoming", "+12025550201",
		"DEMO - Incoming consultation.wav",
	),
	(
		"outgoing", "Outgoing", "Calls Recording Demo Outgoing", "+12025550202",
		"DEMO - Outgoing consultation.wav",
	),
)


def is_recording_demo(call):
	return call.note == RECORDING_DEMO_MARKER and any(
		call.external_call_id == f"doublet-recording-demo-{key}" and call.call_type == call_type
		for key, call_type, _label, _number, _filename in RECORDING_DEMOS
	)


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


def seed_recording_demos(
	incoming_wav_path=None,
	outgoing_wav_path=None,
	manifest_path=None,
	preview_only=True,
	confirmation=None,
):
	"""Preview or seed two recordings without exposing a public API.

	First run a read-only preview on the intended site:
	bench --site <site> execute doublet_crm.calls_demo.seed_recording_demos

	The bundled WAVs and manifest are the defaults. Absolute paths can also be supplied.

	After reviewing the preview, repeat with preview_only=false and the exact
	site-specific confirmation returned by the preview. This command requires
	Administrator and is deliberately not whitelisted for HTTP access.
	"""
	if frappe.session.user != "Administrator":
		frappe.throw("Run this command as Administrator with bench execute.", frappe.PermissionError)
	if not isinstance(preview_only, bool):
		frappe.throw("preview_only must be a JSON boolean.")
	site_name = getattr(frappe.local, "site", None)
	if not site_name:
		frappe.throw("The current Frappe site could not be identified. No data was changed.")
	required_confirmation = f"I CONFIRM: seed two recording demos on {site_name}"
	if not preview_only and confirmation != required_confirmation:
		frappe.throw(
			f"To write, pass preview_only=false and confirmation={required_confirmation!r}. "
			"No data was changed."
		)

	bundle = Path(__file__).resolve().parents[1] / "demo_audio" / "DoubleT_Call_Demo_Audio"
	incoming_wav_path = incoming_wav_path or bundle / "DoubleT_Incoming_Demo_VI.wav"
	outgoing_wav_path = outgoing_wav_path or bundle / "DoubleT_Outgoing_Demo_VI.wav"
	manifest_path = manifest_path or bundle / "DoubleT_Call_Demo_Manifest.json"

	# Validate both inputs and all existing demo identifiers before the first write.
	audio_inputs = {
		"incoming": _read_demo_wav(incoming_wav_path),
		"outgoing": _read_demo_wav(outgoing_wav_path),
	}
	incoming_hash = hashlib.md5(audio_inputs["incoming"]["data"], usedforsecurity=False).digest()
	outgoing_hash = hashlib.md5(audio_inputs["outgoing"]["data"], usedforsecurity=False).digest()
	if incoming_hash == outgoing_hash:
		frappe.throw("Supply two different WAV recordings. No data was changed.")
	audio_names = {
		"incoming": Path(incoming_wav_path).name,
		"outgoing": Path(outgoing_wav_path).name,
	}
	demo_samples = _read_demo_manifest(manifest_path, audio_names)

	manager_email, manager_name, _manager_role = DEMO_USERS["manager"]
	manager_exists = frappe.db.exists("User", manager_email)
	if manager_exists:
		manager_user = frappe.get_doc("User", manager_email)
		if (
			manager_user.user_type != "System User"
			or not manager_user.enabled
			or not {"Sales Manager", "System Manager"}.intersection(frappe.get_roles(manager_email))
		):
			frappe.throw(
				"The demo manager account must be an enabled System User with a manager role. "
				"No data was changed."
			)

	now = now_datetime()
	plans = []
	for key, call_type, customer_label, number, _filename in RECORDING_DEMOS:
		external_id = f"doublet-recording-demo-{key}"
		existing_calls = frappe.get_all(
			"DoubleT Call Log", filters={"external_call_id": external_id},
			fields=["name"], limit_page_length=2,
		)
		if len(existing_calls) > 1:
			frappe.throw("Multiple Call Logs use a recording demo ID. No data was changed.")
		call_name = existing_calls[0].name if existing_calls else None

		leads = frappe.get_all(
			"DoubleT Lead", filters={"first_name": customer_label, "phone": number},
			fields=["name"], limit_page_length=2,
		)
		if len(leads) > 1:
			frappe.throw("Multiple Leads match a recording demo identity. No data was changed.")
		customer = leads[0].name if leads else None

		file = None
		manifest_file = None
		expected_recording_hash = hashlib.md5(
			audio_inputs[key]["data"], usedforsecurity=False,
		).hexdigest()
		manifest_bytes = _demo_manifest_bytes(demo_samples[key], expected_recording_hash)
		current_url = ""
		start = add_to_date(now, minutes=-(10 if key == "incoming" else 5))
		old = None
		if call_name:
			old = frappe.get_doc("DoubleT Call Log", call_name)
			matches_demo = (
				old.external_call_id == external_id
				and old.note == RECORDING_DEMO_MARKER
				and old.call_type == call_type
				and customer
				and old.reference_doctype == "DoubleT Lead"
				and old.reference_name == customer
			)
			if not matches_demo:
				frappe.throw(
					"A Call Log already uses a recording demo ID but does not match this demo. "
					"No data was changed."
				)
			if not old.start_time:
				frappe.throw("The verified demo Call Log has no start time. No data was changed.")
			start = old.start_time
			current_url = old.recording_url or ""

			attached_files = frappe.get_all("File", {
				"attached_to_doctype": "DoubleT Call Log",
				"attached_to_name": call_name,
			}, ["name", "file_name", "content_hash", "file_url", "is_private"])
			private_files = [item for item in attached_files if item.is_private]
			if current_url:
				matches = [
					item for item in private_files
					if item.file_url == current_url
					and Path(item.file_name or "").suffix.lower() == ".wav"
				]
				if len(matches) != 1 or matches[0].content_hash != expected_recording_hash:
					frappe.throw(
						"The demo Call Log already points to a different or unavailable recording. "
						"No data was changed."
					)
				file = matches[0]
			else:
				matches = [
					item for item in private_files
					if item.content_hash == expected_recording_hash
					and Path(item.file_name or "").suffix.lower() == ".wav"
				]
				other_audio = [
					item for item in attached_files
					if Path(item.file_name or "").suffix.lower() in {".wav", ".mp3", ".m4a", ".ogg", ".webm"}
					and item.content_hash != expected_recording_hash
				]
				if len(matches) > 1 or other_audio:
					frappe.throw(
						"The demo Call Log has an ambiguous or different audio file. "
						"No data was changed."
					)
				file = matches[0] if matches else None

			if manifest_bytes:
				manifest_matches = [
					item for item in private_files
					if item.file_name.startswith(RECORDING_DEMO_MANIFEST_NAME.removesuffix(".json"))
					and item.file_name.lower().endswith(".json")
				]
				if len(manifest_matches) > 1:
					frappe.throw("The demo Call Log has multiple private manifests. No data was changed.")
				manifest_file = manifest_matches[0] if manifest_matches else None
				manifest_hash = hashlib.md5(manifest_bytes, usedforsecurity=False).hexdigest()
				if manifest_file and manifest_file.content_hash != manifest_hash:
					frappe.throw(
						"The demo Call Log already has a different private manifest. "
						"No data was changed."
					)

		duration = audio_inputs[key]["duration_seconds"]
		end = get_datetime(start) + timedelta(seconds=audio_inputs[key]["exact_duration_seconds"])
		metadata_update = bool(
			old and (
				int(old.duration or 0) != duration
				or not old.end_time
				or get_datetime(old.end_time) != end
			)
		)
		plans.append({
			"key": key,
			"call_type": call_type,
			"customer_label": customer_label,
			"number": number,
			"filename": audio_names[key],
			"external_id": external_id,
			"call_name": call_name,
			"customer": customer,
			"file": file,
			"current_url": current_url,
			"manifest_file": manifest_file,
			"manifest_bytes": manifest_bytes,
			"start_time": start,
			"end_time": end,
			"duration_seconds": duration,
			"wav_duration_seconds": audio_inputs[key]["exact_duration_seconds"],
			"metadata_update": metadata_update,
		})

	preview = {
		"site": site_name,
		"writes_performed": False,
		"confirmation_required": required_confirmation,
		"calls": {
			plan["key"]: {
				"action": "Update verified demo metadata" if plan["call_name"] and plan["metadata_update"]
				else "Reuse verified demo" if plan["call_name"] else "Create demo",
				"call_log": plan["call_name"],
				"lead": plan["customer"] or "Create demo Lead",
				"duration_seconds": plan["duration_seconds"],
				"wav_duration_seconds": round(plan["wav_duration_seconds"], 3),
				"start_time": str(plan["start_time"]),
				"end_time": str(plan["end_time"]),
				"audio_action": "Reuse matching private WAV" if plan["file"] else "Attach private WAV",
				"manifest_action": "Reuse matching private manifest" if plan["manifest_file"] else "Attach private manifest",
			}
			for plan in plans
		},
	}
	if preview_only:
		return {"mode": "PREVIEW", **preview}

	# All identity, file, confirmation, and WAV checks have passed before this point.
	manager = _user(manager_email, manager_name, "Sales Manager")
	result = {}
	for plan in plans:
		key = plan["key"]
		customer = plan["customer"] or _customer(
			"DoubleT Lead", plan["customer_label"], plan["number"],
		)
		call_name = plan["call_name"]
		if not call_name:
			if plan["call_type"] == "Incoming":
				from_number, to_number = plan["number"], LINE
			else:
				from_number, to_number = LINE, plan["number"]
			call_name = frappe.get_doc({
				"doctype": "DoubleT Call Log",
				"agent": manager,
				"call_type": plan["call_type"],
				"status": "Completed",
				"start_time": plan["start_time"],
				"end_time": plan["end_time"],
				"duration": plan["duration_seconds"],
				"from_number": from_number,
				"to_number": to_number,
				"reference_doctype": "DoubleT Lead",
				"reference_name": customer,
				"external_call_id": plan["external_id"],
				"note": RECORDING_DEMO_MARKER,
			}).insert().name
		elif plan["metadata_update"]:
			frappe.db.set_value("DoubleT Call Log", call_name, {
				"duration": plan["duration_seconds"],
				"end_time": plan["end_time"],
			}, update_modified=False)

		file = plan["file"]
		if not file:
			file = save_file(
				plan["filename"], audio_inputs[key]["data"],
				"DoubleT Call Log", call_name, is_private=1,
			)
		if not plan["current_url"]:
			frappe.db.set_value(
				"DoubleT Call Log", call_name, "recording_url",
				file.file_url, update_modified=False,
			)
		manifest_file = plan["manifest_file"]
		if not manifest_file:
			manifest_file = save_file(
				RECORDING_DEMO_MANIFEST_NAME, plan["manifest_bytes"],
				"DoubleT Call Log", call_name, is_private=1,
			)
		result[key] = {
			"call_log": call_name,
			"file": file.name,
			"is_private": True,
			"manifest_file": manifest_file.name if manifest_file else None,
			"duration_seconds": plan["duration_seconds"],
			"wav_duration_seconds": round(plan["wav_duration_seconds"], 3),
			"metadata_updated": plan["metadata_update"],
		}
	return result


def _read_demo_manifest(path, audio_names):
	try:
		raw = Path(path).expanduser().resolve(strict=True).read_bytes()
		if not raw or len(raw) > MAX_DEMO_MANIFEST_BYTES:
			raise ValueError("empty or oversized manifest")
		manifest = json.loads(raw)
	except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
		frappe.throw("The demo manifest must be a readable JSON file under 128 KB. No data was changed.")

	notice = manifest.get("notice") if isinstance(manifest, dict) else None
	if not isinstance(notice, str) or "DEMO / MOCK DATA" not in notice or "NOT generated by BeeKnoee AI" not in notice:
		frappe.throw("The manifest must clearly identify content as mock data. No data was changed.")
	entries = manifest.get("calls")
	if not isinstance(entries, list) or len(entries) != len(RECORDING_DEMOS):
		frappe.throw("The manifest must describe exactly the Incoming and Outgoing demo calls. No data was changed.")

	expected_audio = {"Incoming": audio_names["incoming"], "Outgoing": audio_names["outgoing"]}
	samples = {}
	for entry in entries:
		if not isinstance(entry, dict):
			frappe.throw("Invalid demo manifest entry. No data was changed.")
		call_type = entry.get("call_type")
		key = {"Incoming": "incoming", "Outgoing": "outgoing"}.get(call_type) if isinstance(call_type, str) else None
		needs = entry.get("customer_needs_demo")
		next_steps = entry.get("next_steps_demo")
		transcript = entry.get("transcript_demo")
		summary = entry.get("summary_demo")
		if (
			not key or key in samples
			or entry.get("audio_file") != expected_audio[call_type]
			or not isinstance(transcript, str) or not transcript.strip() or len(transcript) > 50000
			or not isinstance(summary, str) or not summary.strip() or len(summary) > 10000
			or not isinstance(needs, list) or len(needs) > 50
			or not isinstance(next_steps, list) or len(next_steps) > 50
			or any(not isinstance(item, str) or len(item) > 2000 for item in needs + next_steps)
		):
			frappe.throw("The manifest does not match the supplied call recordings. No data was changed.")
		samples[key] = {
			"notice": notice,
			"transcript_demo": transcript,
			"summary_demo": summary,
			"customer_needs_demo": needs,
			"next_steps_demo": next_steps,
			"audio_file": entry["audio_file"],
		}
	if set(samples) != {"incoming", "outgoing"}:
		frappe.throw("The manifest must include one Incoming and one Outgoing call. No data was changed.")
	return samples


def _demo_manifest_bytes(sample, recording_hash):
	return json.dumps({
		"mode": "DEMO",
		"recording_content_hash": recording_hash,
		"sample": sample,
	}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _read_demo_wav(path):
	try:
		with Path(path).expanduser().resolve(strict=True).open("rb") as stream:
			data = stream.read(MAX_DEMO_RECORDING_BYTES + 1)
		if len(data) > MAX_DEMO_RECORDING_BYTES:
			frappe.throw("Each demo WAV must be 25 MB or smaller. No data was changed.")
		with wave.open(io.BytesIO(data), "rb") as audio:
			frames = audio.getnframes()
			rate = audio.getframerate()
			frame_size = audio.getnchannels() * audio.getsampwidth()
			if frames <= 0 or rate <= 0 or frame_size <= 0 or len(audio.readframes(frames)) != frames * frame_size:
				raise ValueError("incomplete audio")
			exact_duration = frames / rate
			duration_seconds = int(math.floor(exact_duration + 0.5))
	except (OSError, EOFError, TypeError, ValueError, wave.Error):
		frappe.throw("Both supplied demo recordings must be readable, non-empty WAV files. No data was changed.")
	return {
		"data": data,
		"duration_seconds": duration_seconds,
		"exact_duration_seconds": exact_duration,
	}


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
