"""
Normalizzazione nomi squadre — da fonti esterne (EN) ai nomi canonici (IT).

Il sistema usa i nomi ITALIANI come chiave ovunque (constants.GROUPS, rating,
correlazioni). Le fonti esterne (The Odds API, dataset risultati) usano però
nomi INGLESI con varianti ("South Korea"/"Korea Republic", "Czechia"/"Czech
Republic", "Bosnia & Herzegovina"/"Bosnia and Herzegovina"...).

Senza normalizzazione i lookup falliscono in silenzio: niente rating FIFA,
niente girone (→ niente regole di correlazione!), tier di default per tutti.
Questo modulo è l'unico punto di conversione: ogni nuovo alias va aggiunto QUI.

`normalize_team()` non inventa mai: se un nome non è riconosciuto lo restituisce
invariato (e `is_known_team()` permette di accorgersene a monte).
"""
from __future__ import annotations

from ..constants import GROUPS

# Nomi canonici (italiani) = quelli dei gironi.
CANONICAL: frozenset[str] = frozenset(t for g in GROUPS.values() for t in g)

# Alias esterni → nome canonico. Include le varianti note di The Odds API,
# dell'endpoint /scores e dei dataset risultati (martj42).
ALIASES: dict[str, str] = {
    # Europa
    "Spain": "Spagna", "France": "Francia", "England": "Inghilterra",
    "Portugal": "Portogallo", "Netherlands": "Olanda", "Belgium": "Belgio",
    "Germany": "Germania", "Croatia": "Croazia", "Switzerland": "Svizzera",
    "Austria": "Austria", "Norway": "Norvegia", "Sweden": "Svezia",
    "Scotland": "Scozia", "Turkey": "Turchia", "Türkiye": "Turchia",
    "Turkiye": "Turchia", "Czechia": "Cechia", "Czech Republic": "Cechia",
    "Bosnia and Herzegovina": "Bosnia-Erzegovina",
    "Bosnia & Herzegovina": "Bosnia-Erzegovina",
    "Bosnia-Herzegovina": "Bosnia-Erzegovina",
    # Americhe
    "Brazil": "Brasile", "Argentina": "Argentina", "Mexico": "Messico",
    "United States": "USA", "USA": "USA", "United States of America": "USA",
    "Canada": "Canada", "Colombia": "Colombia", "Uruguay": "Uruguay",
    "Ecuador": "Ecuador", "Paraguay": "Paraguay", "Panama": "Panama",
    "Haiti": "Haiti", "Curacao": "Curaçao", "Curaçao": "Curaçao",
    # Africa
    "Morocco": "Marocco", "Senegal": "Senegal", "Egypt": "Egitto",
    "Algeria": "Algeria", "Tunisia": "Tunisia", "Ghana": "Ghana",
    "South Africa": "Sudafrica", "Cape Verde": "Capo Verde",
    "Cabo Verde": "Capo Verde", "Cape Verde Islands": "Capo Verde",
    "Ivory Coast": "Costa d'Avorio", "Cote d'Ivoire": "Costa d'Avorio",
    "Côte d'Ivoire": "Costa d'Avorio", "DR Congo": "Congo DR",
    "Congo DR": "Congo DR", "Democratic Republic of the Congo": "Congo DR",
    # Asia / Oceania
    "Japan": "Giappone", "South Korea": "Corea del Sud",
    "Korea Republic": "Corea del Sud", "Iran": "Iran", "IR Iran": "Iran",
    "Saudi Arabia": "Arabia Saudita", "Qatar": "Qatar", "Iraq": "Iraq",
    "Jordan": "Giordania", "Uzbekistan": "Uzbekistan",
    "Australia": "Australia", "New Zealand": "Nuova Zelanda",
}


def normalize_team(name: str) -> str:
    """Nome canonico (IT) da un nome esterno. Sconosciuto → invariato (mai inventare)."""
    name = (name or "").strip()
    if name in CANONICAL:
        return name
    return ALIASES.get(name, name)


def is_known_team(name: str) -> bool:
    """True se il nome (anche alias) corrisponde a una delle 48 nazionali."""
    return normalize_team(name) in CANONICAL
