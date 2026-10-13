"""Ogni regola di guardrail ha almeno un test qui."""

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from dropship.guardrails import (
    ApprovalStore,
    KillSwitch,
    KillSwitchActive,
    SpendCapExceeded,
    SpendGuard,
    check_copy,
    check_product,
)
from dropship.guardrails.approvals import PUBLISH_PRODUCT, RAISE_BUDGET
from tests.helpers import make_candidate


class TestComplianceProhibited(unittest.TestCase):
    def test_clean_product_allowed(self):
        r = check_product(make_candidate())
        self.assertTrue(r.allowed, r.reasons)

    def test_weapons_blocked_by_category(self):
        self.assertFalse(check_product(make_candidate(category="weapons", certifications=())).allowed)

    def test_weapons_blocked_by_keyword(self):
        c = make_candidate(category="outdoor", title="Coltello tattico a scatto", certifications=())
        self.assertFalse(check_product(c).allowed)

    def test_supplements_blocked(self):
        c = make_candidate(category="health", title="Integratore di collagene")
        r = check_product(c)
        self.assertFalse(r.allowed)
        self.assertTrue(any("integrator" in x.lower() for x in r.reasons))

    def test_supplements_blocked_even_in_innocent_category(self):
        c = make_candidate(category="home", title="Capsule dimagranti naturali")
        self.assertFalse(check_product(c).allowed)

    def test_vape_and_tobacco_blocked(self):
        c = make_candidate(category="home", title="Sigaretta elettronica usa e getta")
        self.assertFalse(check_product(c).allowed)

    def test_drugs_and_medicines_blocked(self):
        c = make_candidate(category="pharma", title="Farmaco anti dolore")
        self.assertFalse(check_product(c).allowed)

    def test_medical_devices_blocked(self):
        c = make_candidate(category="medical_device", title="Misuratore pressione")
        self.assertFalse(check_product(c).allowed)

    def test_keyword_match_is_word_based_not_substring(self):
        # "armadio" contiene "arma" ma non è un'arma
        c = make_candidate(category="home", title="Armadio salvaspazio")
        self.assertTrue(check_product(c).allowed, check_product(c).reasons)


class TestComplianceRegulated(unittest.TestCase):
    def test_cosmetics_without_compliance_blocked(self):
        c = make_candidate(category="cosmetics", title="Siero viso", certifications=())
        r = check_product(c)
        self.assertFalse(r.allowed)
        self.assertTrue(any("CPNP" in x for x in r.reasons))

    def test_cosmetics_with_cpnp_and_responsible_person_allowed(self):
        c = make_candidate(
            category="cosmetics", title="Siero viso", certifications=("CPNP", "EU_RESPONSIBLE_PERSON")
        )
        self.assertTrue(check_product(c).allowed)

    def test_electronics_without_ce_blocked(self):
        c = make_candidate(category="electronics", title="Caricatore USB", certifications=())
        r = check_product(c)
        self.assertFalse(r.allowed)
        self.assertTrue(any("CE" in x for x in r.reasons))

    def test_electronics_with_ce_allowed(self):
        c = make_candidate(category="electronics", title="Caricatore USB", certifications=("CE",))
        self.assertTrue(check_product(c).allowed)

    def test_toys_without_ce_blocked(self):
        c = make_candidate(category="toys", title="Peluche", certifications=())
        self.assertFalse(check_product(c).allowed)

    def test_certifications_case_insensitive(self):
        c = make_candidate(category="electronics", title="Caricatore", certifications=("ce",))
        self.assertTrue(check_product(c).allowed)


class TestComplianceCounterfeit(unittest.TestCase):
    def test_replica_keyword_blocked(self):
        c = make_candidate(title="Orologio replica di lusso", category="fashion")
        self.assertFalse(check_product(c).allowed)

    def test_known_brand_in_title_without_authorization_blocked(self):
        c = make_candidate(title="Cover stile Apple iPhone", category="accessories")
        r = check_product(c)
        self.assertFalse(r.allowed)
        self.assertTrue(any("marchio" in x.lower() for x in r.reasons))

    def test_declared_brand_without_authorization_blocked(self):
        c = make_candidate(brand="Nike", brand_authorized=False, category="fashion")
        self.assertFalse(check_product(c).allowed)

    def test_authorized_brand_allowed(self):
        c = make_candidate(
            title="Scarpe Nike Air", brand="Nike", brand_authorized=True, category="fashion"
        )
        self.assertTrue(check_product(c).allowed)


class TestCopyCompliance(unittest.TestCase):
    def test_clean_copy_allowed(self):
        self.assertTrue(check_copy("Lampada comoda, luce regolabile.").allowed)

    def test_health_claims_blocked(self):
        self.assertFalse(check_copy("Guarisce il mal di schiena in 3 giorni").allowed)

    def test_absolute_guarantees_blocked(self):
        self.assertFalse(check_copy("Risultati garantiti al 100%").allowed)


class TestKillSwitch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_inactive_by_default(self):
        ks = KillSwitch(self.dir, environ={})
        self.assertFalse(ks.is_active())
        ks.assert_inactive("test")  # non solleva

    def test_file_activation_blocks_actions(self):
        ks = KillSwitch(self.dir, environ={})
        ks.activate("ROAS crollato")
        self.assertTrue(ks.is_active())
        with self.assertRaises(KillSwitchActive):
            ks.assert_inactive("publish")

    def test_deactivate(self):
        ks = KillSwitch(self.dir, environ={})
        ks.activate("x")
        ks.deactivate()
        self.assertFalse(ks.is_active())

    def test_env_activation_cannot_be_overridden_by_file(self):
        ks = KillSwitch(self.dir, environ={"DROPSHIP_KILL_SWITCH": "1"})
        ks.deactivate()
        self.assertTrue(ks.is_active())


class TestSpendGuard(unittest.TestCase):
    def setUp(self):
        self.g = SpendGuard(daily_cap=Decimal("50"), max_campaign_budget=Decimal("20"))

    def test_within_cap_ok(self):
        self.g.check(committed_today=Decimal("20"), requested=Decimal("20"))

    def test_daily_cap_exceeded(self):
        with self.assertRaises(SpendCapExceeded):
            self.g.check(committed_today=Decimal("40"), requested=Decimal("15"))

    def test_single_campaign_cap_exceeded(self):
        with self.assertRaises(SpendCapExceeded):
            self.g.check(committed_today=Decimal("0"), requested=Decimal("25"))

    def test_non_positive_budget_rejected(self):
        with self.assertRaises(SpendCapExceeded):
            self.g.check(committed_today=Decimal("0"), requested=Decimal("0"))


class TestApprovals(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "approvals.json"
        self.store = ApprovalStore(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_not_approved_by_default(self):
        self.assertFalse(self.store.is_approved(PUBLISH_PRODUCT, "SKU-1"))

    def test_request_is_pending_until_human_approves(self):
        req = self.store.request(PUBLISH_PRODUCT, "SKU-1", "Pubblica lampada")
        self.assertEqual(req.status, "PENDING")
        self.assertFalse(self.store.is_approved(PUBLISH_PRODUCT, "SKU-1"))
        self.store.approve(req.request_id, approver="Mario")
        self.assertTrue(self.store.is_approved(PUBLISH_PRODUCT, "SKU-1"))

    def test_request_is_idempotent(self):
        a = self.store.request(PUBLISH_PRODUCT, "SKU-1", "x")
        b = self.store.request(PUBLISH_PRODUCT, "SKU-1", "x")
        self.assertEqual(a.request_id, b.request_id)
        self.assertEqual(len(self.store.pending()), 1)

    def test_approval_requires_named_approver(self):
        req = self.store.request(PUBLISH_PRODUCT, "SKU-1", "x")
        with self.assertRaises(ValueError):
            self.store.approve(req.request_id, approver="")

    def test_approval_is_bound_to_exact_subject(self):
        req = self.store.request(RAISE_BUDGET, "CMP-1:15.00", "alza a 15")
        self.store.approve(req.request_id, approver="Mario")
        self.assertTrue(self.store.is_approved(RAISE_BUDGET, "CMP-1:15.00"))
        self.assertFalse(self.store.is_approved(RAISE_BUDGET, "CMP-1:20.00"))

    def test_consumed_approval_cannot_be_reused(self):
        req = self.store.request(RAISE_BUDGET, "CMP-1:15.00", "x")
        self.store.approve(req.request_id, approver="Mario")
        self.assertTrue(self.store.consume(RAISE_BUDGET, "CMP-1:15.00"))
        self.assertFalse(self.store.is_approved(RAISE_BUDGET, "CMP-1:15.00"))
        self.assertFalse(self.store.consume(RAISE_BUDGET, "CMP-1:15.00"))
        # una nuova richiesta per lo stesso soggetto torna PENDING
        again = self.store.request(RAISE_BUDGET, "CMP-1:15.00", "x")
        self.assertEqual(again.status, "PENDING")

    def test_rejected_request_is_not_approved(self):
        req = self.store.request(PUBLISH_PRODUCT, "SKU-1", "x")
        self.store.reject(req.request_id, approver="Mario")
        self.assertFalse(self.store.is_approved(PUBLISH_PRODUCT, "SKU-1"))

    def test_unknown_request_id(self):
        with self.assertRaises(KeyError):
            self.store.approve("nonexistent", approver="Mario")

    def test_persisted_on_disk(self):
        req = self.store.request(PUBLISH_PRODUCT, "SKU-1", "x")
        self.store.approve(req.request_id, approver="Mario")
        again = ApprovalStore(self.path)
        self.assertTrue(again.is_approved(PUBLISH_PRODUCT, "SKU-1"))
        data = json.loads(self.path.read_text())
        self.assertEqual(data[0]["approver"], "Mario")

    def test_corrupted_file_fails_closed(self):
        self.path.write_text("{not json")
        store = ApprovalStore(self.path)
        self.assertFalse(store.is_approved(PUBLISH_PRODUCT, "SKU-1"))


if __name__ == "__main__":
    unittest.main()
