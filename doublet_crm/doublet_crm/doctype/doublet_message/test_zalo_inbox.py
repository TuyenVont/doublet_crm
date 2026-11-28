from datetime import timedelta
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import get_datetime, now_datetime

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
from doublet_crm.zalo_oa import CONVERSATION, MESSAGE, receive_mock_text
from doublet_crm.zalo_workflow import EVENT, update_conversation


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

    def act(self, conversation, action, request_id=None, **params):
        version = get_conversation_info(conversation)["version"]
        return update_conversation(conversation, action, request_id or frappe.generate_hash(), version, **params)

    def new_lead(self, conversation):
        self.act(conversation, "Create Lead", lead_name="Zalo test")
        return get_conversation_info(conversation)["lead"]

    def sales_user(self, role="Sales User"):
        user = frappe.get_doc({
            "doctype": "User",
            "email": f"inbox-user-{frappe.generate_hash(length=8)}@example.com",
            "first_name": "Inbox QA",
            "send_welcome_email": 0,
        }).insert()
        user.add_roles(role)
        return user.name

    def test_list_lead_and_store_simulated_reply(self):
        inbound = self.receive()
        conversation = inbound["conversation"]
        lead = self.new_lead(conversation)
        listing = list_conversations(oa_id=self.payload["oa_id"])
        listed = next(item for item in listing["conversations"] if item["name"] == conversation)
        self.assertEqual(listed["lead"], lead)
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
            [first["message"], second["message"]],
        )
        with self.assertRaises(frappe.ValidationError):
            get_messages(conversation, before=other["message"])

    def test_future_timestamp_does_not_fabricate_response_time(self):
        external_user_id = f"future-{frappe.generate_hash(length=10)}"
        inbound = self.receive(
            external_user_id=external_user_id,
            external_message_id="future-message",
            sent_at="2099-01-01T00:00:00+07:00",
        )
        reply = save_mock_reply(inbound["conversation"], "Reply with actual clock")
        inbound_sent_at = frappe.db.get_value(MESSAGE, inbound["message"], "sent_at")
        self.assertLess(get_datetime(reply["sent_at"]), get_datetime(inbound_sent_at))
        row = get_conversation_info(inbound["conversation"])
        self.assertIsNone(row["first_response_seconds"])
        self.assertIsNone(row["waiting_seconds"])

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
        lead = self.new_lead(inbound["conversation"])
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

    def test_sales_user_cannot_list_read_or_reply_to_unassigned_conversation(self):
        inbound = self.receive()
        lead = self.new_lead(inbound["conversation"])
        user = self.sales_user()
        frappe.share.add("DoubleT Lead", lead, user, read=1)
        frappe.set_user(user)

        self.assertEqual(list_conversations(oa_id=self.payload["oa_id"])["conversations"], [])
        for endpoint in (get_messages, get_conversation_info, get_customer_details):
            with self.assertRaises(frappe.PermissionError):
                endpoint(inbound["conversation"])
        with self.assertRaises(frappe.PermissionError):
            save_mock_reply(inbound["conversation"], "Test")
        self.assertEqual(list_record_conversations("DoubleT Lead", lead), {"can_read": True, "conversations": []})
        with self.assertRaises(frappe.PermissionError):
            get_record_messages("DoubleT Lead", lead, inbound["conversation"])
        with self.assertRaises(frappe.PermissionError):
            save_record_mock_reply("DoubleT Lead", lead, inbound["conversation"], "Test")

    def test_handling_handover_retries_and_independent_reply_status(self):
        first, second = self.sales_user(), self.sales_user()
        manager = self.sales_user("Sales Manager")
        inbound = self.receive()
        name = inbound["conversation"]
        frappe.set_user(manager)
        self.act(name, "Assign", assignee=first)
        frappe.set_user(first)
        with self.assertRaises(frappe.PermissionError):
            save_mock_reply(name, "Accept first")
        self.act(name, "Accept")
        reply = save_mock_reply(name, "Sent once", request_id="same-reply")
        self.assertEqual(save_mock_reply(name, "Sent once", request_id="same-reply"), reply)
        with self.assertRaises(frappe.ValidationError):
            save_mock_reply(name, "Different text", request_id="same-reply")
        self.assertEqual(get_conversation_info(name)["reply_status"], "Replied")
        frappe.set_user(manager)
        version = get_conversation_info(name)["version"]
        fields = {"assignee": second, "reason": "Shift change"}
        self.assertFalse(update_conversation(name, "Assign", "handover", version, **fields)["duplicate"])
        self.assertTrue(update_conversation(name, "Assign", "handover", version, **fields)["duplicate"])
        frappe.set_user(first)
        with self.assertRaises(frappe.PermissionError):
            get_messages(name)
        self.assertFalse(frappe.has_permission(MESSAGE, "read", doc=reply["name"]))
        frappe.set_user(second)
        self.act(name, "Accept")
        self.act(name, "Resolve")
        state = get_conversation_info(name)
        self.assertEqual((state["handling_status"], state["reply_status"]), ("Resolved", "Replied"))
        self.assertEqual([row["action"] for row in state["history"]],
                         ["Assigned", "Accepted", "Transferred", "Accepted", "Resolved"])
        self.assertEqual(state["history"][2]["reason"], "Shift change")
        self.assertEqual(len(get_messages(name)["messages"]), 2)
        frappe.set_user("Administrator")
        resolved = frappe.db.get_value(CONVERSATION, name, "resolved_at")
        with patch("doublet_crm.zalo_oa._parse_sent_at", return_value=resolved + timedelta(seconds=1)):
            self.receive(external_message_id="reopen")
            self.receive(external_message_id="reopen")
        self.assertEqual(get_conversation_info(name)["handling_status"], "Waiting")
        self.assertEqual(frappe.db.count(EVENT, {"conversation": name, "action": "Reopened"}), 1)

    def test_customer_link_uses_exact_record_and_rejects_stale_or_unreadable_link(self):
        name = self.receive()["conversation"]
        sales = self.sales_user()
        first = frappe.get_doc({"doctype": "DoubleT Contact", "first_name": "Same name"}).insert()
        other = frappe.get_doc({"doctype": "DoubleT Contact", "first_name": "Same name"}).insert()
        private_lead = frappe.get_doc({"doctype": "DoubleT Lead", "first_name": "Unshared"}).insert()
        version = get_conversation_info(name)["version"]
        self.act(name, "Assign", assignee=sales)
        frappe.set_user(sales)
        with self.assertRaises(frappe.ValidationError):
            update_conversation(name, "Link Customer", "stale", version,
                                customer_type=first.doctype, customer_name=first.name)
        with self.assertRaises(frappe.PermissionError):
            self.act(name, "Link Customer", customer_type=private_lead.doctype, customer_name=private_lead.name)
        self.act(name, "Link Customer", customer_type=first.doctype, customer_name=first.name)
        self.assertEqual(get_customer_details(name)["contact"]["name"], first.name)
        with self.assertRaises(frappe.PermissionError):
            get_record_messages(other.doctype, other.name, name)
        self.assertEqual(get_record_messages(first.doctype, first.name, name)["messages"][0]["direction"], "inbound")
        with self.assertRaises(frappe.PermissionError):
            self.act(name, "Link Customer", customer_type=other.doctype, customer_name=other.name)

    def test_response_time_uses_first_unanswered_inbound_and_handles_legacy_missing_time(self):
        clock = now_datetime().replace(microsecond=0)
        with patch("doublet_crm.zalo_oa._parse_sent_at", side_effect=[
            clock - timedelta(seconds=120), clock - timedelta(seconds=90), clock - timedelta(seconds=12),
        ]):
            first = self.receive()
            name = first["conversation"]
            self.receive(external_message_id="second")
            with patch("doublet_crm.zalo_inbox.now_datetime", return_value=clock - timedelta(seconds=30)):
                self.assertEqual(get_conversation_info(name)["waiting_seconds"], 90)
                save_mock_reply(name, "Reply")
            self.receive(external_message_id="third")
        with patch("doublet_crm.zalo_inbox.now_datetime", return_value=clock):
            row = get_conversation_info(name)
            self.assertEqual(row["first_response_seconds"], 90)
            self.assertEqual(row["waiting_seconds"], 12)
            self.assertEqual(row["reply_status"], "Needs reply")
        frappe.db.set_value(MESSAGE, first["message"], {"sent_at": None, "creation": clock - timedelta(seconds=120)})
        self.assertIsNone(get_conversation_info(name)["first_response_seconds"])
