"""CLI: python3 -m dropship.cli <comando>

Comandi principali: scan | publish | campaign | orders
Supporto:           approve | reject | pending | kill | status

Senza chiavi tutto gira in MOCK (dati marcati source=MOCK, nessuna rete).
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dropship import adapters
from dropship.campaigns.service import CampaignManager
from dropship.catalog.selection import select_products
from dropship.config import ConfigError, load_dotenv, load_settings
from dropship.guardrails import ApprovalStore, GuardrailViolation, KillSwitch, SpendGuard
from dropship.http import ExternalServiceError
from dropship.models import PriceQuote
from dropship.orders.service import OrderService
from dropship.storage import read_json, write_json
from dropship.store.service import publish_product
from dropship.store.static_site import write_static_site
from dropship.trends.service import scan

DEFAULT_KEYWORDS = ("casa", "animali", "beauty", "tech", "moda")


def _positive_decimal(text):
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError("numero non valido") from None
    if not value.is_finite() or value <= 0:
        raise argparse.ArgumentTypeError("deve essere > 0")
    return value


def _build_parser():
    p = argparse.ArgumentParser(prog="dropship", description="Dropship MVP (mock-first, con guardrail)")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("scan", help="rileva prodotti in tendenza")
    s.add_argument("--keywords", default=",".join(DEFAULT_KEYWORDS))

    s = sub.add_parser("publish", help="seleziona e pubblica (richiede approvazione umana)")
    s.add_argument("--keywords", default=",".join(DEFAULT_KEYWORDS))
    s.add_argument("--limit", type=int, default=3, choices=range(1, 21), metavar="N")

    s = sub.add_parser("approve", help="approva una richiesta (azione umana)")
    s.add_argument("request_id")
    s.add_argument("--by", required=True, help="nome di chi approva")

    s = sub.add_parser("reject", help="rifiuta una richiesta")
    s.add_argument("request_id")
    s.add_argument("--by", required=True)

    sub.add_parser("pending", help="elenca richieste in attesa")

    s = sub.add_parser("campaign", help="bozze campagne ads + stop-loss")
    s.add_argument("--budget", type=_positive_decimal, default=Decimal("10"), help="budget giornaliero per campagna")
    s.add_argument("--platform", choices=("meta", "tiktok", "google"), default="meta")
    s.add_argument("--raise-id", help="id campagna di cui cambiare il budget")
    s.add_argument("--to", type=_positive_decimal, help="nuovo budget giornaliero")

    sub.add_parser("orders", help="inoltra ordini pagati al fornitore + tracking")

    s = sub.add_parser("kill", help="kill switch")
    s.add_argument("state", choices=("on", "off"))
    s.add_argument("--reason", default="attivato manualmente")

    sub.add_parser("status", help="modalità connettori e stato guardrail")
    return p


class App:
    def __init__(self, environ):
        self.env = environ
        self.settings = load_settings(environ)
        self.data = Path(self.settings.data_dir)
        self.approvals = ApprovalStore(self.data / "approvals.json")
        self.kill = KillSwitch(self.data, environ)

    # stato pubblicati -------------------------------------------------------
    def published(self):
        data = read_json(self.data / "published.json", {})
        return data if isinstance(data, dict) else {}

    def save_published(self, data):
        write_json(self.data / "published.json", data)

    def campaign_manager(self):
        cfg = self.settings.campaigns
        return CampaignManager(
            self.data / "campaigns.json", adapters.build_ads(self.env),
            SpendGuard(cfg.daily_spend_cap, cfg.max_campaign_budget), self.approvals, self.kill, cfg,
        )

    def run_scan(self, keywords):
        kws = [k.strip() for k in keywords.split(",") if k.strip()][:20]
        return scan(adapters.build_supplier(self.env), adapters.build_trend_source(self.env), kws,
                    self.settings.thresholds, self.settings.pricing)


def cmd_scan(app, args):
    results = app.run_scan(args.keywords)
    from dropship.guardrails import check_product

    print(f"{'SKU':<16}{'SCORE':>6}  {'ESITO':<10} {'FONTE':<8} TITOLO")
    for r in results:
        comp = check_product(r.candidate)
        verdict = "BLOCCATO" if not comp.allowed else ("OK" if r.passed else "SCARTATO")
        print(f"{r.candidate.sku:<16}{r.score:>6.1f}  {verdict:<10} {r.signal.source:<8} {r.candidate.title}")
        for reason in (comp.reasons if not comp.allowed else r.reasons):
            print(f"{'':<18}- {reason}")
    return 0


def cmd_publish(app, args):
    report = select_products(app.run_scan(args.keywords), app.settings.pricing, limit=args.limit)
    store = adapters.build_store(app.env)
    copywriter = adapters.build_copywriter(app.env)
    published = app.published()
    for sku, reasons in report.rejected:
        if reasons and reasons[0].startswith("BLOCCATO"):
            print(f"[BLOCCATO] {sku}: {'; '.join(reasons[1:])}")
    for sel in report.selected:
        c, q = sel.candidate, sel.quote
        if c.sku in published:
            print(f"[GIÀ PUBBLICATO] {c.sku}")
            continue
        out = publish_product(c, q, copywriter, store, app.approvals, app.kill)
        head = f"{c.sku} '{c.title}' € {q.price_gross} (netto € {q.price_net}, IVA € {q.vat}, margine {q.margin:.0%})"
        if out.status == "PENDING_APPROVAL":
            print(f"[IN ATTESA DI APPROVAZIONE] {head} -> richiesta {out.request_id}")
            print(f"    approva con: python3 -m dropship.cli approve {out.request_id} --by \"Nome Cognome\"")
        elif out.status == "BLOCKED":
            print(f"[BLOCCATO] {c.sku}: {'; '.join(out.reasons)}")
        else:
            print(f"[PUBBLICATO] {head} id={out.product_id} source={out.source}")
            published[c.sku] = {
                "title": c.title, "product_id": out.product_id, "source": out.source, "listing": out.listing,
                "quote": {k: (str(v) if v is not None else None) for k, v in q.__dict__.items()},
                "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
    app.save_published(published)
    if published and store.source == "MOCK":
        files = write_static_site([v["listing"] for v in published.values()], app.data / "site")
        print(f"Sito statico di fallback: {len(files)} file in {app.data / 'site'}")
    return 0


def _quote_from(d):
    return PriceQuote(**{k: (Decimal(v) if v not in (None, "None") else None) for k, v in d.items()})


def cmd_campaign(app, args):
    mgr = app.campaign_manager()
    if args.raise_id:
        if args.to is None:
            print("Serve --to <budget>")
            return 1
        out = mgr.change_budget(args.raise_id, args.to)
        print(f"[{out.status}] {args.raise_id} -> € {args.to} {'; '.join(out.reasons)}"
              + (f" richiesta {out.request_id}" if out.request_id else ""))
        return 0
    published = app.published()
    if not published:
        print("Nessun prodotto pubblicato: esegui prima 'publish' e approva le richieste.")
        return 0
    existing = {(c.sku, c.platform) for c in mgr.list() if c.status != "STOPPED"}
    for sku, info in published.items():
        if (sku, args.platform) in existing:
            continue
        quote = _quote_from(info["quote"])
        try:
            mgr.create_draft(sku, info["title"], quote, args.platform, args.budget)
        except GuardrailViolation as exc:
            print(f"[BLOCCATO] {sku}: {exc}")
    for c in mgr.list():
        if c.status == "PAUSED":
            out = mgr.activate(c.campaign_id)
            if out.status == "PENDING_APPROVAL":
                print(f"    attivazione {c.campaign_id}: richiesta {out.request_id} (approve per attivare)")
            elif out.status == "BLOCKED":
                print(f"    attivazione {c.campaign_id} bloccata: {'; '.join(out.reasons)}")
            c = mgr.get(c.campaign_id)
        line = (f"[{c.status}] {c.campaign_id} {c.platform:<7} {c.sku:<14} € {c.daily_budget}/giorno "
                f"ROAS break-even {c.break_even_roas} source={c.source}")
        print(line)
        if c.status == "ACTIVE":
            d = mgr.apply_stop_loss(c.campaign_id)
            after = " -> campagna messa in pausa (STOPPED)" if d.action == "STOP" else ""
            print(f"    stop-loss: {d.action} ({d.reason}){after}")
    total = sum((c.daily_budget for c in mgr.list() if c.status in ("PAUSED", "ACTIVE")), Decimal("0"))
    print(f"Budget giornaliero impegnato: € {total} / cap € {app.settings.campaigns.daily_spend_cap}")
    return 0


def cmd_orders(app, args):
    published = app.published()
    store = adapters.build_store(app.env, mock_order_skus=list(published))
    svc = OrderService(adapters.build_supplier(app.env), app.kill, app.data / "orders.json", known_skus=published)
    orders = store.list_paid_unfulfilled_orders()
    if not orders:
        print("Nessun ordine da evadere.")
        return 0
    for o in orders:
        r = svc.forward(o)
        detail = "; ".join(r.reasons)
        sup = f" -> fornitore {r.supplier_order.supplier_order_id} ({r.supplier_order.source})" if r.supplier_order else ""
        print(f"[{r.status}] {o.order_id} sku={o.sku} qty={o.quantity}{sup} {detail}".rstrip())
        if r.status in ("FORWARDED", "DUPLICATE"):
            t = svc.tracking(o.order_id)
            print(f"    tracking: {t.tracking_number or 'NON ANCORA DISPONIBILE'} {t.carrier} {t.status} source={t.source}")
    return 0


def cmd_approve(app, args, reject=False):
    try:
        req = (app.approvals.reject if reject else app.approvals.approve)(args.request_id, approver=args.by)
    except KeyError:
        print(f"Richiesta {args.request_id} non trovata")
        return 1
    print(f"[{req.status}] {req.request_id} {req.action} {req.subject} da {req.approver}: {req.summary}")
    return 0


def cmd_pending(app, args):
    items = app.approvals.pending()
    if not items:
        print("Nessuna richiesta in attesa.")
    for r in items:
        print(f"{r.request_id} {r.action:<18} {r.subject:<24} {r.summary}")
    return 0


def cmd_kill(app, args):
    if args.state == "on":
        app.kill.activate(args.reason)
        mgr = app.campaign_manager()
        paused = mgr.pause_all()
        print(f"KILL SWITCH ATTIVO. Campagne messe in pausa: {len(paused)}")
        if mgr.last_pause_failures:
            print("ATTENZIONE: pausa NON riuscita per " + ", ".join(mgr.last_pause_failures)
                  + " -> mettile in pausa a mano dal pannello della piattaforma!")
    else:
        app.kill.deactivate()
        print("Kill switch file rimosso." + (" ATTENZIONE: resta attivo via DROPSHIP_KILL_SWITCH."
                                             if app.kill.is_active() else ""))
    return 0


def cmd_status(app, args):
    for line in adapters.describe_modes(app.env):
        print(line)
    print(f"kill switch: {'ATTIVO (' + app.kill.reason() + ')' if app.kill.is_active() else 'spento'}")
    print(f"richieste in attesa: {len(app.approvals.pending())}")
    print(f"cap spesa giornaliero: € {app.settings.campaigns.daily_spend_cap}")
    return 0


COMMANDS = {
    "scan": cmd_scan, "publish": cmd_publish, "campaign": cmd_campaign, "orders": cmd_orders,
    "approve": cmd_approve, "reject": lambda a, ns: cmd_approve(a, ns, reject=True),
    "pending": cmd_pending, "kill": cmd_kill, "status": cmd_status,
}


def main(argv=None, environ=None):
    if environ is None:
        environ = dict(os.environ)
        load_dotenv(Path(".env"), environ)
    try:
        args = _build_parser().parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        app = App(environ)
        if args.command in ("publish", "campaign", "orders") and app.kill.is_active():
            print(f"KILL SWITCH attivo ({app.kill.reason()}): nessuna azione eseguita.")
            return 3
        return COMMANDS[args.command](app, args)
    except GuardrailViolation as exc:
        print(f"[GUARDRAIL] {exc}")
        return 3
    except ConfigError as exc:
        print(f"[CONFIGURAZIONE] {exc}")
        return 1
    except (ExternalServiceError, RuntimeError) as exc:
        print(f"[SERVIZIO ESTERNO] {exc}")
        return 4
    except ValueError as exc:
        print(f"[ERRORE] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
