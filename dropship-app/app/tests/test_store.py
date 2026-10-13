import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from dropship.catalog.pricing import suggest_price
from dropship.config import PricingConfig
from dropship.guardrails import ApprovalStore, KillSwitch, KillSwitchActive
from dropship.guardrails.approvals import PUBLISH_PRODUCT
from dropship.models import ProductCopy
from dropship.store.copywriter import AnthropicCopywriter, MockCopywriter
from dropship.store.listing import build_listing, slugify
from dropship.store.publishers import MockStorePublisher, ShopifyStorePublisher
from dropship.store.service import publish_product
from dropship.store.static_site import write_static_site
from tests.helpers import FakeTransport, make_candidate

PC = PricingConfig()


def quote_for(c):
    return suggest_price(c.supplier_cost, c.shipping_cost, PC, c.market_price)


class TestListing(unittest.TestCase):
    def test_slugify_is_safe(self):
        self.assertEqual(slugify("Lampada LED è Bella!"), "lampada-led-e-bella")
        self.assertEqual(slugify("../../etc/passwd"), "etc-passwd")
        self.assertEqual(slugify("<<>>"), "prodotto")

    def test_shopify_payload_shape(self):
        c = make_candidate()
        copy = MockCopywriter().generate(c, quote_for(c))
        payload = build_listing(c, quote_for(c), copy)
        p = payload["product"]
        self.assertEqual(p["status"], "draft")
        self.assertEqual(p["variants"][0]["sku"], "SKU-1")
        self.assertEqual(p["variants"][0]["price"], "39.90")
        self.assertTrue(p["variants"][0]["taxable"])
        self.assertIn("source:MOCK", p["tags"])

    def test_body_html_escapes_supplier_text(self):
        c = make_candidate(description="<script>alert(1)</script>")
        copy = ProductCopy(
            title="<img src=x onerror=alert(1)>",
            description="<script>alert(1)</script>",
            bullets=("<b>ok</b>",),
            source="MOCK",
        )
        p = build_listing(c, quote_for(c), copy)["product"]
        self.assertNotIn("<script>", p["body_html"])
        self.assertNotIn("<b>ok</b>", p["body_html"])
        self.assertIn("&lt;script&gt;", p["body_html"])


class TestStaticSite(unittest.TestCase):
    def test_writes_index_and_product_pages_escaped(self):
        c = make_candidate(title="<script>x</script>")
        copy = ProductCopy(title=c.title, description="d", bullets=("a",), source="MOCK")
        listing = build_listing(c, quote_for(c), copy)
        with tempfile.TemporaryDirectory() as tmp:
            files = write_static_site([listing], Path(tmp))
            names = sorted(f.name for f in files)
            self.assertIn("index.html", names)
            for f in files:
                html = f.read_text()
                self.assertNotIn("<script>x</script>", html)
                self.assertIn("Content-Security-Policy", html)
                self.assertTrue(f.resolve().is_relative_to(Path(tmp).resolve()))

    def test_mock_content_is_labelled(self):
        c = make_candidate()
        copy = MockCopywriter().generate(c, quote_for(c))
        listing = build_listing(c, quote_for(c), copy)
        with tempfile.TemporaryDirectory() as tmp:
            files = write_static_site([listing], Path(tmp))
            self.assertIn("MOCK", (Path(tmp) / "index.html").read_text())
            self.assertEqual(len(files), 2)


class TestCopywriters(unittest.TestCase):
    def test_mock_copy_is_marked_mock(self):
        c = make_candidate()
        copy = MockCopywriter().generate(c, quote_for(c))
        self.assertEqual(copy.source, "MOCK")
        self.assertTrue(copy.title)
        self.assertTrue(copy.bullets)

    def test_anthropic_copywriter_uses_injected_client(self):
        class Block:
            type = "text"
            text = '{"title": "T", "description": "D", "bullets": ["a", "b"]}'

        class Resp:
            stop_reason = "end_turn"
            content = [Block()]

        class Messages:
            def __init__(self):
                self.kwargs = None

            def create(self, **kwargs):
                self.kwargs = kwargs
                return Resp()

        class Beta:
            def __init__(self):
                self.messages = Messages()

        class Client:
            def __init__(self):
                self.beta = Beta()

        client = Client()
        cw = AnthropicCopywriter(api_key="k", client=client)
        c = make_candidate()
        copy = cw.generate(c, quote_for(c))
        self.assertEqual(copy.title, "T")
        self.assertEqual(copy.bullets, ("a", "b"))
        self.assertEqual(copy.source, "ANTHROPIC")
        self.assertEqual(client.beta.messages.kwargs["model"], "claude-opus-5-5")

    def test_anthropic_refusal_raises(self):
        class Resp:
            stop_reason = "refusal"
            content = []

        class Client:
            class beta:
                class messages:
                    @staticmethod
                    def create(**kw):
                        return Resp()

        cw = AnthropicCopywriter(api_key="k", client=Client())
        c = make_candidate()
        with self.assertRaises(RuntimeError):
            cw.generate(c, quote_for(c))

    def test_repr_hides_api_key(self):
        cw = AnthropicCopywriter(api_key="sk-segretissima", client=object())
        self.assertNotIn("sk-segretissima", repr(cw))


class TestShopifyPublisher(unittest.TestCase):
    def test_rejects_non_shopify_domain(self):
        for bad in ("evil.com", "shop.myshopify.com.evil.com", "http://x.myshopify.com", ""):
            with self.assertRaises(ValueError, msg=bad):
                ShopifyStorePublisher(shop_domain=bad, access_token="t")

    def test_publish_calls_admin_api_with_token_header(self):
        t = FakeTransport([(201, {"product": {"id": 123, "status": "active"}})])
        pub = ShopifyStorePublisher(shop_domain="negozio.myshopify.com", access_token="shpat-test", transport=t)
        res = pub.publish({"product": {"title": "x"}})
        self.assertEqual(res.product_id, "123")
        self.assertEqual(res.source, "SHOPIFY")
        call = t.calls[0]
        self.assertTrue(call["url"].startswith("https://negozio.myshopify.com/admin/api/"))
        self.assertEqual(call["headers"]["X-Shopify-Access-Token"], "shpat-test")

    def test_repr_hides_token(self):
        pub = ShopifyStorePublisher(shop_domain="negozio.myshopify.com", access_token="tok-segreto")
        self.assertNotIn("tok-segreto", repr(pub))


class TestPublishService(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.approvals = ApprovalStore(self.dir / "approvals.json")
        self.ks = KillSwitch(self.dir, environ={})
        self.store = MockStorePublisher()

    def tearDown(self):
        self.tmp.cleanup()

    def _publish(self, c):
        return publish_product(c, quote_for(c), MockCopywriter(), self.store, self.approvals, self.ks)

    def test_new_product_requires_human_approval(self):
        out = self._publish(make_candidate())
        self.assertEqual(out.status, "PENDING_APPROVAL")
        self.assertIsNotNone(out.request_id)
        self.assertEqual(self.store.published, [])

    def test_publishes_after_approval_as_active(self):
        c = make_candidate()
        out = self._publish(c)
        self.approvals.approve(out.request_id, approver="Mario")
        out2 = self._publish(c)
        self.assertEqual(out2.status, "PUBLISHED")
        self.assertEqual(len(self.store.published), 1)
        self.assertEqual(self.store.published[0]["product"]["status"], "active")
        self.assertEqual(out2.source, "MOCK")

    def test_prohibited_product_blocked_even_if_approved(self):
        c = make_candidate(category="health", title="Integratore vitamine")
        self.approvals.approve(
            self.approvals.request(PUBLISH_PRODUCT, c.sku, "forzatura").request_id, approver="Mario"
        )
        out = self._publish(c)
        self.assertEqual(out.status, "BLOCKED")
        self.assertEqual(self.store.published, [])

    def test_misleading_copy_blocked(self):
        class BadCopy(MockCopywriter):
            def generate(self, candidate, quote):
                return ProductCopy(title="X", description="Cura l'insonnia", bullets=(), source="MOCK")

        c = make_candidate()
        out = publish_product(c, quote_for(c), BadCopy(), self.store, self.approvals, self.ks)
        self.assertEqual(out.status, "BLOCKED")

    def test_kill_switch_blocks_publish(self):
        self.ks.activate("stop")
        with self.assertRaises(KillSwitchActive):
            self._publish(make_candidate())


if __name__ == "__main__":
    unittest.main()
