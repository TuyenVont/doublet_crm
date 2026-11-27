import unittest
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, patch

import frappe

from doublet_crm.doublet_crm.doctype.doublet_quotation import doublet_quotation
from doublet_crm import sales_completion
from doublet_crm.doublet_crm.doctype.doublet_deal.doublet_deal import (
	DoubleTDeal,
	positive_quantity,
	variant_attributes_label,
)


def setUpModule():
	frappe.local.flags = frappe._dict(in_test=True)


class RaisedByFrappe(Exception):
	pass


def row(**values):
	return SimpleNamespace(**values)


class TestDealProductsPure(TestCase):
	def test_positive_quantity_rejects_zero_negative_and_non_finite(self):
		for value in (0, -1, "NaN", "Infinity", None):
			with self.subTest(value=value), \
				patch("doublet_crm.doublet_crm.doctype.doublet_deal.doublet_deal._", side_effect=lambda text: text), \
				patch("frappe.throw", side_effect=RaisedByFrappe):
				with self.assertRaises(RaisedByFrappe):
					positive_quantity(value)

	def test_variant_label_is_snapshot_safe(self):
		product = row(variant_attributes=[row(attribute_name="Color", attribute_value="Blue"), row(attribute_name="", attribute_value="x")])
		self.assertEqual(variant_attributes_label(product), "Color: Blue")

	def test_controller_rejects_duplicate_sku_and_uses_current_pricing(self):
		deal_rows = [row(product="P-1", quantity=1), row(product="P-2", quantity=2)]
		deal = row(deal_type="PERSONAL", contact="C-1", company=None)
		deal.get = lambda field: deal_rows if field == "interested_products" else None
		products = {
			"P-1": row(name="P-1", product_name="One", sku="SAME", variant_attributes=[]),
			"P-2": row(name="P-2", product_name="Two", sku="SAME", variant_attributes=[]),
		}
		with patch("doublet_crm.doublet_crm.doctype.doublet_deal.doublet_deal.readable_doc", side_effect=lambda _doctype, name: products[name]), \
			patch("doublet_crm.doublet_crm.doctype.doublet_deal.doublet_deal.resolve_product_price", return_value={"price": "15.00"}) as pricing, \
			patch("doublet_crm.doublet_crm.doctype.doublet_deal.doublet_deal._", side_effect=lambda text: text), \
			patch("frappe.throw", side_effect=RaisedByFrappe):
			with self.assertRaises(RaisedByFrappe):
				DoubleTDeal.validate_interested_products(deal)
		self.assertEqual(deal_rows[0].reference_price, "15.00")
		self.assertEqual(pricing.call_count, 1)

	def test_controller_propagates_unsellable_product_rejection_from_pricing_validation(self):
		deal_row = row(product="P-1", quantity=1)
		deal = row(deal_type="PERSONAL", contact="C-1", company=None)
		deal.get = lambda field: [deal_row] if field == "interested_products" else None
		product = row(name="P-1", product_name="Template", sku="SKU-1", variant_attributes=[])
		with patch("doublet_crm.doublet_crm.doctype.doublet_deal.doublet_deal.readable_doc", return_value=product), \
			patch("doublet_crm.doublet_crm.doctype.doublet_deal.doublet_deal.resolve_product_price", side_effect=RaisedByFrappe):
			with self.assertRaises(RaisedByFrappe):
				DoubleTDeal.validate_interested_products(deal)


class TestSalesCompletionMocked(TestCase):
	def test_quotation_context_reprices_without_mutating_deal_or_amount(self):
		product = row(name="VAR-1", product_name="Variant", sku="SKU-1")
		deal_item = row(product="VAR-1", quantity=2)
		deal = row(
			name="DEAL-1", deal_title="Deal", deal_type="PERSONAL", contact="CONTACT-1", company=None,
			source_lead="LEAD-1", interested_products=[deal_item], amount=999,
		)
		with patch("doublet_crm.sales_completion.readable_doc", side_effect=lambda doctype, _name: product if doctype == "DoubleT Product" else row(name="CONTACT-1")), \
			patch("doublet_crm.sales_completion.resolve_product_price", return_value={"price": "25.00", "price_list": "PL-1", "source": "price_list"}):
			result = sales_completion._quotation_context(deal)
		self.assertEqual(result["items"][0]["unit_price"], "25.00")
		self.assertEqual(result["source_lead"], "LEAD-1")
		self.assertEqual(deal.amount, 999)
		self.assertEqual(deal_item.quantity, 2)

	def test_api_requires_quotation_create_and_returns_conversion_guidance(self):
		lead = row(name="LEAD-1", status="QUALIFIED", converted_deal=None)
		with patch("doublet_crm.sales_completion.frappe.has_permission") as permission, \
			patch("doublet_crm.sales_completion.readable_doc", return_value=lead), \
			patch("doublet_crm.sales_completion._", side_effect=lambda text: text), \
			patch("doublet_crm.sales_completion._lead_deal_names", return_value=[]):
			result = sales_completion.get_quotation_draft_context(lead_name="LEAD-1")
		permission.assert_called_once_with("DoubleT Quotation", "create", throw=True)
		self.assertTrue(result["conversion_required"])

	def test_invalid_lead_status_is_rejected_by_backend(self):
		lead = row(name="LEAD-1", status="CONTACTED", converted_deal=None)
		with patch("doublet_crm.sales_completion.frappe.has_permission"), \
			patch("doublet_crm.sales_completion.readable_doc", return_value=lead), \
			patch("doublet_crm.sales_completion._", side_effect=lambda text: text), \
			patch("doublet_crm.sales_completion.frappe.throw", side_effect=RaisedByFrappe):
			with self.assertRaises(RaisedByFrappe):
				sales_completion.get_quotation_draft_context(lead_name="LEAD-1")

	def test_multiple_readable_lead_deals_require_explicit_selection(self):
		lead = row(name="LEAD-1", status="QUALIFIED", converted_deal=None)
		deals = {
			"D-1": row(name="D-1", deal_title="First", source_lead="LEAD-1"),
			"D-2": row(name="D-2", deal_title="Second", source_lead="LEAD-1"),
		}
		with patch("doublet_crm.sales_completion.frappe.has_permission"), \
			patch("doublet_crm.sales_completion.readable_doc", return_value=lead), \
			patch("doublet_crm.sales_completion._lead_deal_names", return_value=["D-1", "D-2"]), \
			patch("doublet_crm.sales_completion._readable_deal", side_effect=lambda name: deals[name]):
			result = sales_completion.get_quotation_draft_context(lead_name="LEAD-1")
		self.assertTrue(result["requires_deal_selection"])
		self.assertEqual([choice["name"] for choice in result["deals"]], ["D-1", "D-2"])

	def test_single_linked_deal_builds_draft_without_creating_records(self):
		lead = row(name="LEAD-1", status="QUALIFIED", converted_deal=None)
		deal = row(name="D-1", deal_title="Only", source_lead="LEAD-1")
		with patch("doublet_crm.sales_completion.frappe.has_permission"), \
			patch("doublet_crm.sales_completion.readable_doc", return_value=lead), \
			patch("doublet_crm.sales_completion._lead_deal_names", return_value=["D-1"]), \
			patch("doublet_crm.sales_completion._readable_deal", return_value=deal), \
			patch("doublet_crm.sales_completion._quotation_context", return_value={"deal": "D-1", "items": []}) as context:
			result = sales_completion.get_quotation_draft_context(lead_name="LEAD-1")
		self.assertEqual(result["deal"], "D-1")
		context.assert_called_once_with(deal, "LEAD-1")

	def test_save_replaces_only_product_table_and_preserves_amount(self):
		deal = MagicMock()
		deal.name = "DEAL-1"
		deal.modified = "2026-11-26 00:00:00"
		deal.amount = 500
		deal.interested_products = []
		def append(_field, values):
			deal.interested_products.append(row(name=None, product=values["product"], quantity=values["quantity"], product_name="", sku="", variant_attributes="", reference_price=0))
		deal.append.side_effect = append
		with patch("doublet_crm.sales_completion._readable_deal", return_value=deal) as readable, \
			patch("doublet_crm.sales_completion._safe_product_rows", return_value=[]):
			sales_completion.save_deal_products("DEAL-1", [{"product": "P-1", "quantity": 2}], modified=str(deal.modified))
		readable.assert_called_once_with("DEAL-1", "write")
		deal.save.assert_called_once()
		self.assertEqual(deal.amount, 500)
		self.assertEqual(deal.interested_products[0].product, "P-1")

	def test_deal_product_read_does_not_expose_unreadable_product_snapshot(self):
		deal = row(interested_products=[row(product="SECRET", name="ROW-1", product_name="Secret", sku="SECRET", variant_attributes="", quantity=1, reference_price=1)])
		with patch("doublet_crm.sales_completion.readable_doc", side_effect=RaisedByFrappe):
			with self.assertRaises(RaisedByFrappe):
				sales_completion._safe_product_rows(deal)


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
