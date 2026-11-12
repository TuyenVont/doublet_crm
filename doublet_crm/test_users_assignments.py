from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from doublet_crm.api import (
    get_assigned_users,
    get_assignment_user_info,
    get_assignment_users,
    remove_assignments,
)


class TestUsersAssignments(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.lead = frappe.get_doc({
            "doctype": "DoubleT Lead",
            "first_name": f"Assignment {frappe.generate_hash(length=8)}",
        }).insert()

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_user_payload_and_lookup(self):
        users, assignable = get_assignment_users()
        self.assertTrue(any(user.name == "Administrator" for user in users))
        self.assertEqual({user.name for user in users}, {user.name for user in assignable})
        self.assertTrue(all(user.get("full_name") and "role" in user for user in users))
        self.assertEqual([user.name for user in get_assignment_user_info(["Administrator"])], ["Administrator"])
        with self.assertRaises(frappe.ValidationError):
            get_assignment_user_info("not-a-list")

    def test_assignments_are_scoped_and_removable(self):
        other = frappe.get_doc({"doctype": "DoubleT Lead", "first_name": "Other assignment"}).insert()
        for lead in (self.lead, other):
            frappe.get_doc({
                "doctype": "ToDo", "allocated_to": "Administrator", "status": "Open",
                "reference_type": "DoubleT Lead", "reference_name": lead.name,
                "description": "Assignment test",
            }).insert()
        self.assertEqual(get_assigned_users("DoubleT Lead", self.lead.name), ["Administrator"])
        self.assertEqual(remove_assignments("DoubleT Lead", self.lead.name, ["Administrator"]), [])
        self.assertEqual(get_assigned_users("DoubleT Lead", other.name), ["Administrator"])

    def test_document_permissions_and_doctype_allowlist(self):
        with self.assertRaises(frappe.ValidationError):
            get_assigned_users("User", "Administrator")
        with patch("doublet_crm.api.frappe.has_permission", return_value=False):
            with self.assertRaises(frappe.PermissionError):
                get_assigned_users("DoubleT Lead", self.lead.name)
            with self.assertRaises(frappe.PermissionError):
                remove_assignments("DoubleT Lead", self.lead.name, [])

    def test_user_directory_rejects_guest(self):
        frappe.set_user("Guest")
        with self.assertRaises(frappe.PermissionError):
            get_assignment_users()
        with self.assertRaises(frappe.PermissionError):
            get_assignment_user_info(["Administrator"])
