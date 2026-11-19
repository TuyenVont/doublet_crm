from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

import frappe

from doublet_crm.api import _check_activity_reference, _get_readable_attachments, get_activities


class TestActivityAttachments(TestCase):
    @patch("doublet_crm.api.frappe.has_permission", return_value=False)
    @patch("doublet_crm.api.frappe.db.exists", return_value=True)
    def test_lead_read_permission_is_required(self, _exists, _has_permission):
        with self.assertRaises(frappe.PermissionError):
            _check_activity_reference("DoubleT Lead", "LEAD-DENIED")

    @patch("doublet_crm.api.frappe.get_all")
    def test_empty_attachment_list(self, get_all):
        get_all.return_value = []

        self.assertEqual(_get_readable_attachments("DoubleT Lead", "LEAD-EMPTY"), [])
        self.assertEqual(
            get_all.call_args.kwargs["filters"],
            {"attached_to_doctype": "DoubleT Lead", "attached_to_name": "LEAD-EMPTY"},
        )

    @patch("doublet_crm.api.frappe.get_doc")
    @patch("doublet_crm.api.frappe.get_all")
    def test_filters_unreadable_files_and_keeps_reference_scope(self, get_all, get_doc):
        get_all.return_value = [frappe._dict(name="FILE-READ"), frappe._dict(name="FILE-DENIED")]
        readable = Mock()
        readable.has_permission.return_value = True
        readable.get.side_effect = {
            "name": "FILE-READ",
            "file_name": "readable.pdf",
            "file_url": "/private/files/readable.pdf",
        }.get
        denied = Mock()
        denied.has_permission.return_value = False
        get_doc.side_effect = [readable, denied]

        result = _get_readable_attachments("DoubleT Lead", "LEAD-001")

        self.assertEqual([row.name for row in result], ["FILE-READ"])
        self.assertEqual(
            get_all.call_args.kwargs["filters"],
            {"attached_to_doctype": "DoubleT Lead", "attached_to_name": "LEAD-001"},
        )
        readable.apply_fieldlevel_read_permissions.assert_called_once_with()
        denied.apply_fieldlevel_read_permissions.assert_not_called()

    @patch("doublet_crm.api._get_readable_attachments")
    @patch("doublet_crm.api.get_linked_tasks")
    @patch("doublet_crm.api.get_linked_notes")
    @patch("doublet_crm.api.frappe.get_list")
    @patch("doublet_crm.api.frappe.get_doc")
    @patch("doublet_crm.api.frappe.has_permission")
    @patch("doublet_crm.api._check_activity_reference")
    def test_comment_denial_does_not_block_readable_files(
        self,
        check_reference,
        has_permission,
        get_doc,
        get_list,
        get_linked_notes,
        get_linked_tasks,
        get_attachments,
    ):
        get_doc.return_value = SimpleNamespace(owner="owner@example.com", creation="2026-01-01")
        has_permission.return_value = False
        get_list.return_value = []
        get_attachments.return_value = [frappe._dict(name="FILE-READ")]

        result = get_activities("DoubleT Lead", "LEAD-001")

        check_reference.assert_called_once_with("DoubleT Lead", "LEAD-001")
        self.assertEqual([row.name for row in result[4]], ["FILE-READ"])
        self.assertNotIn("Comment", [call.args[0] for call in get_list.call_args_list])
        get_linked_notes.assert_not_called()
        get_linked_tasks.assert_not_called()
