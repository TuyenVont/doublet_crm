from datetime import datetime

import frappe
from frappe.tests.utils import FrappeTestCase

from doublet_crm.patches.setup_zalo_lead_source import execute
from doublet_crm.zalo_inbox import get_conversation_info
from doublet_crm.zalo_oa import CONVERSATION, LEAD, LEAD_SOURCE, MESSAGE, receive_mock_text
from doublet_crm.zalo_workflow import update_conversation


class TestDoubleTMessage(FrappeTestCase):
    def setUp(self):
        self.previous_user = frappe.session.user
        frappe.set_user("Administrator")
        execute()
        self.payload = {
            "oa_id": frappe.generate_hash(length=12),
            "external_user_id": "mock-sender",
            "external_message_id": "mock-message",
            "content": "Mình muốn tư vấn sản phẩm A",
            "sent_at": "2026-11-16T20:00:00+07:00",
        }

    def tearDown(self):
        frappe.set_user(self.previous_user)

    def receive(self, **overrides):
        return receive_mock_text(**(self.payload | overrides))

    def test_replay_returns_existing_message(self):
        first = self.receive()
        replay = self.receive()

        self.assertFalse(first["duplicate"])
        self.assertEqual(replay, first | {"duplicate": True})
        conversation = frappe.get_doc(CONVERSATION, first["conversation"])
        message = frappe.get_doc(MESSAGE, first["message"])
        self.assertEqual(conversation.external_user_id, self.payload["external_user_id"])
        self.assertEqual(conversation.oa_id, self.payload["oa_id"])
        self.assertIsNone(first["lead"])
        self.assertFalse(conversation.lead)
        self.assertEqual(conversation.handling_status, "Waiting")
        self.assertEqual(message.conversation, conversation.name)
        self.assertEqual(message.external_message_id, self.payload["external_message_id"])
        self.assertEqual(message.source, "zalo_oa")
        self.assertEqual(message.direction, "inbound")
        self.assertEqual(message.content, self.payload["content"])
        self.assertEqual(message.is_simulated, 1)
        self.assertIsInstance(message.sent_at, datetime)
        self.assertEqual(frappe.db.count(MESSAGE, {"conversation": conversation.name}), 1)

    def test_sender_thread_and_message_id_are_scoped_by_account(self):
        first = self.receive()
        second = self.receive(external_message_id="another-message")
        other_oa = self.receive(oa_id="another-" + self.payload["oa_id"])

        self.assertEqual(first["conversation"], second["conversation"])
        self.assertNotEqual(first["message"], second["message"])
        self.assertNotEqual(first["conversation"], other_oa["conversation"])
        self.assertNotEqual(first["message"], other_oa["message"])
        self.assertEqual(first["lead"], second["lead"])
        self.assertIsNone(other_oa["lead"])

    def link_new_lead(self, conversation):
        info = get_conversation_info(conversation)
        update_conversation(conversation, "Create Lead", "create-lead", info["version"], lead_name="Zalo test")
        return get_conversation_info(conversation)["lead"]

    def test_replay_preserves_an_explicit_customer_link(self):
        first = self.receive()
        lead = self.link_new_lead(first["conversation"])

        replay = self.receive()

        self.assertTrue(replay["duplicate"])
        self.assertEqual(replay["message"], first["message"])
        self.assertEqual(replay["lead"], lead)
        self.assertEqual(frappe.db.get_value(LEAD, lead, "source"), LEAD_SOURCE)
        self.assertEqual(frappe.db.get_value(LEAD, lead, "status"), "NEW")
        self.assertEqual(frappe.db.count(MESSAGE, {"conversation": first["conversation"]}), 1)

    def test_converted_lead_returns_contact_without_creating_another_lead(self):
        first = self.receive()
        lead = self.link_new_lead(first["conversation"])
        contact = frappe.get_doc({"doctype": "DoubleT Contact", "first_name": "Zalo test"}).insert()
        frappe.db.set_value(
            LEAD, lead, {"status": "CONVERTED", "converted_contact": contact.name}
        )

        result = self.receive(external_message_id="after-conversion")

        self.assertEqual(result["lead"], lead)
        self.assertEqual(result["contact"], contact.name)
        self.assertEqual(frappe.db.get_value(LEAD, lead, "status"), "CONVERTED")

    def test_reused_message_id_for_a_different_sender_is_rejected(self):
        self.receive()
        with self.assertRaises(frappe.ValidationError):
            self.receive(external_user_id="other-sender")
        self.assertEqual(frappe.db.count(CONVERSATION, {"oa_id": self.payload["oa_id"]}), 1)

    def test_invalid_message_leaves_no_conversation(self):
        with self.assertRaises(frappe.ValidationError):
            self.receive(sent_at="2026-11-16T20:00:00")
        self.assertFalse(frappe.db.exists(CONVERSATION, {"oa_id": self.payload["oa_id"]}))

    def test_guest_is_rejected(self):
        frappe.set_user("Guest")
        with self.assertRaises(frappe.PermissionError):
            self.receive()
