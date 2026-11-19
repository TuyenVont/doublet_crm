from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

import frappe

from doublet_crm.api import get_linked_docs_of_document


class TestLinkedDocs(TestCase):
    @patch("doublet_crm.api.get_dynamic_linked_docs", return_value=[])
    @patch("doublet_crm.api.get_linked_docs", return_value=[])
    @patch("doublet_crm.api.frappe.get_doc")
    def test_complete_empty_lookup(self, get_doc, _get_links, _get_dynamic_links):
        source = Mock()
        get_doc.return_value = source

        self.assertEqual(
            get_linked_docs_of_document("DoubleT Lead", "LEAD-001"),
            {"docs": [], "complete": True},
        )
        source.check_permission.assert_called_once_with("read")

    @patch("doublet_crm.api.get_dynamic_linked_docs", return_value=[])
    @patch("doublet_crm.api.get_linked_docs")
    @patch("doublet_crm.api.frappe.get_doc")
    def test_unreadable_link_marks_lookup_incomplete(self, get_doc, get_links, _get_dynamic_links):
        source = Mock()
        linked = Mock()
        linked.has_permission.return_value = False
        get_doc.side_effect = [source, linked]
        get_links.return_value = [
            frappe._dict(reference_doctype="DoubleT Deal", reference_docname="DEAL-001")
        ]

        result = get_linked_docs_of_document("DoubleT Lead", "LEAD-001")

        self.assertEqual(result, {"docs": [], "complete": False})
        linked.apply_fieldlevel_read_permissions.assert_not_called()

    @patch("doublet_crm.api.frappe.get_doc")
    def test_source_read_permission_is_required(self, get_doc):
        source = Mock()
        source.check_permission.side_effect = frappe.PermissionError
        get_doc.return_value = source

        with self.assertRaises(frappe.PermissionError):
            get_linked_docs_of_document("DoubleT Lead", "LEAD-DENIED")
