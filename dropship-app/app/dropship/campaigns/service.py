"""Gestione campagne con guardrail: cap di spesa, approvazioni, stop-loss, kill switch."""

import secrets
from dataclasses import asdict
from decimal import Decimal

from dropship.campaigns.planner import evaluate_stop_loss, plan_budget
from dropship.guardrails.approvals import ACTIVATE_CAMPAIGN, RAISE_BUDGET
from dropship.guardrails.errors import SpendCapExceeded
from dropship.models import ActionOutcome, Campaign
from dropship.storage import read_json, write_json

COMMITTED_STATUSES = ("PAUSED", "ACTIVE")  # i draft prenotano budget: il cap resta rispettato all'attivazione


def _from_dict(d):
    d = dict(d)
    d["daily_budget"] = Decimal(d["daily_budget"])
    d["break_even_roas"] = Decimal(d["break_even_roas"]) if d.get("break_even_roas") not in (None, "None") else None
    return Campaign(**d)


class CampaignManager:
    def __init__(self, state_path, ads_platforms, spend_guard, approvals, kill_switch, cfg):
        self.state_path = state_path
        self.ads = dict(ads_platforms)
        self.spend_guard = spend_guard
        self.approvals = approvals
        self.kill_switch = kill_switch
        self.cfg = cfg
        self.last_pause_failures = []

    # --- persistenza -------------------------------------------------------
    def _load(self):
        data = read_json(self.state_path, [])
        return [_from_dict(d) for d in data] if isinstance(data, list) else []

    def _save(self, items):
        write_json(self.state_path, [asdict(c) for c in items])

    def list(self):
        return self._load()

    def get(self, campaign_id):
        for c in self._load():
            if c.campaign_id == campaign_id:
                return c
        raise KeyError(campaign_id)

    def _update(self, campaign):
        items = [campaign if c.campaign_id == campaign.campaign_id else c for c in self._load()]
        self._save(items)

    def _committed(self, exclude_id=None):
        return sum(
            (c.daily_budget for c in self._load() if c.status in COMMITTED_STATUSES and c.campaign_id != exclude_id),
            Decimal("0"),
        )

    # --- azioni ------------------------------------------------------------
    def create_draft(self, sku, title, quote, platform, requested_budget):
        self.kill_switch.assert_inactive("creazione campagna")
        if platform not in self.ads:
            raise ValueError(f"piattaforma non configurata: {platform}")
        budget = plan_budget(requested_budget, self.cfg)
        self.spend_guard.check(self._committed(), budget)
        adapter = self.ads[platform]
        cmp = Campaign(
            campaign_id="CMP-" + secrets.token_hex(4), sku=sku, platform=platform, daily_budget=budget,
            break_even_roas=quote.break_even_roas, source=adapter.source, status="PAUSED",
        )
        cmp.external_id = adapter.create_paused_campaign(cmp, title)
        items = self._load()
        items.append(cmp)
        self._save(items)
        return cmp

    def activate(self, campaign_id):
        self.kill_switch.assert_inactive("attivazione campagna")
        cmp = self.get(campaign_id)
        if cmp.status == "ACTIVE":
            return ActionOutcome("ACTIVE")
        if cmp.status == "STOPPED":
            return ActionOutcome("BLOCKED", ("campagna fermata dallo stop-loss: serve una nuova bozza",))
        if cmp.break_even_roas is None:
            return ActionOutcome("BLOCKED", ("prodotto senza profitto unitario",))
        subject = f"{cmp.campaign_id}:{cmp.daily_budget}"
        if not self.approvals.is_approved(ACTIVATE_CAMPAIGN, subject):
            req = self.approvals.request(
                ACTIVATE_CAMPAIGN, subject,
                f"Attiva {cmp.platform} per {cmp.sku} a € {cmp.daily_budget}/giorno (ROAS BE {cmp.break_even_roas})",
            )
            return ActionOutcome("PENDING_APPROVAL", request_id=req.request_id)
        self.ads[cmp.platform].set_status(cmp.external_id, True)
        self.approvals.consume(ACTIVATE_CAMPAIGN, subject)
        cmp.status = "ACTIVE"
        self._update(cmp)
        return ActionOutcome("ACTIVE")

    def change_budget(self, campaign_id, new_budget):
        self.kill_switch.assert_inactive("modifica budget")
        cmp = self.get(campaign_id)
        new_budget = Decimal(new_budget).quantize(Decimal("0.01"))
        try:
            self.spend_guard.check(self._committed(exclude_id=cmp.campaign_id), new_budget)
        except SpendCapExceeded as exc:
            return ActionOutcome("BLOCKED", (str(exc),))
        raising = new_budget > cmp.daily_budget
        subject = f"{cmp.campaign_id}:{new_budget}"
        if raising:
            if not self.approvals.is_approved(RAISE_BUDGET, subject):
                req = self.approvals.request(
                    RAISE_BUDGET, subject, f"Alza budget {cmp.campaign_id} da € {cmp.daily_budget} a € {new_budget}"
                )
                return ActionOutcome("PENDING_APPROVAL", request_id=req.request_id)
        self.ads[cmp.platform].set_daily_budget(cmp.external_id, new_budget)
        if raising:
            self.approvals.consume(RAISE_BUDGET, subject)
        cmp.daily_budget = new_budget
        self._update(cmp)
        return ActionOutcome("UPDATED")

    def apply_stop_loss(self, campaign_id):
        """Lo stop-loss mette SEMPRE in pausa (azione protettiva: consentita anche col kill switch)."""
        cmp = self.get(campaign_id)
        m = self.ads[cmp.platform].get_metrics(cmp.external_id)
        decision = evaluate_stop_loss(m.spend, m.revenue, cmp.break_even_roas, self.cfg.min_spend_for_decision)
        if decision.action == "STOP" and cmp.status != "STOPPED":
            self.ads[cmp.platform].set_status(cmp.external_id, False)
            cmp.status = "STOPPED"
            self._update(cmp)
        return decision

    def pause_all(self):
        """Mette in pausa tutte le campagne attive o in bozza (usato col kill switch)."""
        paused, failures = [], []
        for cmp in self._load():
            if cmp.status not in COMMITTED_STATUSES:
                continue
            try:
                self.ads[cmp.platform].set_status(cmp.external_id, False)
            except Exception:  # noqa: BLE001 - una piattaforma giù non deve fermare le altre
                failures.append(cmp.campaign_id)
                continue
            if cmp.status == "ACTIVE":
                cmp.status = "PAUSED"
                self._update(cmp)
            paused.append(cmp.campaign_id)
        self.last_pause_failures = failures
        return paused
