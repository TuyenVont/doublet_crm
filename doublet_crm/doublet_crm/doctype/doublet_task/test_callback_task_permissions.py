from contextlib import contextmanager
from copy import deepcopy
from unittest.mock import patch

import frappe
from frappe.client import delete, get, get_list, insert, set_value
from frappe.share import add_docshare
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime

from doublet_crm import contact_center_calls as calls
from doublet_crm.calls_demo import _user
from doublet_crm.doublet_crm.doctype.doublet_task.doublet_task import revoke_callback_task_shares

TASK = "DoubleT Task"


class TestCallbackTaskPermissions(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        key = frappe.generate_hash(length=10)
        self.sales_a = _user(f"permissions-a-{key}@example.com", "Task Scope A", "Sales User")
        self.sales_b = _user(f"permissions-b-{key}@example.com", "Task Scope B", "Sales User")
        self.manager = _user(f"permissions-manager-{key}@example.com", "Task Scope Manager", "Sales Manager")
        self.system_manager = _user(f"permissions-system-{key}@example.com", "Task Scope System", "System Manager")

    def tearDown(self):
        frappe.set_user("Administrator")
        super().tearDown()

    def make_task(self, owner):
        task = frappe.get_doc({"doctype": TASK, "title": "Ordinary task"}).insert()
        task.db_set("owner", owner, update_modified=False)
        return task

    def make_callback(self):
        call = frappe.get_doc({
            "doctype": calls.CALL_LOG,
            "agent": self.sales_a,
            "call_type": "Incoming",
            "status": "Missed",
            "start_time": now_datetime(),
        }).insert()
        calls.assign_call(call.name, self.sales_a)
        task = calls.open_callback(call.name)["callback_task"]["name"]
        calls.assign_call(call.name, self.sales_b)
        return task

    @contextmanager
    def task_permissions(self, rules=None):
        get_meta = frappe.get_meta
        meta = deepcopy(get_meta(TASK))
        meta.permissions = (
            frappe.get_doc("DocType", TASK).permissions
            if rules is None
            else [frappe._dict({"doctype": "Custom DocPerm", "permlevel": 0, **rule}) for rule in rules]
        )
        with (
            patch.object(frappe, "get_meta", side_effect=lambda doctype, *args, **kwargs:
                meta if doctype == TASK else get_meta(doctype, *args, **kwargs)),
            patch.object(frappe.local, "role_permissions", {}),
        ):
            yield

    def assert_visible_tasks(self, names, expected):
        listed = {row.name for row in get_list(TASK, filters={"name": ["in", names]})}
        self.assertEqual(listed, set(expected))
        for name in names:
            if name in expected:
                self.assertEqual(get(TASK, name)["name"], name)
            else:
                with self.assertRaises(frappe.PermissionError):
                    get(TASK, name)

    def test_stock_role_permissions_keep_ordinary_and_callback_scope_separate(self):
        with self.task_permissions():
            ordinary = self.make_task(self.sales_a).name
            callback = self.make_callback()
            names = [ordinary, callback]
            for user, expected in (
                (self.sales_a, []),
                (self.sales_b, [callback]),
                (self.manager, [callback]),
                (self.system_manager, names),
            ):
                with self.subTest(user=user):
                    frappe.set_user(user)
                    self.assert_visible_tasks(names, expected)

            changed = set_value(TASK, ordinary, "status", "Done")
            self.assertEqual(changed["status"], "Done")
            created = insert({"doctype": TASK, "title": "Ordinary CRUD"})
            delete(TASK, created["name"])
            self.assertFalse(frappe.db.exists(TASK, created["name"]))

    def test_existing_role_permissions_and_owner_scope_still_apply_to_ordinary_tasks(self):
        first = self.make_task(self.sales_a).name
        second = self.make_task(self.sales_b).name
        with self.task_permissions([
            {"role": "Sales User", "read": 1, "write": 1, "if_owner": 1},
            {"role": "Sales Manager", "read": 1},
        ]):
            frappe.set_user(self.sales_a)
            self.assert_visible_tasks([first, second], [first])
            self.assertEqual(set_value(TASK, first, "status", "Done")["status"], "Done")
            with self.assertRaises(frappe.PermissionError):
                set_value(TASK, second, "status", "Done")
            frappe.set_user(self.sales_b)
            self.assert_visible_tasks([first, second], [second])
            frappe.set_user(self.manager)
            self.assert_visible_tasks([first, second], [first, second])

    def test_mixed_stock_sales_and_delegated_owner_role_preserves_ordinary_scope(self):
        first = self.make_task(self.sales_a).name
        second = self.make_task(self.sales_b).name
        callback = self.make_callback()
        get_roles = frappe.get_roles
        delegated = "Delegated Ordinary Task Owner"

        def roles_with_delegation(user=None, *args, **kwargs):
            roles = get_roles(user, *args, **kwargs)
            if (user or frappe.session.user) in {self.sales_a, self.sales_b}:
                return [*roles, delegated]
            return roles

        with (
            self.task_permissions([
                {"doctype": "DocPerm", "role": "Sales User", "read": 1},
                {"doctype": "DocPerm", "role": delegated, "read": 1, "if_owner": 1},
            ]),
            patch.object(frappe, "get_roles", side_effect=roles_with_delegation),
        ):
            frappe.set_user(self.sales_a)
            self.assert_visible_tasks([first, second, callback], [first])
            frappe.set_user(self.sales_b)
            self.assert_visible_tasks([first, second, callback], [second, callback])

    def test_ordinary_share_survives_and_callback_share_is_revoked(self):
        with self.task_permissions():
            ordinary = self.make_task("Administrator").name
            callback = self.make_callback()
            add_docshare(TASK, ordinary, self.sales_a)
            with self.assertRaises(frappe.PermissionError):
                add_docshare(TASK, callback, self.sales_a)

            # Simulate a stored share created before callback sharing was blocked.
            legacy_share = frappe.get_doc({
                "doctype": "DocShare",
                "share_doctype": TASK,
                "share_name": callback,
                "user": self.sales_a,
                "read": 1,
            })
            legacy_share.set_new_name()
            legacy_share.db_insert()
            revoke_callback_task_shares()
            revoke_callback_task_shares()
            self.assertEqual(frappe.db.get_value("DocShare", legacy_share.name, "read"), 0)
            frappe.set_user(self.sales_a)
            self.assert_visible_tasks([ordinary, callback], [ordinary])
