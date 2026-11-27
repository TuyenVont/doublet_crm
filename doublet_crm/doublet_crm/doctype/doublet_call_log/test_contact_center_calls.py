import json
from datetime import timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, quote, urlsplit

import frappe
from frappe.client import get, get_list, set_value
from frappe.core.doctype.file.utils import find_file_by_url
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime
from frappe.utils.file_manager import save_file

from doublet_crm import contact_center_calls as calls
from doublet_crm.calls_demo import _recording, _user
from doublet_crm.patches import backfill_call_queue, protect_call_case_history


class TestContactCenterCalls(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.unique = frappe.generate_hash(length=10)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def customer(self, doctype, phone=None):
		return frappe.get_doc({
			"doctype": doctype,
			"first_name": f"Calls test {self.unique}",
			"phone": phone,
		}).insert()

	def user(self, key, role):
		return _user(f"calls-{key}-{self.unique}@example.com", f"Calls {key}", role)

	def log(self, **kwargs):
		return frappe.get_doc({
			"doctype": calls.CALL_LOG,
			"agent": "Administrator",
			"call_type": "Incoming",
			"status": "Completed",
			"start_time": now_datetime(),
			**kwargs,
		}).insert()

	def test_unique_phone_links_lead_and_contact_in_both_directions(self):
		for doctype, call_type, phone, number_field in (
			("DoubleT Lead", "Incoming", "+12025550111", "from_number"),
			("DoubleT Contact", "Outgoing", "+12025550112", "to_number"),
		):
			with self.subTest(doctype=doctype):
				customer = self.customer(doctype, phone)
				log = self.log(call_type=call_type, **{number_field: phone})
				details = calls.get_call(log.name)
				self.assertEqual(details["customer"]["name"], customer.name)
				self.assertEqual(details["link_state"], "Linked")
				other = self.customer(doctype)
				self.assertEqual([row["name"] for row in calls.get_record_calls(doctype, customer.name)["rows"]],
					[log.name])
				self.assertEqual(calls.get_record_calls(doctype, other.name)["rows"], [])

	def test_unmatched_and_ambiguous_calls_can_be_linked_manually(self):
		phone = "+12025550113"
		lead = self.customer("DoubleT Lead", phone)
		contact = self.customer("DoubleT Contact", phone)
		unmatched = self.log(from_number="+12025550114")
		ambiguous = self.log(from_number=phone)
		self.assertEqual(calls.get_call(unmatched.name)["link_state"], "Unmatched")
		self.assertEqual(calls.get_call(ambiguous.name)["link_state"], "Ambiguous")
		self.assertNotIn(lead.name, ambiguous.note)
		self.assertNotIn(contact.name, ambiguous.note)

		manager = self.user("manager", "Sales Manager")
		frappe.set_user(manager)
		with self.assertRaises(frappe.PermissionError):
			calls.link_customer(unmatched.name, lead.doctype, lead.name)
		for log in (unmatched, ambiguous):
			detail = calls.link_customer(log.name, contact.doctype, contact.name)
			self.assertEqual(detail["customer"]["name"], contact.name)
		self.assertSetEqual({row["name"] for row in calls.get_record_calls(contact.doctype, contact.name)["rows"]},
			{unmatched.name, ambiguous.name})

	def test_recording_requires_call_access_even_by_direct_file_url(self):
		manager = self.user("manager", "Sales Manager")
		sales_user = self.user("sales", "Sales User")
		log = self.log()
		file = save_file(
			f"DEMO {self.unique}.wav", _recording() + self.unique.encode(),
			calls.CALL_LOG, log.name, is_private=1,
		)
		frappe.set_user(manager)
		recording = calls.get_call(log.name)["recording"]
		self.assertEqual(recording["state"], "Available")
		self.assertEqual(parse_qs(urlsplit(recording["url"]).query), {"fid": [file.name]})
		self.assertEqual(find_file_by_url(file.file_url).name, file.name)

		frappe.set_user(sales_user)
		with self.assertRaises(frappe.PermissionError):
			calls.get_call(log.name)
		self.assertIsNone(find_file_by_url(file.file_url))

	def test_missing_or_non_private_recording_has_no_playback_url(self):
		log = self.log(recording_url="https://example.com/missing-call.wav")
		self.assertEqual(calls.get_call(log.name)["recording"], {"state": "Legacy"})
		self.assertEqual(calls.get_call(self.log().name)["recording"], {"state": "None"})
		missing = self.log(recording_url="/private/files/missing-legacy.wav")
		self.assertEqual(calls.get_call(missing.name)["recording"], {"state": "Missing"})

	def test_legacy_public_recording_plays_only_after_a_scoped_private_attachment(self):
		log = self.log()
		content = _recording() + self.unique.encode()
		public = save_file(f"Legacy {self.unique}.wav", content, calls.CALL_LOG, log.name, is_private=0)
		frappe.db.set_value(calls.CALL_LOG, log.name, "recording_url", public.file_url)
		self.assertEqual(calls.get_call(log.name)["recording"], {"state": "Legacy"})

		unrelated_audio = save_file(
			f"Unrelated {self.unique}.wav", content + b"unrelated", calls.CALL_LOG, log.name, is_private=1,
		)
		self.assertEqual(calls.get_call(log.name)["recording"], {"state": "Ambiguous"})
		frappe.delete_doc("File", unrelated_audio.name)

		private = save_file(f"Private {self.unique}.wav", content, calls.CALL_LOG, log.name, is_private=1)
		recording = calls.get_call(log.name)["recording"]
		self.assertEqual(recording["state"], "Available")
		self.assertTrue(recording["url"].startswith("/private/files/"))
		frappe.db.set_value(calls.CALL_LOG, log.name, "recording_url", private.file_url)
		self.assertEqual(calls.get_call(log.name)["recording"], recording)
		unrelated = self.log(recording_url=private.file_url)
		self.assertEqual(calls.get_call(unrelated.name)["recording"], {"state": "Missing"})

	def test_assignment_transfer_updates_queue_and_denies_previous_assignee_by_id(self):
		manager = self.user("manager", "Sales Manager")
		sales_a = self.user("sales-a", "Sales User")
		sales_b = self.user("sales-b", "Sales User")
		log = self.log(status="Missed", from_number="+12025550115")
		frappe.set_user(manager)
		self.assertIn(log.name, self.queue_names(scope="unassigned"))
		assigned = calls.assign_call(log.name, sales_a)
		self.assertEqual(assigned["assigned_to"], sales_a)
		self.assertNotIn(log.name, self.queue_names(scope="unassigned"))

		frappe.set_user(sales_a)
		self.assertIn(log.name, self.queue_names())
		with self.assertRaises(frappe.PermissionError):
			calls.assign_call(log.name, sales_b)
		calls.start_call(log.name)

		frappe.set_user(manager)
		transferred = calls.assign_call(log.name, sales_b)
		self.assertEqual(transferred["agent"], "Administrator")
		self.assertEqual(transferred["handling_status"], "In Progress")
		change = transferred["history"][0]
		self.assertEqual((change["actor"], change["previous_assignee"], change["new_assignee"]),
			(manager, sales_a, sales_b))
		self.assertTrue(change["occurred_at"])

		frappe.set_user(sales_a)
		self.assertNotIn(log.name, self.queue_names())
		with self.assertRaises(frappe.PermissionError):
			calls.get_call(log.name)
		with self.assertRaises(frappe.PermissionError):
			calls.start_call(log.name)
		with self.assertRaises(frappe.PermissionError):
			calls.get_calls(scope="all")

		frappe.set_user(sales_b)
		self.assertIn(log.name, self.queue_names(handling_status="In Progress"))
		self.assertEqual(calls.get_call(log.name)["assigned_to"], sales_b)

	def test_queue_priority_filters_and_legacy_policy(self):
		contact = self.customer("DoubleT Contact", "+12025550116")
		contact.last_name = "Customer"
		contact.save()
		logs = [
			self.log(call_type="Outgoing", to_number=contact.phone, start_time="2026-10-29 10:00:00"),
			self.log(status="Missed", from_number=contact.phone, start_time="2026-10-28 10:00:00"),
		]
		self.assertEqual(self.queue_names(search=f"{self.unique} Customer"), [logs[1].name, logs[0].name])
		self.assertEqual(self.queue_names(search=contact.phone, call_type="Outgoing"), [logs[0].name])

		for log in logs:
			frappe.db.set_value(calls.CALL_LOG, log.name, {"handling_status": None, "queue_priority": 0})
		backfill_call_queue.execute()
		self.assertEqual(self.queue_names(search=self.unique, handling_status="Waiting"), [logs[1].name])
		self.assertFalse(calls.get_call(logs[0].name)["handling_status"])
		self.assertEqual(calls.get_call(logs[0].name)["status"], "Completed")

	def test_generic_api_cannot_change_case_status_or_assignee(self):
		log = self.log()
		with self.assertRaisesRegex(frappe.ValidationError, "Contact Center"):
			set_value(calls.CALL_LOG, log.name, "handling_status", "Resolved")
		with self.assertRaisesRegex(frappe.ValidationError, "Contact Center"):
			set_value(calls.CALL_LOG, log.name, "assigned_to", "Administrator")

	def queue_names(self, **kwargs):
		return [row["name"] for row in calls.get_calls(**kwargs)["rows"]]

	def test_callback_retries_handoff_results_and_resolution(self):
		manager = self.user("manager", "Sales Manager")
		sales_a = self.user("sales-a", "Sales User")
		sales_b = self.user("sales-b", "Sales User")
		contact = self.customer("DoubleT Contact")
		log = self.log(status="Missed")

		frappe.set_user(manager)
		calls.link_customer(log.name, contact.doctype, contact.name)
		calls.assign_call(log.name, sales_a)
		frappe.set_user(sales_a)
		started = calls.open_callback(log.name, due_date="2026-12-15")
		self.assertEqual(str(started["callback_task"]["due_date"]), "2026-12-15")
		task_id = started["callback_task"]["name"]
		self.assertEqual(started["handling_status"], "In Progress")
		self.assertEqual(calls.open_callback(log.name)["callback_task"]["name"], task_id)
		self.assertEqual(frappe.db.count(calls.TASK, {"callback_call_log": log.name}), 1)
		task = get(calls.TASK, task_id)
		self.assertEqual(str(task["due_date"]), "2026-12-15 23:59:59")
		self.assertEqual((task["assigned_to"], task["reference_doctype"], task["reference_docname"]),
			(sales_a, contact.doctype, contact.name))
		self.assertIn(task_id, frappe.get_list(calls.TASK, pluck="name"))

		retry = calls.record_callback_result(log.name, "No Answer", "Try later")
		self.assertEqual(retry["handling_status"], "In Progress")
		self.assertEqual(retry["callback_task"]["status"], "In Progress")
		with self.assertRaises(frappe.ValidationError):
			calls.resolve_call(log.name)

		frappe.set_user(manager)
		transferred = calls.assign_call(log.name, sales_b)
		self.assertEqual(transferred["callback_task"]["assigned_to"], sales_b)
		self.assertEqual(str(transferred["callback_task"]["due_date"]), "2026-12-15")
		frappe.set_user(sales_a)
		with self.assertRaises(frappe.PermissionError):
			get(calls.TASK, task_id)
		with self.assertRaises(frappe.PermissionError):
			calls.resolve_call(log.name)

		frappe.set_user(sales_b)
		self.assertIn(task_id, frappe.get_list(calls.TASK, pluck="name"))
		reached = calls.record_callback_result(log.name, "Reached", "Customer confirmed next step")
		self.assertEqual(reached["callback_task"]["status"], "In Progress")
		result = calls.resolve_call(log.name)
		self.assertEqual(result["status"], "Missed")
		self.assertEqual(result["handling_status"], "Resolved")
		self.assertEqual(result["callback_task"]["status"], "Done")
		self.assertEqual(result["callback_task"]["name"], task_id)
		self.assertEqual(calls.open_callback(log.name)["callback_task"]["name"], task_id)

		frappe.set_user(manager)
		reloaded = calls.get_call(log.name)
		self.assertEqual(reloaded["callback_task"]["callback_result"], "Reached")
		self.assertEqual(reloaded["callback_task"]["callback_notes"], "Customer confirmed next step")
		self.assertEqual(reloaded["history"][0]["actor"], sales_b)
		self.assertEqual([event["action"] for event in reloaded["history"][:3]],
			["Resolved", "Callback result", "Assignment changed"])

	def test_callback_reopens_same_task_and_disallows_generic_status_updates(self):
		log = self.log(status="No Answer", call_type="Incoming Forwarded")
		calls.assign_call(log.name, "Administrator")
		task_id = calls.open_callback(log.name)["callback_task"]["name"]
		with self.assertRaisesRegex(frappe.ValidationError, "Contact Center"):
			set_value(calls.TASK, task_id, "status", "Done")
		frappe.db.set_value(calls.TASK, task_id, "status", "Canceled")
		reopened = calls.open_callback(log.name)["callback_task"]
		self.assertEqual((reopened["name"], reopened["status"]), (task_id, "In Progress"))

	def test_resolution_rolls_back_task_if_case_save_fails(self):
		customer = self.customer("DoubleT Contact")
		log = self.log(status="Missed", reference_doctype=customer.doctype, reference_name=customer.name)
		calls.assign_call(log.name, "Administrator")
		task_id = calls.open_callback(log.name)["callback_task"]["name"]
		calls.record_callback_result(log.name, "Reached")
		frappe.db.savepoint("before_call_resolution")
		with patch.object(calls, "_save_case", side_effect=frappe.ValidationError) as save_case:
			with self.assertRaises(frappe.ValidationError):
				calls.resolve_call(log.name)
			save_case.assert_called_once()
			self.assertEqual(frappe.db.get_value(calls.TASK, task_id, "status"), "Done")
		frappe.db.rollback(save_point="before_call_resolution")
		self.assertEqual(frappe.db.get_value(calls.TASK, task_id, "status"), "In Progress")
		self.assertEqual(frappe.db.get_value(calls.CALL_LOG, log.name, "handling_status"), "In Progress")
		self.assertFalse(frappe.db.exists(calls.CALL_EVENT, {"call_log": log.name, "action": "Resolved"}))

	def test_completed_call_can_be_resolved_without_a_callback_task(self):
		log = self.log(status="Completed", call_type="Outgoing")
		calls.assign_call(log.name, "Administrator")
		calls.start_call(log.name)
		result = calls.resolve_call(log.name)
		self.assertEqual((result["status"], result["handling_status"]), ("Completed", "Resolved"))
		self.assertIsNone(result["callback_task"])

	def test_original_agent_keeps_log_access_but_loses_case_and_task_access_at_handoff(self):
		manager = self.user("audit-manager", "Sales Manager")
		sales_a = self.user("audit-a", "Sales User")
		sales_b = self.user("audit-b", "Sales User")
		viewer = self.user("audit-viewer", "Call Log Viewer")
		log = self.log(agent=sales_a, status="Missed", note="Original call note")

		frappe.set_user(manager)
		calls.assign_call(log.name, sales_a)
		frappe.set_user(sales_a)
		task_id = calls.open_callback(log.name)["callback_task"]["name"]
		self.assertTrue(calls.get_call(log.name)["history"])

		frappe.set_user(manager)
		calls.assign_call(log.name, sales_b)
		frappe.set_user(sales_b)
		result = calls.record_callback_result(log.name, "Reached", "Private B callback note")
		event_id = result["history"][0]["name"]
		self.assertEqual(get(calls.CALL_EVENT, event_id)["details"], "Reached\nPrivate B callback note")
		self.assertEqual(get(calls.TASK, task_id)["callback_notes"], "Private B callback note")

		for user in (sales_a, viewer):
			with self.subTest(user=user):
				frappe.set_user(user)
				self.assertNotIn(log.name, self.queue_names())
				details = calls.get_call(log.name)
				self.assertEqual(details["note"], "Original call note")
				self.assertEqual(details["history"], [])
				self.assertIsNone(details["callback_task"])
				self.assertFalse(details["can_handle"])
				raw_log = get(calls.CALL_LOG, log.name)
				self.assertEqual(raw_log["agent"], sales_a)
				self.assertNotIn("case_events", raw_log)
				with self.assertRaises(frappe.PermissionError):
					get(calls.CALL_EVENT, event_id)
				with self.assertRaises(frappe.PermissionError):
					get(calls.TASK, task_id)
				with self.assertRaises(frappe.PermissionError):
					calls.resolve_call(log.name)

		frappe.set_user(sales_a)
		self.assertEqual(get_list(calls.CALL_EVENT, filters={"call_log": log.name}), [])
		self.assertEqual(get_list(calls.TASK, filters={"callback_call_log": log.name}), [])

		frappe.set_user(manager)
		managed = calls.get_call(log.name)
		self.assertEqual(managed["callback_task"]["callback_notes"], "Private B callback note")
		self.assertTrue(any(
			event["previous_assignee"] == sales_a and event["new_assignee"] == sales_b
			for event in managed["history"]
		))

	def test_missed_call_requires_customer_then_updates_and_resolves_the_same_task(self):
		for doctype in ("DoubleT Lead", "DoubleT Contact"):
			with self.subTest(doctype=doctype):
				log = self.log(status="Missed")
				calls.assign_call(log.name, "Administrator")
				task_id = calls.open_callback(log.name)["callback_task"]["name"]
				calls.record_callback_result(log.name, "Reached", "Reached before customer was identified")

				with self.assertRaisesRegex(frappe.ValidationError, "Link a Lead or Contact"):
					calls.resolve_call(log.name)
				with self.assertRaisesRegex(frappe.ValidationError, "Select a Lead or Contact"):
					calls.link_customer(log.name, "User", "Administrator")
				with self.assertRaises(frappe.DoesNotExistError):
					calls.link_customer(log.name, doctype, f"missing-{self.unique}")
				self.assertEqual(get(calls.TASK, task_id)["status"], "In Progress")
				self.assertEqual(calls.get_call(log.name)["handling_status"], "In Progress")

				customer = self.customer(doctype)
				linked = calls.link_customer(log.name, doctype, customer.name)
				self.assertEqual(linked["callback_task"]["name"], task_id)
				self.assertEqual(linked["callback_task"]["callback_result"], "Reached")
				self.assertEqual(get(calls.TASK, task_id)["reference_docname"], customer.name)
				self.assertEqual(calls.open_callback(log.name)["callback_task"]["name"], task_id)
				self.assertEqual(frappe.db.count(calls.TASK, {"callback_call_log": log.name}), 1)
				resolved = calls.resolve_call(log.name)
				self.assertEqual(resolved["handling_status"], "Resolved")
				self.assertEqual(resolved["callback_task"]["status"], "Done")

	def test_stale_task_link_can_be_repaired_without_creating_a_task(self):
		customer = self.customer("DoubleT Contact")
		log = self.log(status="Missed", reference_doctype=customer.doctype, reference_name=customer.name)
		calls.assign_call(log.name, "Administrator")
		task_id = calls.open_callback(log.name)["callback_task"]["name"]
		calls.record_callback_result(log.name, "Reached")
		frappe.db.set_value(calls.TASK, task_id, {"reference_doctype": None, "reference_docname": None})
		with self.assertRaisesRegex(frappe.ValidationError, "Confirm the linked customer"):
			calls.resolve_call(log.name)
		self.assertEqual(calls.link_customer(log.name, customer.doctype, customer.name)["callback_task"]["name"],
			task_id)
		self.assertEqual(calls.resolve_call(log.name)["callback_task"]["status"], "Done")

	def test_version_migration_preserves_original_audit_and_public_note(self):
		manager = self.user("archive-manager", "Sales Manager")
		agent = self.user("archive-agent", "Sales User")
		handler = self.user("archive-handler", "Sales User")
		log = self.log(agent=agent, status="Missed")
		calls.assign_call(log.name, handler)
		task = calls.open_callback(log.name)["callback_task"]["name"]
		case_data = {"changed": [["note", "before", "after"], ["assigned_to", agent, handler]],
			"added": [["case_events", {"details": "Private archived callback"}]]}
		task_data = {"changed": [["callback_notes", "", "Private Task revision"]]}
		revisions = {}
		for doctype, name, data in ((calls.CALL_LOG, log.name, case_data), (calls.TASK, task, task_data)):
			revision = frappe.get_doc(doctype="Version", ref_doctype=doctype, docname=name, data=json.dumps(data))
			revisions[doctype] = revision.insert(ignore_permissions=True).name
		initial_events = {row["name"] for row in calls.get_call(log.name)["history"]}

		protect_call_case_history.execute()
		protect_call_case_history.execute()
		self.assertEqual(json.loads(frappe.db.get_value("Version", revisions[calls.CALL_LOG], "data")),
			{"changed": [["note", "before", "after"]], "added": []})
		self.assertEqual(json.loads(frappe.db.get_value("Version", revisions[calls.TASK], "data")), {})
		for reader in (handler, manager):
			frappe.set_user(reader)
			events = calls.get_call(log.name)["history"]
			self.assertEqual(len(events), len(initial_events) + 2)
			self.assertTrue(initial_events.issubset({event["name"] for event in events}))
			for doctype, data in ((calls.CALL_LOG, case_data), (calls.TASK, task_data)):
				archived = get_list(calls.CALL_EVENT, filters={"source_version": revisions[doctype]},
					fields=["name", "revision_data"])
				self.assertEqual(len(archived), 1)
				self.assertEqual(json.loads(archived[0]["revision_data"])["data"], data)
				with self.assertRaises(frappe.PermissionError):
					frappe.get_doc(calls.CALL_EVENT, archived[0]["name"]).validate_share(None)
		frappe.set_user(agent)
		self.assertEqual(calls.get_call(log.name)["history"], [])
		self.assertEqual(get_list(calls.CALL_EVENT, filters={"call_log": log.name}), [])

	def test_recording_uses_declared_file_and_does_not_guess_between_attachments(self):
		log = self.log()
		first = save_file(
			f"Primary {self.unique}.wav", _recording() + b"primary" + self.unique.encode(),
			calls.CALL_LOG, log.name, is_private=1,
		)
		second = save_file(
			f"Alternate {self.unique}.wav", _recording() + b"alternate" + self.unique.encode(),
			calls.CALL_LOG, log.name, is_private=1,
		)
		self.assertEqual(calls.get_call(log.name)["recording"], {"state": "Ambiguous"})
		frappe.db.set_value(calls.CALL_LOG, log.name, "recording_url", f"/files/legacy-{self.unique}.wav")
		self.assertEqual(calls.get_call(log.name)["recording"], {"state": "Ambiguous"})
		frappe.db.set_value(calls.CALL_LOG, log.name, "recording_url", f"{quote(first.file_url)}?fid={first.name}")
		audio = calls.get_call(log.name)["recording"]
		self.assertEqual(audio["state"], "Available")
		self.assertEqual(audio["label"], first.file_name)
		self.assertEqual(parse_qs(urlsplit(audio["url"]).query), {"fid": [first.name]})
		frappe.db.set_value(calls.CALL_LOG, log.name, "recording_url", f"{first.file_url}?fid={second.name}")
		self.assertEqual(calls.get_call(log.name)["recording"], {"state": "Missing"})

	def test_missing_declared_recording_never_falls_back_to_an_unrelated_file(self):
		log = self.log(recording_url="/private/files/declared-recording-missing.wav")
		save_file(
			f"Fallback {self.unique}.wav", _recording() + self.unique.encode(),
			calls.CALL_LOG, log.name, is_private=1,
		)
		self.assertEqual(calls.get_call(log.name)["recording"], {"state": "Missing"})

	def test_search_checks_only_linked_customers_in_bounded_windows(self):
		user = self.user("search-page", "Sales User")
		n = calls.SEARCH_SCAN_LIMIT + calls.PAGE_SIZE + 6
		now = now_datetime()
		customer_ids = [f"search-{self.unique}-{i:03d}" for i in range(n + 80)]
		call_ids = [f"call-{self.unique}-{i:03d}" for i in range(n)]
		common_fields = ("name", "owner", "modified_by", "creation", "modified", "docstatus", "idx")
		frappe.db.bulk_insert(
			"DoubleT Contact", (*common_fields, "first_name", "last_name", "phone"),
			[
				(name, "Administrator", "Administrator", now, now, 0, 0,
				 "Synthetic", "Search target" if i >= calls.SEARCH_SCAN_LIMIT else "Other customer",
				 "+44 20 7946 0958" if i == n - 1 else None)
				for i, name in enumerate(customer_ids)
			],
		)
		frappe.db.bulk_insert(
			calls.CALL_LOG,
			(*common_fields, "agent", "assigned_to", "call_type", "status", "handling_status",
			 "reference_doctype", "reference_name", "start_time", "queue_priority",
			 "external_call_id", "from_number", "duration"),
			[
				(name, "Administrator", "Administrator", now, now, 0, 0,
				 user, user, "Incoming", "Completed", "Waiting", "DoubleT Contact", customer_ids[i],
				 now - timedelta(seconds=i), 0, f"external-{name}", "+12025550102", 15)
				for i, name in enumerate(call_ids)
			],
		)

		frappe.set_user(user)
		with patch.object(frappe, "get_list", wraps=frappe.get_list) as read:
			first = calls.get_calls(search="Synthetic Search target")
			second = calls.get_calls(search="Synthetic Search target", start=first["next_start"])
			third = calls.get_calls(search="Synthetic Search target", start=second["next_start"])
		self.assertEqual(first["rows"], [])
		self.assertEqual(first["next_start"], calls.SEARCH_SCAN_LIMIT)
		self.assertTrue(first["has_more"])
		self.assertEqual(first["counts"], {"Waiting": n})
		self.assertEqual(len(second["rows"]), calls.PAGE_SIZE)
		self.assertEqual([row["name"] for row in second["rows"] + third["rows"]],
			call_ids[calls.SEARCH_SCAN_LIMIT:])
		self.assertFalse(third["has_more"])
		for call in read.call_args_list:
			if call.args[0] == "DoubleT Contact":
				op, names = call.kwargs["filters"]["name"]
				self.assertEqual(op, "in")
				self.assertLessEqual(len(names), calls.SEARCH_SCAN_LIMIT)
				self.assertEqual(call.kwargs["limit_page_length"], len(names))
				self.assertFalse(set(names) & set(customer_ids[n:]))

		self.assertEqual(self.queue_names(search=f"external-{call_ids[-1]}"), [call_ids[-1]])
		self.assertEqual(self.queue_names(
			search=f"ternal-{call_ids[-1]}", start=calls.SEARCH_SCAN_LIMIT,
		), [call_ids[-1]])
		phone_search = calls.get_calls(search="+44 20 7946 0958", start=calls.SEARCH_SCAN_LIMIT)
		self.assertEqual([row["name"] for row in phone_search["rows"]], [call_ids[-1]])
		self.assertNotIn("phone", phone_search["rows"][0]["customer"])
		self.assertEqual(len(calls.get_calls(search="+1 202-555-0102")["rows"]), calls.PAGE_SIZE)

	def test_search_does_not_match_an_unreadable_customer(self):
		user = self.user("search-restricted", "Sales User")
		lead = self.customer("DoubleT Lead")
		log = self.log(agent=user, reference_doctype=lead.doctype, reference_name=lead.name)
		# An existing log stays readable independently of its linked Lead.
		frappe.db.set_value(calls.CALL_LOG, log.name, "assigned_to", user)
		frappe.set_user(user)
		self.assertEqual(self.queue_names(search=lead.first_name), [])
		page = calls.get_calls(search=log.name)
		self.assertEqual([row["name"] for row in page["rows"]], [log.name])
		self.assertIsNone(page["rows"][0]["customer"])
