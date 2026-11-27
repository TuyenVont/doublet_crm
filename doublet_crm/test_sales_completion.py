import unittest
from types import SimpleNamespace
from unittest.mock import patch

import frappe

from doublet_crm.doublet_crm.doctype.doublet_quotation import doublet_quotation


class Record(SimpleNamespace):
    def get(self, key, default=None):
        return getattr(self, key, default)


def reject(message, exc=None, **kwargs):
    raise (exc or frappe.ValidationError)(message)


class TestCurrentDiscountApproval(unittest.TestCase):
    def quotation(self, approval_status="Not Required", approved_by=None, snapshot=None):
        row = Record(
            product="P", quantity=1, unit_price=100,
            discount_type="Percentage", discount_percent=15,
            discount_amount=15, line_total=85,
        )
        doc = Record(
            items=[row], subtotal=100, total_discount=15, grand_total=85,
            approval_status=approval_status, approved_by=approved_by,
            approval_snapshot_hash=snapshot or "",
        )
        return doc

    def test_old_not_required_draft_is_blocked_after_threshold_tightens(self):
        doc = self.quotation()
        settings = {"enabled": True, "threshold_percent": 10, "threshold_amount": 0}
        with patch.object(doublet_quotation, "_discount_approval_settings", return_value=settings), \
             patch.object(frappe, "throw", side_effect=reject), \
             self.assertRaises(frappe.ValidationError):
            doublet_quotation.ensure_quotation_can_send(doc)

    def test_matching_approval_snapshot_allows_send(self):
        doc = self.quotation(approval_status="Approved", approved_by="manager@example.invalid")
        doc.approval_snapshot_hash = doublet_quotation.compute_financial_snapshot_hash(doc)
        settings = {"enabled": True, "threshold_percent": 10, "threshold_amount": 0}
        with patch.object(doublet_quotation, "_discount_approval_settings", return_value=settings):
            doublet_quotation.ensure_quotation_can_send(doc)

    def test_current_non_required_threshold_ignores_stale_status(self):
        doc = self.quotation(approval_status="Rejected")
        settings = {"enabled": True, "threshold_percent": 20, "threshold_amount": 0}
        with patch.object(doublet_quotation, "_discount_approval_settings", return_value=settings):
            doublet_quotation.ensure_quotation_can_send(doc)


if __name__ == "__main__":
    unittest.main()
