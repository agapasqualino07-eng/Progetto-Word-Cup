import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from dropship.campaigns.planner import evaluate_stop_loss, plan_budget
from dropship.campaigns.platforms import GoogleAds, MetaAds, MockAds, TikTokAds
from dropship.campaigns.service import CampaignManager
from dropship.catalog.pricing import suggest_price
from dropship.config import CampaignConfig, PricingConfig
from dropship.guardrails import (
    ApprovalStore,
    KillSwitch,
    KillSwitchActive,
    SpendCapExceeded,
    SpendGuard,
)
from dropship.models import Campaign
from tests.helpers import FakeTransport, make_candidate

CC = CampaignConfig()


class TestPlanner(unittest.TestCase):
    def test_budget_is_capped(self):
        self.assertEqual(plan_budget(Decimal("100"), CC), CC.max_campaign_budget)
        self.assertEqual(plan_budget(Decimal("7.5"), CC), Decimal("7.50"))

    def test_budget_must_be_positive(self):
        with self.assertRaises(ValueError):
            plan_budget(Decimal("0"), CC)

    def test_stop_loss_triggers_below_break_even(self):
        d = evaluate_stop_loss(Decimal("30"), Decimal("30"), Decimal("1.8"), Decimal("15"))
        self.assertEqual(d.action, "STOP")
        self.assertEqual(d.roas, Decimal("1.00"))

    def test_continue_above_break_even(self):
        d = evaluate_stop_loss(Decimal("30"), Decimal("90"), Decimal("1.8"), Decimal("15"))
        self.assertEqual(d.action, "CONTINUE")

    def test_insufficient_spend_means_no_decision(self):
        d = evaluate_stop_loss(Decimal("5"), Decimal("0"), Decimal("1.8"), Decimal("15"))
        self.assertEqual(d.action, "DATI INSUFFICIENTI")

    def test_no_break_even_means_stop(self):
        d = evaluate_stop_loss(Decimal("30"), Decimal("300"), None, Decimal("15"))
        self.assertEqual(d.action, "STOP")


class TestCampaignManager(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.approvals = ApprovalStore(self.dir / "approvals.json")
        self.ks = KillSwitch(self.dir, environ={})
        self.ads = {"meta": MockAds("meta"), "tiktok": MockAds("tiktok")}
        self.mgr = CampaignManager(
            self.dir / "campaigns.json",
            self.ads,
            SpendGuard(CC.daily_spend_cap, CC.max_campaign_budget),
            self.approvals,
            self.ks,
            CC,
        )
        c = make_candidate()
        self.quote = suggest_price(c.supplier_cost, c.shipping_cost, PricingConfig(), c.market_price)

    def tearDown(self):
        self.tmp.cleanup()

    def _draft(self, budget="10", platform="meta", sku="SKU-1"):
        return self.mgr.create_draft(sku, "Lampada", self.quote, platform, Decimal(budget))

    def test_draft_is_paused_and_marked_mock(self):
        cmp = self._draft()
        self.assertEqual(cmp.status, "PAUSED")
        self.assertEqual(cmp.source, "MOCK")
        self.assertEqual(cmp.break_even_roas, self.quote.break_even_roas)
        self.assertEqual(self.ads["meta"].campaigns[cmp.external_id]["status"], "PAUSED")

    def test_draft_budget_is_capped(self):
        cmp = self._draft("100")
        self.assertEqual(cmp.daily_budget, CC.max_campaign_budget)

    def test_daily_spend_cap_across_campaigns(self):
        self._draft("20", sku="A")
        self._draft("20", sku="B")
        with self.assertRaises(SpendCapExceeded):
            self._draft("20", sku="C")

    def test_unknown_platform_rejected(self):
        with self.assertRaises(ValueError):
            self._draft(platform="myspace")

    def test_activation_requires_approval(self):
        cmp = self._draft()
        out = self.mgr.activate(cmp.campaign_id)
        self.assertEqual(out.status, "PENDING_APPROVAL")
        self.assertEqual(self.mgr.get(cmp.campaign_id).status, "PAUSED")
        self.approvals.approve(out.request_id, approver="Mario")
        out2 = self.mgr.activate(cmp.campaign_id)
        self.assertEqual(out2.status, "ACTIVE")
        self.assertEqual(self.mgr.get(cmp.campaign_id).status, "ACTIVE")

    def test_raising_budget_requires_approval(self):
        cmp = self._draft("10")
        out = self.mgr.change_budget(cmp.campaign_id, Decimal("15"))
        self.assertEqual(out.status, "PENDING_APPROVAL")
        self.assertEqual(self.mgr.get(cmp.campaign_id).daily_budget, Decimal("10.00"))
        self.approvals.approve(out.request_id, approver="Mario")
        out2 = self.mgr.change_budget(cmp.campaign_id, Decimal("15"))
        self.assertEqual(out2.status, "UPDATED")
        self.assertEqual(self.mgr.get(cmp.campaign_id).daily_budget, Decimal("15.00"))

    def test_approved_raise_still_respects_cap(self):
        cmp = self._draft("10")
        out = self.mgr.change_budget(cmp.campaign_id, Decimal("25"))
        self.assertEqual(out.status, "BLOCKED")

    def test_lowering_budget_needs_no_approval(self):
        cmp = self._draft("10")
        out = self.mgr.change_budget(cmp.campaign_id, Decimal("5"))
        self.assertEqual(out.status, "UPDATED")

    def test_stop_loss_pauses_campaign(self):
        cmp = self._draft("10")
        self.ads["meta"].set_metrics(cmp.external_id, Decimal("20"), Decimal("10"))
        decision = self.mgr.apply_stop_loss(cmp.campaign_id)
        self.assertEqual(decision.action, "STOP")
        self.assertEqual(self.mgr.get(cmp.campaign_id).status, "STOPPED")
        self.assertEqual(self.ads["meta"].campaigns[cmp.external_id]["status"], "PAUSED")

    def test_stopped_campaign_frees_daily_cap(self):
        a = self._draft("20", sku="A")
        self._draft("20", sku="B")
        self.ads["meta"].set_metrics(a.external_id, Decimal("20"), Decimal("0"))
        self.mgr.apply_stop_loss(a.campaign_id)
        self._draft("20", sku="C")  # non solleva

    def test_kill_switch_blocks_campaign_actions(self):
        cmp = self._draft("10")
        self.ks.activate("stop")
        with self.assertRaises(KillSwitchActive):
            self._draft("5", sku="X")
        with self.assertRaises(KillSwitchActive):
            self.mgr.activate(cmp.campaign_id)

    def test_kill_switch_pause_all(self):
        cmp = self._draft("10")
        self.ks.activate("stop")
        paused = self.mgr.pause_all()
        self.assertEqual(paused, [cmp.campaign_id])
        self.assertEqual(self.ads["meta"].campaigns[cmp.external_id]["status"], "PAUSED")

    def test_reactivation_after_kill_switch_needs_new_approval(self):
        cmp = self._draft("10")
        out = self.mgr.activate(cmp.campaign_id)
        self.approvals.approve(out.request_id, approver="Mario")
        self.assertEqual(self.mgr.activate(cmp.campaign_id).status, "ACTIVE")
        self.ks.activate("stop")
        self.mgr.pause_all()
        self.ks.deactivate()
        self.assertEqual(self.mgr.activate(cmp.campaign_id).status, "PENDING_APPROVAL")

    def test_budget_raise_approval_is_single_use(self):
        cmp = self._draft("10")
        out = self.mgr.change_budget(cmp.campaign_id, Decimal("15"))
        self.approvals.approve(out.request_id, approver="Mario")
        self.mgr.change_budget(cmp.campaign_id, Decimal("15"))
        self.mgr.change_budget(cmp.campaign_id, Decimal("5"))
        self.assertEqual(self.mgr.change_budget(cmp.campaign_id, Decimal("15")).status, "PENDING_APPROVAL")

    def test_pause_all_works_with_fresh_mock_adapter(self):
        # nuova esecuzione CLI = nuovo MockAds senza memoria delle campagne
        cmp = self._draft("10")
        self.mgr.ads["meta"] = MockAds("meta")
        self.assertEqual(self.mgr.pause_all(), [cmp.campaign_id])

    def test_pause_all_continues_when_one_platform_fails(self):
        class Broken(MockAds):
            def set_status(self, external_id, active):
                raise RuntimeError("API giù")

        a = self._draft("10", platform="tiktok", sku="A")
        b = self._draft("10", platform="meta", sku="B")
        self.mgr.ads["tiktok"] = Broken("tiktok")
        paused = self.mgr.pause_all()
        self.assertEqual(paused, [b.campaign_id])
        self.assertEqual(self.mgr.last_pause_failures, [a.campaign_id])

    def test_persistence(self):
        cmp = self._draft("10")
        mgr2 = CampaignManager(
            self.dir / "campaigns.json", self.ads, SpendGuard(CC.daily_spend_cap, CC.max_campaign_budget),
            self.approvals, self.ks, CC,
        )
        self.assertEqual(mgr2.get(cmp.campaign_id).daily_budget, Decimal("10.00"))


def _campaign():
    return Campaign(
        campaign_id="CMP-1", sku="SKU-1", platform="meta", daily_budget=Decimal("10.00"),
        break_even_roas=Decimal("1.8"), source="META",
    )


class TestRealAdsAdapters(unittest.TestCase):
    def test_meta_creates_paused_campaign_in_cents(self):
        t = FakeTransport([(200, {"id": "999"})])
        meta = MetaAds(access_token="tok", ad_account_id="123", transport=t)
        ext = meta.create_paused_campaign(_campaign(), "Lampada")
        self.assertEqual(ext, "999")
        body = t.json_body()
        self.assertEqual(body["status"], "PAUSED")
        self.assertEqual(body["daily_budget"], 1000)
        self.assertIn("/act_123/campaigns", t.calls[0]["url"])
        self.assertNotIn("tok", t.calls[0]["url"])  # token nell'header, non in URL

    def test_meta_rejects_non_numeric_account(self):
        with self.assertRaises(ValueError):
            MetaAds(access_token="tok", ad_account_id="../x")

    def test_tiktok_creates_disabled_campaign(self):
        t = FakeTransport([(200, {"code": 0, "data": {"campaign_id": "777"}})])
        tt = TikTokAds(access_token="tok", advertiser_id="42", transport=t)
        ext = tt.create_paused_campaign(_campaign(), "Lampada")
        self.assertEqual(ext, "777")
        self.assertEqual(t.json_body()["operation_status"], "DISABLE")
        self.assertEqual(t.calls[0]["headers"]["Access-Token"], "tok")

    def test_tiktok_api_error_code_raises(self):
        t = FakeTransport([(200, {"code": 40001, "message": "bad"})])
        tt = TikTokAds(access_token="tok", advertiser_id="42", transport=t)
        with self.assertRaises(RuntimeError):
            tt.create_paused_campaign(_campaign(), "Lampada")

    def test_google_creates_budget_then_paused_campaign(self):
        t = FakeTransport(
            [
                (200, {"access_token": "at"}),
                (200, {"results": [{"resourceName": "customers/1/campaignBudgets/5"}]}),
                (200, {"results": [{"resourceName": "customers/1/campaigns/9"}]}),
            ]
        )
        g = GoogleAds(
            developer_token="dt", client_id="ci", client_secret="cs", refresh_token="rt",
            customer_id="123-456-7890", transport=t,
        )
        ext = g.create_paused_campaign(_campaign(), "Lampada")
        self.assertEqual(ext, "customers/1/campaigns/9")
        self.assertEqual(t.json_body(1)["operations"][0]["create"]["amountMicros"], "10000000")
        self.assertEqual(t.json_body(2)["operations"][0]["create"]["status"], "PAUSED")
        self.assertIn("/customers/1234567890/", t.calls[1]["url"])

    def test_reprs_hide_tokens(self):
        objs = [
            MetaAds(access_token="SEGRETO1", ad_account_id="1"),
            TikTokAds(access_token="SEGRETO1", advertiser_id="1"),
            GoogleAds(developer_token="SEGRETO1", client_id="c", client_secret="SEGRETO1",
                      refresh_token="SEGRETO1", customer_id="1"),
        ]
        for o in objs:
            self.assertNotIn("SEGRETO1", repr(o))


if __name__ == "__main__":
    unittest.main()
