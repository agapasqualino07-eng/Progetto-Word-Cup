"""Regole di conformità prodotto e testi.

Approccio prudente (fail-closed): nel dubbio il prodotto viene BLOCCATO e serve
una revisione umana fuori dall'automazione. Le liste sono un punto di partenza,
NON una consulenza legale: vanno riviste per il proprio mercato.
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Tuple

# Categorie vietate in toto (nessuna certificazione le sblocca nell'MVP).
PROHIBITED_CATEGORIES = {
    "weapons": "armi e accessori offensivi",
    "supplements": "integratori alimentari (regolati, notifica ministeriale)",
    "pharma": "farmaci/medicinali",
    "medical_device": "dispositivi medici (MDR 2017/745)",
    "tobacco": "tabacco/sigarette elettroniche",
    "adult": "prodotti per adulti",
    "drugs": "sostanze stupefacenti o paraphernalia",
}

# Parole chiave vietate (match su parole intere, titolo+descrizione).
PROHIBITED_KEYWORDS = {
    "arma": "armi", "armi": "armi", "pistola": "armi", "fucile": "armi", "coltello": "armi",
    "coltelli": "armi", "pugnale": "armi", "taser": "armi", "storditore": "armi",
    "tirapugni": "armi", "balestra": "armi", "knife": "armi", "gun": "armi", "weapon": "armi",
    "peperoncino": "armi (spray al peperoncino)",
    "integratore": "integratori", "integratori": "integratori", "supplement": "integratori",
    "dimagrante": "integratori", "dimagranti": "integratori",
    "brucia grassi": "integratori",
    "farmaco": "farmaci", "medicinale": "farmaci", "antibiotico": "farmaci",
    "sigaretta elettronica": "tabacco/svapo", "vape": "tabacco/svapo", "svapo": "tabacco/svapo",
    "tabacco": "tabacco/svapo", "nicotina": "tabacco/svapo",
    "replica": "contraffazione", "fake": "contraffazione", "falso": "contraffazione",
    "imitazione": "contraffazione",
}

# Categorie regolate: consentite solo con le certificazioni elencate.
REGULATED_CATEGORIES = {
    "cosmetics": (
        ("CPNP", "EU_RESPONSIBLE_PERSON"),
        "cosmetico: servono notifica CPNP e Persona Responsabile UE (Reg. 1223/2009)",
    ),
    "electronics": (("CE",), "elettronica: serve marcatura CE (LVD/EMC/RED) con DoC"),
    "toys": (("CE",), "giocattolo: serve marcatura CE (Dir. 2009/48/CE, EN71)"),
    "baby": (("CE",), "prodotto per l'infanzia: serve conformità CE/GPSR"),
}

# Marchi noti: nel titolo senza autorizzazione = rischio contraffazione.
PROTECTED_BRANDS = (
    "apple", "iphone", "airpods", "samsung", "nike", "adidas", "gucci", "louis vuitton",
    "chanel", "rolex", "prada", "dior", "hermes", "disney", "marvel", "pokemon", "lego",
    "dyson", "ray-ban", "rayban", "moncler", "supreme", "playstation", "nintendo",
)

# Affermazioni ingannevoli/sanitarie vietate nei testi (Codice del Consumo, claims salute).
FORBIDDEN_CLAIMS = (
    "cura", "cure", "guarisce", "guarire", "terapeutico", "terapeutica", "miracoloso",
    "miracolosa", "garantito al 100", "garantiti al 100", "100% garantito",
    "sicuro al 100", "senza effetti collaterali", "approvato dal ministero",
    "dimagrisci", "perdi peso", "clinicamente testato",
)


@dataclass(frozen=True)
class ComplianceResult:
    allowed: bool
    reasons: Tuple[str, ...]


def _normalize(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return " " + re.sub(r"[^a-z0-9]+", " ", text.lower()).strip() + " "


def _contains_phrase(norm_text, phrase):
    return f" {_normalize(phrase).strip()} " in norm_text


def check_product(candidate):
    reasons = []
    category = (candidate.category or "").strip().lower()
    text = _normalize(f"{candidate.title} {candidate.description}")

    if category in PROHIBITED_CATEGORIES:
        reasons.append(f"categoria vietata: {PROHIBITED_CATEGORIES[category]}")

    for kw, label in PROHIBITED_KEYWORDS.items():
        if _contains_phrase(text, kw):
            reasons.append(f"parola vietata '{kw}': {label}")

    if category in REGULATED_CATEGORIES:
        required, msg = REGULATED_CATEGORIES[category]
        have = {c.strip().upper() for c in candidate.certifications}
        missing = [r for r in required if r not in have]
        if missing:
            reasons.append(f"{msg} (mancano: {', '.join(missing)})")

    if candidate.brand and not candidate.brand_authorized:
        reasons.append(f"marchio '{candidate.brand}' senza autorizzazione del titolare")
    if not candidate.brand_authorized:
        for brand in PROTECTED_BRANDS:
            if _contains_phrase(text, brand):
                reasons.append(f"marchio protetto '{brand}' nel testo senza autorizzazione")

    return ComplianceResult(allowed=not reasons, reasons=tuple(dict.fromkeys(reasons)))


def check_copy(text):
    norm = _normalize(text)
    reasons = [f"affermazione vietata/ingannevole: '{c}'" for c in FORBIDDEN_CLAIMS if _contains_phrase(norm, c)]
    return ComplianceResult(allowed=not reasons, reasons=tuple(reasons))
