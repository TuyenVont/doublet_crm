from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import get_datetime

from doublet_crm.patches.setup_zalo_lead_source import execute
from doublet_crm.zalo_inbox import (
    get_customer_details,
    get_conversation_info,
    get_messages,
    get_record_messages,
    list_conversations,
    list_record_conversations,
    save_mock_reply,
    save_record_mock_reply,
)
from doublet_crm.zalo_oa import MESSAGE, receive_mock_text


class TestZaloInbox(FrappeTestCase):
    def setUp(self):
        self.previous_user = frappe.session.user
        frappe.set_user("Administrator")
        execute()
        self.payload = {
            "oa_id": frappe.generate_hash(length=12),
            "external_user_id": "inbox-user",
            "external_message_id": "inbox-message",
            "content": "Tư vấn sản phẩm",
            "sent_at": "2026-11-16T20:00:00+07:00",
        }

    def tearDown(self):
        frappe.set_user(self.previous_user)

    def receive(self, **overrides):
        return receive_mock_text(**(self.payload | overrides))

    def test_list_lead_and_store_simulated_reply(self):
        inbound = self.receive()
        conversation = inbound["conversation"]
        listing = list_conversations()
        listed = next(item for item in listing["conversations"] if item["name"] == conversation)
        self.assertEqual(listed["lead"], inbound["lead"])
        self.assertEqual(listed["oa_id"], self.payload["oa_id"])

        reply = save_mock_reply(conversation, "Để mình tư vấn cho bạn.")
        self.assertEqual(reply["direction"], "outbound")
        self.assertEqual(reply["is_simulated"], 1)
        self.assertEqual(frappe.db.get_value(MESSAGE, reply["name"], "conversation"), conversation)
        thread = get_messages(conversation)
        self.assertTrue(thread["can_reply"])
        self.assertEqual({item["name"] for item in thread["messages"]}, {reply["name"], inbound["message"]})

    def test_history_cursor_handles_identical_timestamps_and_checks_conversation(self):
        first = self.receive()
        second = self.receive(external_message_id="tied-message")
        other = self.receive(external_user_id="other", external_message_id="other-conversation")
        conversation = first["conversation"]

        with patch("doublet_crm.zalo_inbox.PAGE_SIZE", 1):
            page = get_messages(conversation)
            self.assertTrue(page["has_more"])
            older = get_messages(conversation, before=page["messages"][0]["name"])

        self.assertFalse(older["has_more"])
        self.assertEqual(
            [older["messages"][0]["name"], page["messages"][0]["name"]],
            sorted([first["message"], second["message"]]),
        )
        with self.assertRaises(frappe.ValidationError):
            get_messages(conversation, before=other["message"])

    def test_reply_is_newer_than_future_dated_inbound(self):
        external_user_id = f"future-{frappe.generate_hash(length=10)}"
        inbound = self.receive(
            external_user_id=external_user_id,
            external_message_id="future-message",
            sent_at="2099-01-01T00:00:00+07:00",
        )
        reply = save_mock_reply(inbound["conversation"], "Future-safe reply")
        inbound_sent_at = frappe.db.get_value(MESSAGE, inbound["message"], "sent_at")
        self.assertGreater(get_datetime(reply["sent_at"]), get_datetime(inbound_sent_at))
        listing = list_conversations(search=external_user_id, reply_status="Replied")
        self.assertEqual([row["name"] for row in listing["conversations"]], [inbound["conversation"]])

    def test_inbox_search_filters_latest_activity_and_reply_state(self):
        unique = frappe.generate_hash(length=10)
        alpha_oa = f"oa-alpha-{unique}"
        beta_oa = f"oa-beta-{unique}"
        alpha_user = f"alpha-user-{unique}"
        first = self.receive(
            oa_id=alpha_oa,
            external_user_id=alpha_user,
            external_message_id="alpha-message",
            content="Alpha needs help",
            sent_at="2026-11-16T20:00:00+07:00",
        )
        second = self.receive(
            oa_id=beta_oa,
            external_user_id=f"beta-user-{unique}",
            external_message_id="beta-message",
            content="Beta is newer",
            sent_at="2026-11-16T21:00:00+07:00",
        )

        listing = list_conversations(search=unique)
        self.assertEqual(
            [row["name"] for row in listing["conversations"]],
            [second["conversation"], first["conversation"]],
        )
        self.assertIn(alpha_oa, listing["oa_options"])
        self.assertIn(beta_oa, listing["oa_options"])
        self.assertEqual(listing["conversations"][0]["last_message_content"], "Beta is newer")
        self.assertEqual(listing["conversations"][0]["reply_status"], "Needs reply")

        with patch("doublet_crm.zalo_inbox.PAGE_SIZE", 1):
            page = list_conversations(search=unique)
            self.assertEqual(page["conversations"][0]["name"], second["conversation"])
            self.assertTrue(page["has_more"])
            self.assertEqual(get_conversation_info(first["conversation"])["name"], first["conversation"])
            search = list_conversations(search=alpha_user)
            self.assertEqual([row["name"] for row in search["conversations"]], [first["conversation"]])
            self.assertFalse(search["has_more"])

        oa_filtered = list_conversations(oa_id=beta_oa)
        self.assertEqual([row["name"] for row in oa_filtered["conversations"]], [second["conversation"]])
        self.assertEqual(len(list_conversations(search=unique, reply_status="Needs reply")["conversations"]), 2)

        reply = save_mock_reply(first["conversation"], "Alpha replied")
        replied = list_conversations(search=unique, reply_status="Replied")
        self.assertEqual([row["name"] for row in replied["conversations"]], [first["conversation"]])
        self.assertEqual(replied["conversations"][0]["last_message_content"], reply["content"])
        self.assertEqual(
            [row["name"] for row in list_conversations(search=unique, reply_status="Needs reply")["conversations"]],
            [second["conversation"]],
        )
        self.assertEqual(list_conversations(search=unique)["conversations"][0]["name"], first["conversation"])

        with self.assertRaises(frappe.ValidationError):
            list_conversations(reply_status="Unread")

    def test_record_scoped_history_reply_relationships_and_isolation(self):
        inbound = self.receive()
        other = self.receive(external_user_id="other-record", external_message_id="other-record-message")
        lead = inbound["lead"]
        unique = frappe.generate_hash(length=10)
        contact = frappe.get_doc({
            "doctype": "DoubleT Contact",
            "first_name": f"Zalo Contact {unique}",
        }).insert()
        company = frappe.get_doc({
            "doctype": "DoubleT Company",
            "company_name": f"Zalo Company {unique}",
        }).insert()
        stage = frappe.get_doc({
            "doctype": "DoubleT Deal Stage",
            "stage_name": f"Zalo Stage {unique}",
            "sort_order": 1,
            "stage_type": "OPEN",
            "enabled": 1,
        }).insert()
        deal = frappe.get_doc({
            "doctype": "DoubleT Deal",
            "deal_title": f"Zalo Deal {unique}",
            "deal_type": "PERSONAL",
            "contact": contact.name,
            "stage": stage.name,
            "source_lead": lead,
        }).insert()
        frappe.db.set_value("DoubleT Lead", lead, {
            "converted_contact": contact.name,
            "converted_company": company.name,
            "converted_deal": deal.name,
        })

        customer = get_customer_details(inbound["conversation"])
        self.assertEqual(customer["lead"]["name"], lead)
        self.assertEqual(customer["contact"]["name"], contact.name)
        self.assertEqual(customer["deal"]["name"], deal.name)
        self.assertEqual(customer["company"]["name"], company.name)

        references = (
            ("DoubleT Lead", lead),
            ("DoubleT Deal", deal.name),
            ("DoubleT Contact", contact.name),
            ("DoubleT Company", company.name),
        )
        for reference_doctype, reference_name in references:
            with self.subTest(reference_doctype=reference_doctype):
                listing = list_record_conversations(reference_doctype, reference_name)
                self.assertTrue(listing["can_read"])
                self.assertEqual([row["name"] for row in listing["conversations"]], [inbound["conversation"]])
                thread = get_record_messages(reference_doctype, reference_name, inbound["conversation"])
                self.assertEqual([row["name"] for row in thread["messages"]], [inbound["message"]])
                with self.assertRaises(frappe.PermissionError):
                    get_record_messages(reference_doctype, reference_name, other["conversation"])

        reply = save_record_mock_reply("DoubleT Contact", contact.name, inbound["conversation"], "Record reply")
        self.assertEqual(reply["direction"], "outbound")
        self.assertEqual(
            frappe.db.get_value(MESSAGE, reply["name"], "conversation"),
            inbound["conversation"],
        )

        with self.assertRaises(frappe.ValidationError):
            list_record_conversations("User", frappe.session.user)

    def test_sales_user_cannot_list_read_or_reply_without_doctype_permissions(self):
        inbound = self.receive()
        user = frappe.get_doc({
            "doctype": "User",
            "email": f"inbox-sales-{frappe.generate_hash(length=8)}@example.com",
            "first_name": "Inbox Sales",
            "send_welcome_email": 0,
        }).insert()
        user.add_roles("Sales User")
        frappe.share.add("DoubleT Lead", inbound["lead"], user.name, read=1)
        frappe.set_user(user.name)

        self.assertEqual(list_conversations(), {
            "can_read": False,
            "conversations": [],
            "has_more": False,
            "total": 0,
            "oa_options": [],
        })
        with self.assertRaises(frappe.PermissionError):
            get_messages(inbound["conversation"])
        with self.assertRaises(frappe.PermissionError):
            save_mock_reply(inbound["conversation"], "Test")
        with self.assertRaises(frappe.PermissionError):
            get_customer_details(inbound["conversation"])
        with self.assertRaises(frappe.PermissionError):
            get_conversation_info(inbound["conversation"])
        self.assertEqual(
            list_record_conversations("DoubleT Lead", inbound["lead"]),
            {"can_read": False, "conversations": []},
        )
        with self.assertRaises(frappe.PermissionError):
            get_record_messages("DoubleT Lead", inbound["lead"], inbound["conversation"])
        with self.assertRaises(frappe.PermissionError):
            save_record_mock_reply("DoubleT Lead", inbound["lead"], inbound["conversation"], "Test")
