from datetime import date
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from doublet_crm.reports import (
	BOOKED_ORDER_STATUSES,
	_summarize,
	get_sales_performance,
)


def row(**values):
	return frappe._dict(values)


class TestSalesPerformanceReport(FrappeTestCase):
	def test_summary_uses_order_totals_without_double_counting(self):
		orders = [
			row(name="ORD-1", order_date=date(2026, 11, 1), total=100, deal="DEAL-1"),
			row(name="ORD-2", order_date=date(2026, 11, 1), total=50, deal=None),
			row(name="ORD-3", order_date=date(2026, 11, 2), total=150, deal="DEAL-2"),
		]
		deals = {
			"DEAL-1": row(name="DEAL-1", deal_owner="owner@example.com"),
			"DEAL-2": row(name="DEAL-2", deal_owner=None),
		}

		result = _summarize(orders, deals)

		self.assertEqual(result["booked_sales"], 300)
		self.assertEqual(result["order_count"], 3)
		self.assertEqual(result["average_order_value"], 100)
		self.assertEqual(result["trend"][0]["order_count"], 2)
		self.assertEqual(
			{item["assignment_state"] for item in result["by_salesperson"]},
			{"assigned", "unassigned"},
		)

	@patch("doublet_crm.reports.frappe.get_list")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_api_queries_only_booked_orders_in_the_applied_dates(self, has_permission, get_list):
		has_permission.side_effect = [True, True]
		get_list.side_effect = [
			[
				row(
					name="ORD-1",
					order_date=date(2026, 11, 3),
					status="Confirmed",
					total=125,
					currency="USD",
					deal="DEAL-1",
				)
			],
			[row(name="DEAL-1", deal_title="Real Deal", deal_owner="owner@example.com")],
		]

		result = get_sales_performance("2026-11-01", "2026-11-30")

		order_call = get_list.call_args_list[0]
		self.assertEqual(order_call.args[0], "DoubleT Order")
		self.assertIn(["order_date", "between", [date(2026, 11, 1), date(2026, 11, 30)]], order_call.kwargs["filters"])
		self.assertIn(["status", "in", BOOKED_ORDER_STATUSES], order_call.kwargs["filters"])
		self.assertEqual(result["booked_sales"], 125)
		self.assertEqual(result["recent_orders"][0]["deal"], "DEAL-1")
		self.assertIn("not paid revenue", result["business_definition"])

	@patch("doublet_crm.reports.frappe.get_list")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_salesperson_filter_uses_readable_deal_ownership_consistently(self, has_permission, get_list):
		has_permission.side_effect = [True, True]
		get_list.side_effect = [
			["DEAL-1"],
			[
				row(name="ORD-1", order_date=date(2026, 11, 3), status="Confirmed", total=125, currency="USD", deal="DEAL-1"),
				row(name="ORD-2", order_date=date(2026, 11, 4), status="Completed", total=75, currency="USD", deal="DEAL-2"),
			],
			[
				row(name="DEAL-1", deal_title="Mine", deal_owner="owner@example.com"),
				row(name="DEAL-2", deal_title="Theirs", deal_owner="other@example.com"),
			],
		]

		result = get_sales_performance("2026-11-01", "2026-11-30", "owner@example.com")

		self.assertEqual(result["order_count"], 1)
		self.assertEqual(result["booked_sales"], 125)
		self.assertEqual([item["name"] for item in result["recent_orders"]], ["ORD-1"])
		self.assertEqual(result["by_salesperson"][0]["salesperson"], "owner@example.com")

	@patch("doublet_crm.reports.frappe.has_permission")
	def test_order_permission_is_required_before_any_query(self, has_permission):
		has_permission.side_effect = frappe.PermissionError
		with self.assertRaises(frappe.PermissionError):
			get_sales_performance("2026-11-01", "2026-11-30")

	@patch("doublet_crm.reports.frappe.get_list")
	@patch("doublet_crm.reports.frappe.has_permission")
	def test_unreadable_deals_do_not_expose_deal_ids(self, has_permission, get_list):
		has_permission.side_effect = [True, False]
		get_list.return_value = [
			row(
				name="ORD-1",
				order_date=date(2026, 11, 3),
				status="Confirmed",
				total=125,
				currency="USD",
				deal="DEAL-RESTRICTED",
			)
		]

		result = get_sales_performance("2026-11-01", "2026-11-30")

		self.assertEqual(get_list.call_count, 1)
		self.assertFalse(result["permissions"]["deals"])
		self.assertIsNone(result["recent_orders"][0]["deal"])
		self.assertTrue(result["recent_orders"][0]["deal_restricted"])
		self.assertEqual(result["by_salesperson"][0]["assignment_state"], "restricted")

	def test_reversed_date_range_is_rejected(self):
		with patch("doublet_crm.reports.frappe.has_permission", return_value=True):
			with self.assertRaises(frappe.ValidationError):
				get_sales_performance("2026-11-30", "2026-11-01")
