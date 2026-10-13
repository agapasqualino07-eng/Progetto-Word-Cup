import tempfile
import unittest
from pathlib import Path

from dropship.guardrails import KillSwitch, KillSwitchActive
from dropship.orders.service import OrderService
from dropship.orders.suppliers import CJDropshippingSupplier, MockSupplier
from tests.helpers import FakeTransport, make_customer, make_order


class TestOrderService(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.ks = KillSwitch(self.dir, environ={})
        self.supplier = MockSupplier()
        self.svc = OrderService(self.supplier, self.ks, self.dir / "orders.json", known_skus={"SKU-1"})

    def tearDown(self):
        self.tmp.cleanup()

    def test_paid_order_is_forwarded(self):
        r = self.svc.forward(make_order())
        self.assertEqual(r.status, "FORWARDED", r.reasons)
        self.assertEqual(r.supplier_order.source, "MOCK")

    def test_unpaid_order_is_never_forwarded(self):
        r = self.svc.forward(make_order(paid=False))
        self.assertEqual(r.status, "REJECTED")
        self.assertEqual(self.supplier.orders, {})

    def test_unknown_sku_rejected(self):
        r = self.svc.forward(make_order(sku="ALTRO"))
        self.assertEqual(r.status, "REJECTED")

    def test_quantity_limits(self):
        self.assertEqual(self.svc.forward(make_order(order_id="A", quantity=0)).status, "REJECTED")
        self.assertEqual(self.svc.forward(make_order(order_id="B", quantity=50)).status, "REJECTED")

    def test_incomplete_address_rejected(self):
        r = self.svc.forward(make_order(customer=make_customer(address_line="")))
        self.assertEqual(r.status, "REJECTED")

    def test_invalid_country_rejected(self):
        r = self.svc.forward(make_order(customer=make_customer(country="Italia")))
        self.assertEqual(r.status, "REJECTED")

    def test_duplicate_order_not_forwarded_twice(self):
        self.svc.forward(make_order())
        r = self.svc.forward(make_order())
        self.assertEqual(r.status, "DUPLICATE")
        self.assertEqual(len(self.supplier.orders), 1)

    def test_duplicate_detection_persists(self):
        self.svc.forward(make_order())
        svc2 = OrderService(self.supplier, self.ks, self.dir / "orders.json", known_skus={"SKU-1"})
        self.assertEqual(svc2.forward(make_order()).status, "DUPLICATE")

    def test_tracking(self):
        self.svc.forward(make_order())
        t = self.svc.tracking("ORD-1")
        self.assertEqual(t.source, "MOCK")
        self.assertTrue(t.tracking_number)

    def test_tracking_unknown_order(self):
        with self.assertRaises(KeyError):
            self.svc.tracking("NOPE")

    def test_kill_switch_blocks_forwarding(self):
        self.ks.activate("stop")
        with self.assertRaises(KillSwitchActive):
            self.svc.forward(make_order())

    def test_customer_pii_not_in_repr_or_state(self):
        o = make_order()
        self.assertNotIn("Via Roma", repr(o))
        self.assertNotIn("mario@example.com", repr(o))
        self.svc.forward(o)
        state = (self.dir / "orders.json").read_text()
        self.assertNotIn("Via Roma", state)
        self.assertNotIn("mario@example.com", state)


class TestCJSupplier(unittest.TestCase):
    def test_place_order_gets_token_then_creates_order(self):
        t = FakeTransport(
            [
                (200, {"result": True, "data": {"accessToken": "AT"}}),
                (200, {"result": True, "data": {"orderId": "CJ-1", "orderStatus": "CREATED"}}),
            ]
        )
        cj = CJDropshippingSupplier(api_key="key", transport=t)
        res = cj.place_order(make_order())
        self.assertEqual(res.supplier_order_id, "CJ-1")
        self.assertEqual(res.source, "CJ")
        self.assertEqual(t.calls[1]["headers"]["CJ-Access-Token"], "AT")
        body = t.json_body(1)
        self.assertEqual(body["orderNumber"], "ORD-1")
        self.assertEqual(body["products"][0]["quantity"], 1)

    def test_api_failure_raises(self):
        t = FakeTransport([(200, {"result": False, "message": "no"})])
        cj = CJDropshippingSupplier(api_key="key", transport=t)
        with self.assertRaises(RuntimeError):
            cj.place_order(make_order())

    def test_repr_hides_key(self):
        self.assertNotIn("CHIAVE", repr(CJDropshippingSupplier(api_key="CHIAVE")))


if __name__ == "__main__":
    unittest.main()
