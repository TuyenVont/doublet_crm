import json
import os
from datetime import timedelta
from unittest.mock import Mock, patch

import frappe
from frappe.client import get as client_get
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime
from frappe.utils.file_manager import save_file

from doublet_crm import contact_center_calls as calls
from doublet_crm.api import get_linked_notes
from doublet_crm.call_log import ai_summary as ai
from doublet_crm.calls_demo import (
	RECORDING_DEMO_MANIFEST_NAME, RECORDING_DEMO_MARKER, _demo_manifest_bytes, _recording, _user,
)
from doublet_crm.patches import archive_legacy_call_ai_notes, recover_legacy_call_ai_notes

CONFIG = ai.BeeKnoeeConfig(
	base_url="https://platform.beeknoee.com/api/v1",
	api_key="test-key",
	stt_model="whisper-large-v3-turbo",
	llm_model="openai/gpt-oss-120b",
)
TRANSCRIPT = "Khách hỏi thời gian giao hàng. Nhân viên sẽ gửi lịch dự kiến vào thứ Sáu."
ANALYSIS = {
	"summary": "Khách hỏi về lịch giao hàng.",
	"customer_needs": ["Cần biết thời gian giao hàng."],
	"next_step": ["Nhân viên gửi lịch dự kiến vào thứ Sáu."],
}


def response(data, status=200):
	return Mock(status_code=status, json=Mock(return_value=data))


def chat_response():
	return response({"choices": [{"message": {"content": json.dumps(ANALYSIS)}}]})


class TestDoubleTCallAISummary(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.unique = frappe.generate_hash(length=10)
		self.config = patch.object(ai, "_get_ai_config", return_value=CONFIG)
		self.queue = patch.object(frappe, "enqueue")
		self.key = self.config.start()
		self.job = self.queue.start()
		budget = patch.object(ai, "_consume_generation_budget")
		self.budget = budget.start()
		self.addCleanup(budget.stop)
		self.addCleanup(self.config.stop)
		self.addCleanup(self.queue.stop)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def user(self, key, role="Sales User"):
		return _user(f"call-ai-{key}-{self.unique}@example.com", f"Call AI {key}", role)

	def call(self, *, agent="Administrator", url=None, **values):
		return frappe.get_doc({
			"doctype": calls.CALL_LOG, "agent": agent, "call_type": "Incoming", "status": "Completed",
			"start_time": now_datetime(), "note": "Original call note.", "recording_url": url,
			**values,
		}).insert()

	def attach(self, call, key="main", audio=None):
		if audio is None:
			audio = _recording() + f"{self.unique}-{key}".encode()
		file = save_file(f"AI {self.unique}-{key}.wav", audio, call.doctype, call.name, is_private=1)
		return file, audio

	def past_cooldown(self, name):
		frappe.db.set_value(
			ai.SUMMARY, name, "requested_at",
			now_datetime() - timedelta(seconds=ai.CALL_COOLDOWN_SECONDS + 1),
		)

	def run_job(self, *responses):
		# Keep the worker's transaction boundaries inside this test's transaction.
		with (
			patch.object(frappe.db, "commit"),
			patch.object(frappe.db, "rollback"),
			patch.object(ai.requests, "post", side_effect=responses) as send,
		):
			args = self.job.call_args.kwargs
			ai._process_call_summary(args["call_log_name"], args["request_id"], args["source_key"])
		return send

	def test_manual_generation_persists_and_repeated_requests_share_the_pending_job(self):
		log = self.call()
		_, audio = self.attach(log)
		self.job.reset_mock()
		self.assertEqual(ai.get_call_summary(log.name)["status"], "Idle")
		self.job.assert_not_called()
		self.assertEqual(ai.summarize_call(log.name)["status"], "Queued")
		self.assertEqual(ai.summarize_call(log.name, regenerate=True)["status"], "Queued")
		self.job.assert_called_once()
		self.budget.assert_called_once()
		self.assertTrue(self.job.call_args.kwargs["enqueue_after_commit"])
		posts = self.run_job(response({"text": TRANSCRIPT}), chat_response())
		self.assertEqual(posts.call_count, 2)
		stt, summary = posts.call_args_list
		self.assertEqual(stt.args[0], ai.BEEKNOEE_BASE_URL + "/audio/transcriptions")
		self.assertEqual(stt.kwargs["files"]["file"][1], audio)
		self.assertEqual(stt.kwargs["data"]["model"], CONFIG.stt_model)
		self.assertFalse(stt.kwargs["allow_redirects"])
		self.assertEqual(summary.args[0], ai.BEEKNOEE_BASE_URL + "/chat/completions")
		self.assertEqual(summary.kwargs["json"]["messages"][-1]["content"], TRANSCRIPT)
		view = ai.get_call_summary(log.name)
		self.assertEqual(view["status"], "Ready")
		self.assertEqual(view["result"]["transcript"], TRANSCRIPT)
		self.assertEqual(view["result"]["summary"], ANALYSIS["summary"])
		self.assertEqual(view["result"]["customer_needs"], ANALYSIS["customer_needs"])
		self.assertEqual(view["result"]["next_steps"], ANALYSIS["next_step"])
		self.assertEqual(frappe.db.count(ai.SUMMARY, {"call_log": log.name}), 1)
		self.assertEqual(frappe.db.get_value(calls.CALL_LOG, log.name, "note"), "Original call note.")
		self.assertFalse(frappe.db.exists("Version", {"ref_doctype": ai.SUMMARY, "docname": log.name}))
		self.assertEqual(ai.summarize_call(log.name)["status"], "Ready")
		self.job.assert_called_once()

	def test_marked_demo_uses_only_the_private_manifest_and_never_queues(self):
		log = self.call()
		recording, _ = self.attach(log)
		log.external_call_id = "doublet-recording-demo-incoming"
		log.note = RECORDING_DEMO_MARKER
		sample = {
			"notice": "DEMO / MOCK DATA; NOT generated by BeeKnoee AI",
			"transcript_demo": "Demo transcript",
			"summary_demo": "Demo summary",
			"customer_needs_demo": [],
			"next_steps_demo": [],
		}
		save_file(
			RECORDING_DEMO_MANIFEST_NAME, _demo_manifest_bytes(sample, recording.content_hash),
			log.doctype, log.name, is_private=1,
		)
		with patch.object(ai, "_authorized_call", return_value=log):
			view = ai.get_call_summary(log.name)
			self.assertTrue(view["demo_only"])
			self.assertIsNone(view["provider"])
			self.assertIsNone(view["result"])
			self.assertEqual(view["demo_sample"]["transcript"], sample["transcript_demo"])
			with self.assertRaises(frappe.ValidationError):
				ai.summarize_call(log.name, regenerate=True)
		self.job.assert_not_called()
		self.key.assert_not_called()
		self.assertFalse(frappe.db.exists(ai.SUMMARY, log.name))

	def test_demo_next_steps_create_and_update_one_note_on_explicit_save(self):
		lead = frappe.get_doc({"doctype": "DoubleT Lead", "first_name": f"Demo customer {self.unique}"}).insert()
		log = self.call(reference_doctype=lead.doctype, reference_name=lead.name)
		recording, _ = self.attach(log)
		sample = {
			"notice": "DEMO / MOCK DATA; NOT generated by BeeKnoee AI",
			"transcript_demo": "Demo transcript",
			"summary_demo": "Demo summary",
			"customer_needs_demo": [],
			"next_steps_demo": ["Follow up"],
		}
		save_file(RECORDING_DEMO_MANIFEST_NAME, _demo_manifest_bytes(sample, recording.content_hash),
			log.doctype, log.name, is_private=1)
		with patch.object(ai, "is_recording_demo", return_value=True):
			before = ai.get_call_summary(log.name)
			self.assertTrue(before["next_steps_note"]["can_save"])
			self.assertFalse(frappe.db.exists(ai.NOTE, {"source_call_log": log.name}))
			content = "Call back <reviewed> & confirm"
			saved = ai.save_next_steps(log.name, content)
			self.assertEqual(ai.save_next_steps(log.name, content), saved)
			updated = ai.save_next_steps(log.name, "Send revised quote\nConfirm date", saved["version"])
			self.assertNotEqual(updated["version"], saved["version"])
			with self.assertRaises(frappe.ValidationError):
				ai.save_next_steps(log.name, "Stale edit", saved["version"])
			self.assertEqual(ai.get_call_summary(log.name)["next_steps_note"]["content"], updated["content"])
			rows = get_linked_notes(lead.doctype, lead.name)
			self.assertEqual(len(rows), 1)
			note = frappe.get_doc(ai.NOTE, rows[0].name)
			self.assertEqual(note.source_call_log, log.name)
			self.assertEqual(note.content, "<ul><li>Send revised quote</li><li>Confirm date</li></ul>")
			self.assertIn("DEMO", note.title)
			self.assertEqual(frappe.db.count(ai.NOTE, {"source_call_log": log.name}), 1)
		self.job.assert_not_called()
		self.key.assert_not_called()
		self.assertFalse(frappe.db.exists(ai.SUMMARY, log.name))

	def test_generated_next_steps_require_current_recording_and_keep_the_saved_customer(self):
		contact = frappe.get_doc({"doctype": "DoubleT Contact", "first_name": f"Contact {self.unique}"}).insert()
		other = frappe.get_doc({"doctype": "DoubleT Contact", "first_name": f"Other {self.unique}"}).insert()
		log = self.call(reference_doctype=contact.doctype, reference_name=contact.name)
		self.attach(log)
		with self.assertRaises(frappe.ValidationError):
			ai.save_next_steps(log.name, "Missing summary")
		ai.summarize_call(log.name)
		self.run_job(response({"text": TRANSCRIPT}), chat_response())
		saved = ai.save_next_steps(log.name, "<review> & confirm")
		note = frappe.get_doc(ai.NOTE, {"source_call_log": log.name})
		self.assertEqual(note.content, "<ul><li>&lt;review&gt; &amp; confirm</li></ul>")
		self.assertEqual(ai.get_call_summary(log.name)["result"]["next_steps"], ANALYSIS["next_step"])
		note.reference_name = other.name
		with self.assertRaises(frappe.ValidationError):
			note.save()
		new_recording, _ = self.attach(log, "replacement")
		frappe.db.set_value(log.doctype, log.name, "recording_url", new_recording.file_url)
		with self.assertRaises(frappe.ValidationError):
			ai.save_next_steps(log.name, "Stale recording", saved["version"])
		frappe.db.set_value(log.doctype, log.name, "reference_name", other.name)
		with self.assertRaises(frappe.PermissionError):
			ai.save_next_steps(log.name, "Do not publish to a different customer", saved["version"])
		self.assertEqual(frappe.db.get_value(ai.NOTE, note.name, "reference_name"), contact.name)

	def test_next_steps_cannot_bypass_notes_permissions(self):
		sales = self.user("next-steps")
		contact = frappe.get_doc({"doctype": "DoubleT Contact", "first_name": f"Contact {self.unique}"}).insert()
		log = self.call(agent=sales, reference_doctype=contact.doctype, reference_name=contact.name)
		frappe.set_user(sales)
		self.assertTrue(calls.get_call(log.name)["can_use_ai_summary"])
		with self.assertRaises(frappe.PermissionError):
			ai.save_next_steps(log.name, "Denied")
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			ai.save_next_steps(log.name, "Denied")
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists(ai.NOTE, {"source_call_log": log.name}))

	def test_no_configuration_or_unavailable_recording_never_queues(self):
		valid = self.call()
		self.attach(valid)
		missing = self.call(url=f"/private/files/missing-{self.unique}.wav")
		unselected = self.call()
		self.attach(unselected, "first")
		self.attach(unselected, "second")
		legacy = self.call(url="https://example.invalid/legacy.wav")
		self.job.reset_mock()
		self.key.return_value = None
		view = ai.get_call_summary(valid.name)
		self.assertEqual(view["recording_state"], "Available")
		self.assertFalse(view["configured"])
		with self.assertRaisesRegex(frappe.ValidationError, "not configured"):
			ai.summarize_call(valid.name)
		self.key.return_value = CONFIG
		for log, state in ((missing, "Missing"), (unselected, "Ambiguous"), (legacy, "Legacy")):
			view = ai.get_call_summary(log.name)
			self.assertEqual(view["recording_state"], state)
			self.assertIsNone(view["result"])
			with self.assertRaises(frappe.ValidationError):
				ai.summarize_call(log.name)
		self.job.assert_not_called()

	def test_failed_or_incomplete_provider_result_never_persists_a_partial_summary(self):
		log = self.call()
		self.attach(log, audio=f"Invalid recording {self.unique}".encode())
		ai.summarize_call(log.name)
		send = self.run_job(response({"error": "sample provider error"}, status=422))
		self.assertEqual(send.call_count, 1)
		view = ai.get_call_summary(log.name)
		self.assertEqual(view["status"], "Error")
		self.assertIn("could not transcribe", view["error"])
		self.assertIsNone(view["result"])
		self.assertFalse(frappe.db.get_value(ai.SUMMARY, log.name, "transcript"))

		self.past_cooldown(log.name)
		ai.summarize_call(log.name)
		self.run_job(response({"text": TRANSCRIPT}), response({"choices": [{"message": {"content": "{}"}}]}))
		self.assertEqual(ai.get_call_summary(log.name)["status"], "Error")
		self.assertFalse(frappe.db.get_value(ai.SUMMARY, log.name, "transcript"))

	def test_failed_regeneration_keeps_valid_result_and_a_changed_source_hides_it(self):
		log = self.call()
		self.attach(log)
		ai.summarize_call(log.name)
		self.run_job(response({"text": TRANSCRIPT}), chat_response())
		original = ai.get_call_summary(log.name)["result"]
		self.past_cooldown(log.name)
		ai.summarize_call(log.name, regenerate=True)
		self.run_job(response({"text": ""}))
		failed = ai.get_call_summary(log.name)
		self.assertEqual(failed["status"], "Error")
		self.assertEqual(failed["result"], original)
		other, _ = self.attach(log, "replacement")
		frappe.db.set_value(calls.CALL_LOG, log.name, "recording_url", other.file_url)
		view = ai.get_call_summary(log.name)
		self.assertTrue(view["recording_changed"])
		self.assertIsNone(view["result"])

	def test_original_agent_keeps_playback_but_cannot_read_or_generate_after_handoff(self):
		a, b = self.user("a"), self.user("b")
		manager = self.user("manager", "Sales Manager")
		log = self.call(agent=a)
		self.attach(log)
		frappe.set_user(a)
		self.assertTrue(calls.get_call(log.name)["can_use_ai_summary"])
		self.assertEqual(ai.summarize_call(log.name)["status"], "Queued")
		self.run_job(response({"text": TRANSCRIPT}), chat_response())
		frappe.set_user(manager)
		calls.assign_call(log.name, b)
		self.assertEqual(ai.get_call_summary(log.name)["result"]["summary"], ANALYSIS["summary"])

		frappe.set_user(a)
		original = calls.get_call(log.name)
		self.assertEqual(original["recording"]["state"], "Available")
		self.assertFalse(original["can_use_ai_summary"])
		self.assertEqual(original["note"], "Original call note.")
		for read in (ai.get_call_summary, ai.summarize_call):
			with self.assertRaises(frappe.PermissionError):
				read(log.name)
		with self.assertRaises(frappe.PermissionError):
			client_get(ai.SUMMARY, log.name)
		frappe.set_user(b)
		self.assertEqual(ai.get_call_summary(log.name)["result"]["transcript"], TRANSCRIPT)
		with self.assertRaises(frappe.PermissionError):
			client_get(ai.SUMMARY, log.name)

	def test_worker_rechecks_authorization_before_sending_recording(self):
		a, b = self.user("worker-a"), self.user("worker-b")
		log = self.call(agent=a)
		self.attach(log)
		frappe.set_user(a)
		ai.summarize_call(log.name)
		frappe.set_user("Administrator")
		calls.assign_call(log.name, b)
		frappe.set_user(a)
		self.run_job().assert_not_called()
		frappe.set_user(b)
		view = ai.get_call_summary(log.name)
		self.assertEqual(view["status"], "Error")
		self.assertIsNone(view["result"])

	def test_legacy_ai_notes_and_versions_are_archived_idempotently(self):
		log = self.call()
		legacy = "[AI Tóm tắt]\nArchived summary.\n\n[Next Step]\nSend the quote."
		note = "Original call note.\n\n---\n" + legacy
		frappe.db.set_value(calls.CALL_LOG, log.name, "note", note)
		revision = frappe.get_doc({
			"doctype": "Version", "ref_doctype": calls.CALL_LOG, "docname": log.name,
			"data": json.dumps({"changed": [["note", "Old manual note.", note]]}, ensure_ascii=False),
		}).insert(ignore_permissions=True)

		for _ in range(2):
			archive_legacy_call_ai_notes.execute()
		self.assertEqual(frappe.db.get_value(calls.CALL_LOG, log.name, "note"), "Original call note.")
		view = ai.get_call_summary(log.name)
		self.assertEqual(view["legacy_note"], legacy)
		self.assertIsNone(view["result"])
		self.assertEqual(frappe.db.count(ai.SUMMARY, {"call_log": log.name}), 1)
		self.assertEqual(frappe.db.count(calls.CALL_EVENT, {"source_version": revision.name}), 1)
		public = frappe.db.get_value("Version", revision.name, "data")
		self.assertNotIn("Archived summary", public)
		self.assertIn("Old manual note.", public)

	def test_deleting_call_log_removes_its_private_summary(self):
		log = self.call()
		self.attach(log)
		ai.summarize_call(log.name)
		self.run_job(response({"text": TRANSCRIPT}), chat_response())
		self.assertTrue(frappe.db.exists(ai.SUMMARY, log.name))
		frappe.delete_doc(calls.CALL_LOG, log.name)
		self.assertFalse(frappe.db.exists(calls.CALL_LOG, log.name))
		self.assertFalse(frappe.db.exists(ai.SUMMARY, log.name))

	def test_summary_regenerate_obeys_the_call_cooldown_without_charging_duplicates(self):
		log = self.call()
		self.attach(log)
		ai.summarize_call(log.name)
		self.run_job(response({"text": TRANSCRIPT}), chat_response())

		self.assertGreater(ai.get_call_summary(log.name)["retry_after"], 0)
		with self.assertRaises(frappe.RateLimitExceededError):
			ai.summarize_call(log.name, regenerate=True)
		self.assertEqual(ai.summarize_call(log.name)["status"], "Ready")
		self.budget.assert_called_once()
		self.past_cooldown(log.name)
		self.assertEqual(ai.summarize_call(log.name, regenerate=True)["status"], "Queued")
		self.assertEqual(self.budget.call_count, 2)

	def test_notes_keep_all_explicit_handwritten_sections_and_a_versioned_append(self):
		log = self.call()
		archive = archive_legacy_call_ai_notes
		ai_first = "[AI Tóm tắt]\nOriginal AI output."
		ai_last = "[Next Step]\nAI follow-up."
		note = archive.SEPARATOR.join((
			"Human introduction.", ai_first, "Handwritten between blocks.", ai_last, "Later handwritten note.",
		))
		edited = note + "\nAdditional handwritten comment."
		frappe.db.set_value(calls.CALL_LOG, log.name, "note", edited)
		source = {"changed": [["note", note, edited], ["status", "Initiated", "Completed"]]}
		version = frappe.get_doc({
			"doctype": "Version", "ref_doctype": calls.CALL_LOG, "docname": log.name,
			"data": json.dumps(source, ensure_ascii=False),
		}).insert(ignore_permissions=True)

		for _ in range(2):
			archive.execute()
		self.assertEqual(frappe.db.get_value(calls.CALL_LOG, log.name, "note"),
			archive.SEPARATOR.join(("Human introduction.", "Handwritten between blocks.",
				"Later handwritten note.\nAdditional handwritten comment.")))
		self.assertEqual(frappe.db.get_value(ai.SUMMARY, log.name, "legacy_note"),
			archive.SEPARATOR.join((ai_first, ai_last)))
		public = json.loads(frappe.db.get_value("Version", version.name, "data"))
		self.assertIn("Additional handwritten comment.", public["changed"][0][2])
		self.assertEqual(public["changed"][1], source["changed"][1])
		original = frappe.get_all(calls.CALL_EVENT, filters={"source_version": version.name}, pluck="revision_data")
		self.assertEqual(len(original), 1)
		self.assertEqual(json.loads(original[0])["data"], source)

	def test_reapply_repairs_previously_archived_notes_and_version_without_duplicating(self):
		log = self.call()
		archive = archive_legacy_call_ai_notes
		public_prefix = "Earlier handwritten note."
		new_edit = "Handwritten after the first migration."
		ai_text = "[AI Tóm tắt]\nLegacy output.\n\n[Next Step]\nLegacy follow-up."
		full = archive.SEPARATOR.join((public_prefix, ai_text))
		manual_append = "Handwritten without a separator."
		edited = full + "\n" + manual_append
		frappe.db.set_value(calls.CALL_LOG, log.name, "note", archive.SEPARATOR.join((public_prefix, new_edit)))
		frappe.get_doc({
			"doctype": ai.SUMMARY, "call_log": log.name, "legacy_note": ai_text + "\n" + manual_append,
		}).insert(ignore_permissions=True)
		version = frappe.get_doc({
			"doctype": "Version", "ref_doctype": calls.CALL_LOG, "docname": log.name,
			"data": json.dumps({"changed": [["note", full, edited]]}, ensure_ascii=False),
		}).insert(ignore_permissions=True)
		archive._archive_revision(version, log.name, calls.CALL_LOG, {
			"changed": [["note", public_prefix, public_prefix]],
		})

		for _ in range(2):
			recover_legacy_call_ai_notes.execute()
		self.assertEqual(frappe.db.get_value(calls.CALL_LOG, log.name, "note"),
			archive.SEPARATOR.join((public_prefix, new_edit, manual_append)))
		self.assertEqual(frappe.db.get_value(ai.SUMMARY, log.name, "legacy_note"), ai_text)
		self.assertEqual(frappe.db.count(ai.SUMMARY, {"call_log": log.name}), 1)
		self.assertEqual(frappe.db.count(calls.CALL_EVENT, {"source_version": version.name}), 1)
		self.assertEqual(json.loads(frappe.db.get_value("Version", version.name, "data"))["changed"],
			[["note", public_prefix, public_prefix + "\n" + manual_append]])


class TestBeeKnoeeBaseURL(FrappeTestCase):
	def test_default_environment_and_site_precedence(self):
		with patch.dict(os.environ, {"DOUBLET_BEEKNOEE_API_KEY": "fixture-key"}, clear=True):
			with patch.object(frappe, "conf", {}):
				self.assertEqual(ai._get_ai_config().base_url, "https://platform.beeknoee.com/api/v1")
			os.environ["DOUBLET_BEEKNOEE_BASE_URL"] = "https://platform.beeknoee.com/v1/"
			with patch.object(frappe, "conf", {}):
				self.assertEqual(ai._get_ai_config().base_url, "https://platform.beeknoee.com/v1")
			with patch.object(frappe, "conf", {"doublet_beeknoee_base_url": "https://bee.example/api/v1/"}):
				config = ai._get_ai_config()
				self.assertEqual(config.base_url, "https://bee.example/api/v1")
				self.assertNotIn("fixture-key", repr(config))

	def test_unsafe_base_urls_disable_generation_configuration(self):
		with patch.dict(os.environ, {"DOUBLET_BEEKNOEE_API_KEY": "fixture-key"}, clear=True):
			for url in (
				"http://bee.example/api/v1",
				"https://user:secret@bee.example/api/v1",
				"https://bee.example/api/v1?token=x",
				"https://bee.example/api/v1#fragment",
				"https:///api/v1",
				"https://bee.example:invalid/api/v1",
				"https://bee.example\\path",
			):
				with self.subTest(url=url), patch.object(frappe, "conf", {"doublet_beeknoee_base_url": url}):
					self.assertIsNone(ai._get_ai_config())
