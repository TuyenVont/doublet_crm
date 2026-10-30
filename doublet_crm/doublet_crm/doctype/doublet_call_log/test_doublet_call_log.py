import random

import frappe
from frappe.tests import test_api as frappe_test_api
from frappe.tests.utils import FrappeTestCase

from doublet_crm.api import create_call_log


class TestDoubleTCallLog(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")

        self.api_user = self.make_user(
            "Call Log API",
            "call-log-api",
        )

    def tearDown(self):
        frappe.set_user("Administrator")
        super().tearDown()

    def make_user(self, role, prefix):
        unique = frappe.generate_hash(length=10)
        email = f"{prefix}-{unique}@example.com"

        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": prefix,
            "send_welcome_email": 0,
        }).insert(ignore_permissions=True)

        if role:
            user.add_roles(role)

        return user

    def make_phone(self):
        return f"090{random.randint(1000000, 9999999)}"

    def make_external_id(self):
        return f"call-{frappe.generate_hash(length=16)}"

    def make_call_log(self, agent):
        previous_user = frappe.session.user
        frappe.set_user("Administrator")

        try:
            return frappe.get_doc({
                "doctype": "DoubleT Call Log",
                "agent": agent,
                "call_type": "Incoming",
                "start_time": "2026-10-29 10:00:00",
                "status": "Completed",
                "from_number": self.make_phone(),
                "external_call_id": self.make_external_id(),
            }).insert()
        finally:
            frappe.set_user(previous_user)

    def test_sales_user_cannot_write_delete_or_export_own_log(self):
        sales_user = self.make_user(
            "Sales User",
            "call-log-sales-permission",
        )
        other_sales_user = self.make_user(
            "Sales User",
            "call-log-sales-other",
        )

        own_log = self.make_call_log(sales_user.name)
        other_log = self.make_call_log(other_sales_user.name)

        self.assertTrue(
            frappe.has_permission(
                "DoubleT Call Log",
                ptype="read",
                doc=own_log,
                user=sales_user.name,
            )
        )

        for ptype in ("write", "delete", "export"):
            self.assertFalse(
                frappe.has_permission(
                    "DoubleT Call Log",
                    ptype=ptype,
                    doc=own_log,
                    user=sales_user.name,
                ),
                msg=f"Sales User unexpectedly has {ptype} permission",
            )

        self.assertFalse(
            frappe.has_permission(
                "DoubleT Call Log",
                ptype="create",
                user=sales_user.name,
            )
        )

        self.assertFalse(
            frappe.has_permission(
                "DoubleT Call Log",
                ptype="read",
                doc=other_log,
                user=sales_user.name,
            )
        )

    def test_sales_manager_sees_all_and_can_export_only(self):
        manager = self.make_user(
            "Sales Manager",
            "call-log-sales-manager",
        )
        agent_1 = self.make_user(
            "Sales User",
            "call-log-manager-agent-1",
        )
        agent_2 = self.make_user(
            "Sales User",
            "call-log-manager-agent-2",
        )

        logs = (
            self.make_call_log(agent_1.name),
            self.make_call_log(agent_2.name),
        )

        for log in logs:
            self.assertTrue(
                frappe.has_permission(
                    "DoubleT Call Log",
                    ptype="read",
                    doc=log,
                    user=manager.name,
                )
            )

            self.assertTrue(
                frappe.has_permission(
                    "DoubleT Call Log",
                    ptype="export",
                    doc=log,
                    user=manager.name,
                )
            )

            for ptype in ("write", "delete"):
                self.assertFalse(
                    frappe.has_permission(
                        "DoubleT Call Log",
                        ptype=ptype,
                        doc=log,
                        user=manager.name,
                    ),
                    msg=(
                        "Sales Manager unexpectedly has "
                        f"{ptype} permission"
                    ),
                )

        self.assertFalse(
            frappe.has_permission(
                "DoubleT Call Log",
                ptype="create",
                user=manager.name,
            )
        )

    def test_call_log_viewer_sees_all_but_cannot_export(self):
        viewer = self.make_user(
            "Call Log Viewer",
            "call-log-viewer",
        )
        agent_1 = self.make_user(
            "Sales User",
            "call-log-viewer-agent-1",
        )
        agent_2 = self.make_user(
            "Sales User",
            "call-log-viewer-agent-2",
        )

        logs = (
            self.make_call_log(agent_1.name),
            self.make_call_log(agent_2.name),
        )

        for log in logs:
            self.assertTrue(
                frappe.has_permission(
                    "DoubleT Call Log",
                    ptype="read",
                    doc=log,
                    user=viewer.name,
                )
            )

            self.assertTrue(
                frappe.has_permission(
                    "DoubleT Call Log",
                    ptype="report",
                    doc=log,
                    user=viewer.name,
                )
            )

            for ptype in (
                "write",
                "delete",
                "export",
            ):
                self.assertFalse(
                    frappe.has_permission(
                        "DoubleT Call Log",
                        ptype=ptype,
                        doc=log,
                        user=viewer.name,
                    ),
                    msg=(
                        "Call Log Viewer unexpectedly has "
                        f"{ptype} permission"
                    ),
                )

        self.assertFalse(
            frappe.has_permission(
                "DoubleT Call Log",
                ptype="create",
                user=viewer.name,
            )
        )

    def test_user_without_call_log_role_is_denied(self):
        ordinary_user = self.make_user(
            None,
            "call-log-no-role",
        )
        agent = self.make_user(
            "Sales User",
            "call-log-no-role-agent",
        )

        log = self.make_call_log(agent.name)

        for ptype in (
            "read",
            "write",
            "delete",
            "report",
            "export",
        ):
            self.assertFalse(
                frappe.has_permission(
                    "DoubleT Call Log",
                    ptype=ptype,
                    doc=log,
                    user=ordinary_user.name,
                ),
                msg=(
                    "Ordinary user unexpectedly has "
                    f"{ptype} permission"
                ),
            )

        self.assertFalse(
            frappe.has_permission(
                "DoubleT Call Log",
                ptype="create",
                user=ordinary_user.name,
            )
        )

    def create_via_api(self, **values):
        payload = {
            "agent": self.api_user.name,
            "call_type": "Incoming",
            "start_time": "2026-10-29T10:00:00+07:00",
            "status": "Completed",
            "external_call_id": self.make_external_id(),
            **values,
        }

        frappe.set_user(self.api_user.name)

        try:
            return create_call_log(**payload)
        finally:
            frappe.set_user("Administrator")

    def test_create_call_log(self):
        phone = self.make_phone()

        result = self.create_via_api(
            from_number=phone,
            duration=30,
        )

        self.assertFalse(result["duplicate"])

        doc = frappe.get_doc(
            "DoubleT Call Log",
            result["name"],
        )

        self.assertEqual(doc.agent, self.api_user.name)
        self.assertEqual(doc.call_type, "Incoming")
        self.assertEqual(doc.status, "Completed")
        self.assertEqual(doc.duration, 30)
        self.assertEqual(
            doc.external_call_id,
            result["external_call_id"],
        )

    def test_phone_normalization_and_lead_match(self):
        local_phone = self.make_phone()
        e164_phone = "+84" + local_phone[1:]

        lead = frappe.get_doc({
            "doctype": "DoubleT Lead",
            "first_name": (
                f"CallLog-{frappe.generate_hash(length=10)}"
            ),
            "phone": local_phone,
        }).insert()

        result = self.create_via_api(
            from_number=e164_phone,
        )

        doc = frappe.get_doc(
            "DoubleT Call Log",
            result["name"],
        )

        self.assertEqual(doc.from_number, e164_phone)
        self.assertEqual(
            doc.reference_doctype,
            "DoubleT Lead",
        )
        self.assertEqual(
            doc.reference_name,
            lead.name,
        )

    def test_external_call_id_is_idempotent(self):
        external_call_id = self.make_external_id()
        phone = self.make_phone()

        first = self.create_via_api(
            external_call_id=external_call_id,
            from_number=phone,
        )

        second = self.create_via_api(
            external_call_id=external_call_id,
            from_number=phone,
        )

        self.assertFalse(first["duplicate"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(first["name"], second["name"])

        self.assertEqual(
            frappe.db.count(
                "DoubleT Call Log",
                {"external_call_id": external_call_id},
            ),
            1,
        )

    def test_sales_user_only_sees_own_logs(self):
        sales_user_1 = self.make_user(
            "Sales User",
            "call-log-sales-1",
        )
        sales_user_2 = self.make_user(
            "Sales User",
            "call-log-sales-2",
        )

        log_1 = frappe.get_doc({
            "doctype": "DoubleT Call Log",
            "agent": sales_user_1.name,
            "call_type": "Incoming",
            "start_time": "2026-10-29 10:00:00",
            "status": "Completed",
            "from_number": self.make_phone(),
            "external_call_id": self.make_external_id(),
        }).insert()

        log_2 = frappe.get_doc({
            "doctype": "DoubleT Call Log",
            "agent": sales_user_2.name,
            "call_type": "Incoming",
            "start_time": "2026-10-29 10:01:00",
            "status": "Completed",
            "from_number": self.make_phone(),
            "external_call_id": self.make_external_id(),
        }).insert()

        frappe.set_user(sales_user_1.name)

        visible_logs = frappe.get_list(
            "DoubleT Call Log",
            pluck="name",
            limit_page_length=0,
        )

        self.assertIn(log_1.name, visible_logs)
        self.assertNotIn(log_2.name, visible_logs)

        own_log = frappe.get_doc(
            "DoubleT Call Log",
            log_1.name,
        )
        own_log.check_permission("read")

        other_log = frappe.get_doc(
            "DoubleT Call Log",
            log_2.name,
        )

        with self.assertRaises(frappe.PermissionError):
            other_log.check_permission("read")


class TestDoubleTCallLogAPIAuth(
    frappe_test_api.FrappeAPITestCase
):
    def tearDown(self):
        frappe_test_api.authorization_token = None
        super().tearDown()

    def test_invalid_api_token_is_rejected(self):
        frappe_test_api.authorization_token = (
            "NonExistentKey:INCORRECT"
        )

        response = self.post(
            self.method("doublet_crm.api.create_call_log"),
            {
                "agent": "Administrator",
                "call_type": "Incoming",
                "start_time": (
                    "2026-10-29T10:00:00+07:00"
                ),
                "status": "Completed",
                "external_call_id": (
                    "invalid-token-call-test"
                ),
            },
        )

        self.assertEqual(response.status_code, 401)
