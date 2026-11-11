import frappe
from frappe.tests.utils import FrappeTestCase

from doublet_crm.patches.setup_default_price_lists import (
    RETAIL_PRICE_LIST,
    WHOLESALE_PRICE_LIST,
    execute,
)


class TestSetupDefaultPriceLists(FrappeTestCase):
    def test_seeding_is_idempotent(self):
        setting_before = frappe.db.get_single_value(
            "DoubleT Pricing Settings", "default_price_list"
        )
        execute()
        before = frappe.get_all(
            "DoubleT Price List",
            filters={"price_list_name": ["in", [RETAIL_PRICE_LIST, WHOLESALE_PRICE_LIST]]},
            pluck="price_list_name",
        )
        execute()
        after = frappe.get_all(
            "DoubleT Price List",
            filters={"price_list_name": ["in", [RETAIL_PRICE_LIST, WHOLESALE_PRICE_LIST]]},
            pluck="price_list_name",
        )

        self.assertEqual(set(before), {RETAIL_PRICE_LIST, WHOLESALE_PRICE_LIST})
        self.assertEqual(after, before)
        default_price_list = frappe.db.get_value(
            "DoubleT Price List", {"is_default": 1}, "name"
        )
        self.assertTrue(default_price_list)
        setting_after = frappe.db.get_single_value(
            "DoubleT Pricing Settings", "default_price_list"
        )
        if setting_before:
            self.assertEqual(setting_after, setting_before)
        else:
            self.assertEqual(setting_after, default_price_list)
