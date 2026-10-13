"""Configurazione: soglie, pricing, cap di spesa. Override via variabili d'ambiente.

Tutti i valori sono validati: una configurazione assurda (es. margine 150%)
fa fallire l'avvio invece di produrre decisioni sbagliate in silenzio.
"""

import os
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class TrendThresholds:
    min_demand_growth: float = 0.20  # +20% di interesse nelle ultime 4 settimane
    max_ad_saturation: float = 0.60  # 0..1, quota di inserzionisti già attivi
    min_margin: float = 0.30  # margine netto stimato al prezzo di mercato
    max_weight_kg: float = 2.0
    min_score: float = 60.0  # 0..100


@dataclass(frozen=True)
class PricingConfig:
    vat_rate: Decimal = Decimal("0.22")  # IVA ordinaria Italia
    min_margin: Decimal = Decimal("0.30")  # margine minimo sul netto IVA
    payment_fee_pct: Decimal = Decimal("0.029")
    payment_fee_fixed: Decimal = Decimal("0.30")


@dataclass(frozen=True)
class CampaignConfig:
    daily_spend_cap: Decimal = Decimal("50")  # cap giornaliero TOTALE ads
    max_campaign_budget: Decimal = Decimal("20")  # cap per singola campagna
    min_spend_for_decision: Decimal = Decimal("15")  # sotto: dati insufficienti


@dataclass(frozen=True)
class Settings:
    thresholds: TrendThresholds = field(default_factory=TrendThresholds)
    pricing: PricingConfig = field(default_factory=PricingConfig)
    campaigns: CampaignConfig = field(default_factory=CampaignConfig)
    data_dir: Path = Path("data")
    force_mock: bool = False


TRUE_VALUES = {"1", "true", "yes", "on", "si", "sì"}


def _get(env, name, default, kind):
    raw = env.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return kind(str(raw).strip())
    except (ValueError, InvalidOperation):
        raise ConfigError(f"{name}: valore non numerico") from None


def _rate(name, value, upper_inclusive=False):
    ok = 0 <= value <= 1 if upper_inclusive else 0 <= value < 1
    if not ok:
        raise ConfigError(f"{name}: deve essere tra 0 e 1")
    return value


def _positive(name, value):
    if value <= 0:
        raise ConfigError(f"{name}: deve essere > 0")
    return value


def load_settings(env=None):
    env = os.environ if env is None else env
    th = TrendThresholds(
        min_demand_growth=_get(env, "DROPSHIP_MIN_DEMAND_GROWTH", 0.20, float),
        max_ad_saturation=_rate(
            "DROPSHIP_MAX_AD_SATURATION",
            _get(env, "DROPSHIP_MAX_AD_SATURATION", 0.60, float),
            upper_inclusive=True,
        ),
        min_margin=_rate("DROPSHIP_MIN_TREND_MARGIN", _get(env, "DROPSHIP_MIN_TREND_MARGIN", 0.30, float)),
        max_weight_kg=_positive("DROPSHIP_MAX_WEIGHT_KG", _get(env, "DROPSHIP_MAX_WEIGHT_KG", 2.0, float)),
        min_score=_get(env, "DROPSHIP_MIN_TREND_SCORE", 60.0, float),
    )
    if not 0 <= th.min_score <= 100:
        raise ConfigError("DROPSHIP_MIN_TREND_SCORE: deve essere tra 0 e 100")

    pr = PricingConfig(
        vat_rate=_rate("DROPSHIP_VAT_RATE", _get(env, "DROPSHIP_VAT_RATE", Decimal("0.22"), Decimal)),
        min_margin=_rate("DROPSHIP_MIN_MARGIN", _get(env, "DROPSHIP_MIN_MARGIN", Decimal("0.30"), Decimal)),
        payment_fee_pct=_rate(
            "DROPSHIP_PAYMENT_FEE_PCT", _get(env, "DROPSHIP_PAYMENT_FEE_PCT", Decimal("0.029"), Decimal)
        ),
        payment_fee_fixed=_get(env, "DROPSHIP_PAYMENT_FEE_FIXED", Decimal("0.30"), Decimal),
    )
    if pr.payment_fee_fixed < 0:
        raise ConfigError("DROPSHIP_PAYMENT_FEE_FIXED: deve essere >= 0")

    cc = CampaignConfig(
        daily_spend_cap=_positive(
            "DROPSHIP_DAILY_SPEND_CAP", _get(env, "DROPSHIP_DAILY_SPEND_CAP", Decimal("50"), Decimal)
        ),
        max_campaign_budget=_positive(
            "DROPSHIP_MAX_CAMPAIGN_BUDGET", _get(env, "DROPSHIP_MAX_CAMPAIGN_BUDGET", Decimal("20"), Decimal)
        ),
        min_spend_for_decision=_positive(
            "DROPSHIP_MIN_SPEND_FOR_DECISION",
            _get(env, "DROPSHIP_MIN_SPEND_FOR_DECISION", Decimal("15"), Decimal),
        ),
    )
    if cc.max_campaign_budget > cc.daily_spend_cap:
        raise ConfigError("DROPSHIP_MAX_CAMPAIGN_BUDGET non può superare DROPSHIP_DAILY_SPEND_CAP")

    return Settings(
        thresholds=th,
        pricing=pr,
        campaigns=cc,
        data_dir=Path(env.get("DROPSHIP_DATA_DIR") or "data"),
        force_mock=str(env.get("DROPSHIP_FORCE_MOCK", "")).strip().lower() in TRUE_VALUES,
    )


def parse_dotenv(text):
    """Parser .env minimale (KEY=VALUE, commenti #, 'export', virgolette)."""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not key.replace("_", "").isalnum():
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        out[key] = value
    return out


def load_dotenv(path, environ):
    """Carica un .env SENZA sovrascrivere variabili già presenti nell'ambiente."""
    path = Path(path)
    if not path.is_file():
        return
    for key, value in parse_dotenv(path.read_text(encoding="utf-8")).items():
        environ.setdefault(key, value)


def is_truthy(value):
    return str(value or "").strip().lower() in TRUE_VALUES
