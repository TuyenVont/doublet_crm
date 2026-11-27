"""Database-free controller checks; persistence and DB locks need site integration tests."""

import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import frappe

from doublet_crm.doublet_crm.doctype.doublet_order import doublet_order as module


class Record(SimpleNamespace):
    def get(self, key, default=None):
        return getattr(self, key, default)


class OrderHarness(module.DoubleTOrder):
    """Exercise the production controller without metadata queries or DB writes."""
    def __init__(self, values=None, previous=None):
        self.__dict__.update(
            doctype="DoubleT Order", name=None, status="Draft", order_date="2026-11-16",
            customer_type="COMPANY", contact=None, company="CO", deal=None,
            quotation=None, currency="USD", notes=None, previous=previous,
            items=[Record(name=None, product="P", product_name=None, sku=None,
                          quantity=2, unit_price="19.99", discount_type="Percentage",
                          discount_percent=10, discount_amount=0)],
        )
        self.__dict__.update(values or {})
        self.items = [Record(**{"name": None, "product_name": None, "sku": None, **row}) if isinstance(row, dict) else row for row in self.items]

    def get_doc_before_save(self):
        return self.previous

    def has_value_changed(self, field):
        return self.get(field) != self.previous.get(field)

    def insert(self):
        self.validate()
        self.name = "ORD-00001"
        return self

    def check_permission(self, permission):
        return True


def reject(message, exc=None, **kwargs):
    raise (exc or frappe.ValidationError)(message)


class TestOrderController(unittest.TestCase):
    def setUp(self):
        self.product = Record(product_name="Current Product", sku="P", is_sellable=lambda: True)
        self.company = Record(name="CO")
        self.contact = Record(name="C", company="CO")
        self.documents = {("DoubleT Product", "P"): self.product,
                          ("DoubleT Company", "CO"): self.company,
                          ("DoubleT Contact", "C"): self.contact}
        def readable(doctype, name):
            return self.documents[(doctype, name)]
        # Quotation's customer validator resolves its own readable_doc global.
        from doublet_crm.doublet_crm.doctype.doublet_quotation import doublet_quotation
        for target in (patch.object(module, "_", side_effect=lambda text: text),
                       patch.object(doublet_quotation, "_", side_effect=lambda text: text),
                       patch.object(module, "nowdate", return_value="2026-11-16"),
                       patch.object(module, "readable_doc", side_effect=readable),
                       patch.object(doublet_quotation, "readable_doc", side_effect=readable),
                       patch.object(frappe, "throw", side_effect=reject)):
            target.start()
            self.addCleanup(target.stop)

    def quote(self):
        source = Record(name="QUO-1", status="Accepted", customer_type="COMPANY", company="CO", contact=None,
                        deal=None, currency=None, subtotal="39.98", total_discount="4.00",
                        grand_total="35.98", items=[Record(product="P", product_name="Stored Product",
                        sku="OLD-SKU", quantity=2, unit_price="19.99", discount_type="Percentage",
                        discount_percent=10, discount_amount="4.00", line_total="35.98")])
        return source

    def test_manual_order_and_usd_rounding(self):
        order = OrderHarness()
        order.validate()
        self.assertEqual((order.subtotal, order.total_discount, order.total),
                         (Decimal("39.98"), Decimal("4.00"), Decimal("35.98")))
        self.assertEqual(order.items[0].subtotal, Decimal("35.98"))
        self.assertEqual(order.items[0].product_name, "Current Product")

    def test_amount_discount(self):
        order = OrderHarness()
        order.items[0].discount_type = "Amount"
        order.items[0].discount_percent = 0
        order.items[0].discount_amount = 5
        order.validate()
        self.assertEqual(order.total, Decimal("34.98"))

    def test_invalid_numbers_and_discounts(self):
        for field, value in (("quantity", 0), ("quantity", "NaN"), ("quantity", "Infinity"),
                             ("unit_price", -1), ("unit_price", ""), ("unit_price", "NaN"),
                             ("discount_percent", 101), ("discount_percent", -1),
                             ("discount_type", "Other")):
            with self.subTest(field=field, value=value), self.assertRaises(frappe.ValidationError):
                order = OrderHarness()
                setattr(order.items[0], field, value)
                order.validate()
        for amount, percent in ((40, 0), (-1, 0), (2, 1)):
            order = OrderHarness()
            order.items[0].discount_type = "Amount"
            order.items[0].discount_amount, order.items[0].discount_percent = amount, percent
            with self.assertRaises(frappe.ValidationError):
                order.validate()

    def test_required_rows_date_and_currency(self):
        for values in ({"items": []}, {"order_date": None}, {"currency": "EUR"}):
            with self.subTest(values=values), self.assertRaises(frappe.ValidationError):
                OrderHarness(values).validate()

    def test_customer_consistency(self):
        for values in ({"customer_type": "OTHER"}, {"customer_type": "PERSONAL"},
                       {"company": None}, {"contact": "C", "company": "OTHER"}):
            if values.get("company") == "OTHER":
                self.documents[("DoubleT Company", "OTHER")] = Record(name="OTHER")
            with self.subTest(values=values), self.assertRaises(frappe.ValidationError):
                OrderHarness(values).validate()
        OrderHarness({"customer_type": "PERSONAL", "company": None, "contact": "C"}).validate()

    def test_deal_must_match_customer(self):
        meta = Record(get_field=lambda _: Record(permlevel=0), get_permlevel_access=lambda _: [0])
        self.documents[("DoubleT Deal", "D")] = Record(
            deal_type="COMPANY", company="CO", contact=None, meta=meta)
        from doublet_crm.doublet_crm.doctype.doublet_quotation import doublet_quotation
        with patch.object(doublet_quotation.frappe, "session", Record(user="Administrator")):
            OrderHarness({"deal": "D"}).validate()
            with self.assertRaises(frappe.ValidationError):
                OrderHarness({"deal": "D", "contact": "C"}).validate()

    def test_product_access_and_sellability(self):
        self.product.is_sellable = lambda: False
        with self.assertRaises(frappe.ValidationError):
            OrderHarness().validate()
        with patch.object(module, "readable_doc", side_effect=frappe.PermissionError):
            with self.assertRaises(frappe.PermissionError):
                OrderHarness().validate()

    def test_lifecycle_and_locked_data(self):
        for initial, targets in module.TRANSITIONS.items():
            for target in module.TRANSITIONS:
                old = OrderHarness({"status": initial})
                new = OrderHarness({"status": target}, previous=old)
                if target in targets:
                    new.validate_lifecycle(old)
                else:
                    with self.assertRaises(frappe.ValidationError):
                        new.validate_lifecycle(old)
        with self.assertRaises(frappe.ValidationError):
            OrderHarness({"status": "Confirmed"}).validate()
        for field in module.LOCKED_FIELDS:
            old = OrderHarness({"status": "Confirmed"})
            new = OrderHarness({"status": "Completed", field: "changed"}, previous=old)
            with self.subTest(field=field), self.assertRaises(frappe.ValidationError):
                new.validate_lifecycle(old)
        old = OrderHarness({"status": "Confirmed"})
        new = OrderHarness({"status": "Completed"}, previous=old)
        new.items[0].quantity = 3
        with self.assertRaises(frappe.ValidationError):
            new.validate_lifecycle(old)

    def test_locked_derived_totals_are_restored(self):
        old = OrderHarness()
        old.validate()
        old.status = "Confirmed"
        new = OrderHarness({"status": "Completed", "items": copy.deepcopy(old.items),
                            "total": 999}, previous=old)
        new.items[0].subtotal = 999
        new.validate()
        self.assertEqual(new.total, old.total)
        self.assertEqual(new.items[0].subtotal, old.items[0].subtotal)

    def test_delete_only_draft(self):
        OrderHarness().on_trash()
        for status in ("Confirmed", "Completed", "Cancelled"):
            with self.assertRaises(frappe.ValidationError):
                OrderHarness({"status": status}).on_trash()

    def convert(self, source, existing=None):
        def get_doc(values):
            return OrderHarness(values)
        with patch.object(module, "lock_quotation", return_value=source) as lock, \
             patch.object(frappe, "db", Record(get_value=Mock(return_value=existing))), \
             patch.object(frappe, "get_doc", side_effect=get_doc), \
             patch.object(frappe, "has_permission", side_effect=(frappe.PermissionError if existing else None), return_value=True):
            self.documents[("DoubleT Quotation", source.name)] = source
            result = module.create_order_from_quotation.__wrapped__(source.name)
            lock.assert_called_with(source.name)
            return result

    def test_conversion_preserves_stored_prices_and_inactive_product_snapshot(self):
        source = self.quote()
        self.product.is_sellable = lambda: False
        orders = []
        original = OrderHarness.insert
        def capture(order):
            orders.append(order)
            return original(order)
        with patch.object(OrderHarness, "insert", capture):
            self.assertEqual(self.convert(source), "ORD-00001")
        order = orders[0]
        self.assertEqual(order.total, Decimal("35.98"))
        self.assertEqual(order.items[0].product_name, "Stored Product")
        self.assertEqual(order.items[0].sku, "OLD-SKU")
        self.assertEqual(order.items[0].unit_price, "19.99")
        self.assertEqual((order.status, order.currency), ("Draft", "USD"))

    def test_conversion_amount_discount_and_corrupt_totals(self):
        source = self.quote()
        source.items[0].discount_type = "Amount"
        source.items[0].discount_percent = 0
        self.assertEqual(self.convert(source), "ORD-00001")
        source.grand_total = "999"
        with self.assertRaises(frappe.ValidationError):
            self.convert(source)

    def test_repeat_returns_readable_order_without_create_permission(self):
        source = self.quote()
        self.documents[("DoubleT Quotation", source.name)] = source
        self.documents[("DoubleT Order", "EXISTING")] = Record(name="EXISTING")
        self.assertEqual(self.convert(source, "EXISTING"), "EXISTING")
        with patch.object(module, "readable_doc", side_effect=[source, frappe.PermissionError("denied")]):
            with self.assertRaises(frappe.PermissionError):
                self.convert(source, "EXISTING")

    def test_create_permission_is_required_before_insert(self):
        source = self.quote()
        self.documents[("DoubleT Quotation", source.name)] = source
        with patch.object(module, "lock_quotation", return_value=source), \
             patch.object(frappe, "db", Record(get_value=Mock(return_value=None))), \
             patch.object(frappe, "has_permission", side_effect=frappe.PermissionError), \
             patch.object(OrderHarness, "insert") as insert:
            with self.assertRaises(frappe.PermissionError):
                module.create_order_from_quotation.__wrapped__(source.name)
            insert.assert_not_called()

    def test_quotation_links_and_currency_must_match(self):
        source = self.quote()
        with patch.object(module, "lock_quotation", return_value=source):
            for values in ({"contact": "C"}, {"deal": "OTHER"}):
                order = OrderHarness({"quotation": source.name, **values})
                with self.assertRaises(frappe.ValidationError):
                    order.validate_quotation(None)
        old = OrderHarness({"quotation": "QUO-1"})
        with self.assertRaises(frappe.ValidationError):
            OrderHarness({"quotation": "QUO-2"}, previous=old).validate_lifecycle(old)

    def test_direct_link_requires_accepted_and_exact_snapshot(self):
        source = self.quote()
        with patch.object(module, "lock_quotation", return_value=source):
            matching = OrderHarness({
                "quotation": source.name,
                "items": [{
                    "product": "P", "quantity": 2, "unit_price": "19.99",
                    "discount_type": "Percentage", "discount_percent": 10,
                    "discount_amount": "4.00",
                }],
            })
            self.assertIs(matching.validate_quotation(None), source)
            source.status = "Sent"
            with self.assertRaises(frappe.ValidationError):
                matching.validate_quotation(None)
            source.status = "Accepted"
            matching.items[0].quantity = 3
            with self.assertRaises(frappe.ValidationError):
                matching.validate_quotation(None)

    def test_lock_loads_current_source_and_checks_read_access(self):
        doc = Record(check_permission=Mock())
        with patch.object(frappe, "get_doc", return_value=doc) as get_doc:
            self.assertIs(module.lock_quotation("QUO-1"), doc)
            get_doc.assert_called_once_with("DoubleT Quotation", "QUO-1", for_update=True)
            doc.check_permission.assert_called_once_with("read")

    def test_multiple_quotation_lines_survive_changed_live_prices_and_repeat(self):
        from doublet_crm.doublet_crm.doctype.doublet_quotation import doublet_quotation

        prices = {"P": "19.99", "P2": "12.35", "P3": "0.29"}
        for product in ("P2", "P3"):
            self.documents[("DoubleT Product", product)] = Record(
                product_name=product, sku=product, is_sellable=lambda: True)
        source = self.quote()
        source.price_list = "Retail"
        source.items = [Record(
            name=None, product=product, quantity=quantity, unit_price=None,
            discount_type=kind, discount_percent=percent, discount_amount=amount,
        ) for product, quantity, kind, percent, amount in (
            ("P", 2, "Percentage", 10, 0),
            ("P2", 3, "Amount", 0, "1.11"),
            ("P3", "1.5", "Percentage", 0, 0),
        )]
        def initial_price(product, *args, **kwargs):
            key = product.sku if product.sku != "P" else "P"
            return {"price": Decimal(prices[key]), "source": "price_list", "price_list": "Retail"}
        with patch.object(doublet_quotation, "resolve_product_price", side_effect=initial_price):
            doublet_quotation.DoubleTQuotation.validate_items_and_calculate(source, None)
        # Model a saved snapshot, then change the live Price List and Product values.
        for index, row in enumerate(source.items):
            row.name = f"QI-{index}"
        source = copy.deepcopy(source)
        prices.update({"P": "999.99", "P2": "888.88", "P3": "777.77"})
        self.product.price = "999.99"
        orders = []
        original = OrderHarness.insert
        def capture(order):
            orders.append(order)
            return original(order)
        with patch.object(doublet_quotation, "resolve_product_price", side_effect=AssertionError("repriced")), \
             patch.object(OrderHarness, "insert", capture):
            name = self.convert(source)
        self.assertEqual(len(orders), 1)
        order = orders[0]
        expected_lines = (Decimal("35.98"), Decimal("35.94"), Decimal("0.44"))
        for quoted, actual, expected in zip(source.items, order.items, expected_lines):
            with self.subTest(product=quoted.product):
                self.assertEqual(actual.product, quoted.product)
                self.assertEqual(Decimal(str(actual.quantity)), Decimal(str(quoted.quantity)))
                self.assertEqual(Decimal(str(actual.unit_price)), Decimal(str(quoted.unit_price)))
                self.assertEqual(actual.subtotal, quoted.line_total)
                self.assertEqual(actual.subtotal, expected)
        self.assertEqual(order.currency, source.get("currency") or "USD")
        self.assertEqual(order.subtotal, Decimal("77.47"))
        self.assertEqual(order.total_discount, Decimal("5.11"))
        self.assertEqual(order.total, source.grand_total)
        self.assertEqual(order.total, Decimal("72.36"))
        self.documents[("DoubleT Order", name)] = order
        with patch.object(OrderHarness, "insert") as insert:
            self.assertEqual(self.convert(source, existing=name), name)
            insert.assert_not_called()

    def test_manual_draft_edit_retains_price_and_updates_totals(self):
        old = OrderHarness()
        old.validate()
        old.items[0].name = "ROW"
        edited = OrderHarness({"items": copy.deepcopy(old.items)}, previous=old)
        edited.items[0].quantity = 3
        self.product.price = "999.99"
        edited.validate()
        self.assertEqual(edited.items[0].unit_price, "19.99")
        self.assertEqual(edited.total, Decimal("53.97"))

    def test_role_permissions_from_versioned_schemas(self):
        from frappe.permissions import get_role_permissions

        base = Path(__file__).parent.parent
        for folder in ("doublet_product_category", "doublet_product", "doublet_quotation", "doublet_order"):
            schema = json.loads((base / folder / f"{folder}.json").read_text())
            meta = frappe._dict(name=schema["name"], permissions=[frappe._dict(row) for row in schema["permissions"]])
            for role, expected in (("System Manager", (1, 1, 1, 1)), ("Sales Manager", (1, 1, 1, 1)),
                                   ("Sales User", (1, 1, 1, 0)), ("Guest", (0, 0, 0, 0))):
                with self.subTest(doctype=meta.name, role=role), \
                     patch.object(frappe, "local", Record(role_permissions={})), \
                     patch.object(frappe, "get_roles", return_value=[role]):
                    actual = get_role_permissions(meta, user="isolated@example.invalid")
                    self.assertEqual(tuple(actual[key] for key in ("read", "create", "write", "delete")), expected)

    def test_schema_roles_and_unique_source(self):
        schema = json.loads(Path(__file__).with_name("doublet_order.json").read_text())
        fields = {field["fieldname"]: field for field in schema["fields"]}
        self.assertEqual(fields["quotation"]["unique"], 1)
        for permission in schema["permissions"]:
            self.assertEqual(tuple(permission[key] for key in ("read", "create", "write")), (1, 1, 1))
            self.assertEqual(permission.get("delete", 0), int(permission["role"] != "Sales User"))
        self.assertNotIn("Guest", [row["role"] for row in schema["permissions"]])


if __name__ == "__main__":
    unittest.main()
