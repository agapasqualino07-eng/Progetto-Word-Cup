"""
Costanti del torneo e dati storici verificati.

Single source of truth per gironi, host nation, debuttanti, tier squadre,
trend storici e matrice di correlazione. Tutti i numeri qui dentro devono
essere VERIFICABILI: se un dato non è verificato, non va aggiunto.

Convenzione: identificatori e nomi di variabile in inglese; i contenuti
(nomi nazionali) in italiano perché è la lingua del sistema.
"""

# ---------------------------------------------------------------------------
# GIRONI — FIFA World Cup 2026 (48 nazionali, 12 gironi da 4)
# ---------------------------------------------------------------------------
GROUPS: dict[str, list[str]] = {
    "A": ["Messico", "Sudafrica", "Corea del Sud", "Cechia"],
    "B": ["Canada", "Bosnia-Erzegovina", "Qatar", "Svizzera"],
    "C": ["Brasile", "Marocco", "Haiti", "Scozia"],
    "D": ["USA", "Paraguay", "Australia", "Turchia"],
    "E": ["Germania", "Curaçao", "Costa d'Avorio", "Ecuador"],
    "F": ["Olanda", "Giappone", "Svezia", "Tunisia"],
    "G": ["Belgio", "Egitto", "Iran", "Nuova Zelanda"],
    "H": ["Spagna", "Capo Verde", "Arabia Saudita", "Uruguay"],
    "I": ["Francia", "Senegal", "Iraq", "Norvegia"],
    "J": ["Argentina", "Algeria", "Austria", "Giordania"],
    "K": ["Portogallo", "Congo DR", "Uzbekistan", "Colombia"],
    "L": ["Inghilterra", "Croazia", "Ghana", "Panama"],
}

# Nazioni ospitanti (vantaggio campo). USA + Canada + Messico.
HOSTS: set[str] = {"USA", "Canada", "Messico"}

# Debuttanti assoluti: storicamente perdono la prima partita (~78%).
DEBUTANTS: set[str] = {"Curaçao", "Capo Verde", "Giordania", "Uzbekistan"}

# Difensore del titolo (campione del mondo in carica). Storicamente, negli
# ultimi tre Mondiali il campione uscente è uscito ai gironi (3/4 = 75%).
DEFENDING_CHAMPION: str = "Argentina"

# ---------------------------------------------------------------------------
# TIER SQUADRE — forza di base (1 = favorite, 4 = outsider/debuttanti)
# ---------------------------------------------------------------------------
TEAM_TIERS: dict[str, int] = {}


def _assign_tiers() -> None:
    tier1 = ["Argentina", "Francia", "Spagna", "Inghilterra", "Brasile",
             "Germania", "Portogallo", "Olanda"]
    tier2 = ["Belgio", "Croazia", "Uruguay", "Colombia", "USA", "Giappone",
             "Marocco", "Messico", "Svizzera", "Senegal", "Austria", "Ecuador"]
    tier3 = ["Corea del Sud", "Australia", "Turchia", "Costa d'Avorio",
             "Norvegia", "Egitto", "Iran", "Svezia", "Tunisia", "Paraguay",
             "Algeria", "Arabia Saudita", "Ghana", "Canada", "Iraq"]
    tier4 = ["Scozia", "Qatar", "Bosnia-Erzegovina", "Cechia", "Panama",
             "Sudafrica", "Congo DR", "Uzbekistan", "Nuova Zelanda", "Haiti",
             "Giordania", "Capo Verde", "Curaçao"]
    for t, teams in [(1, tier1), (2, tier2), (3, tier3), (4, tier4)]:
        for team in teams:
            TEAM_TIERS[team] = t


_assign_tiers()

# Forza d'attacco/difesa di base ricavata dal tier. Sono PRIOR, non verità:
# il modello li raffina con dati reali (xG, ELO, ranking) quando disponibili.
# Valori in "gol attesi" su scala calcio internazionale.
_TIER_ATTACK = {1: 1.75, 2: 1.45, 3: 1.20, 4: 0.95}
_TIER_DEFENSE = {1: -0.55, 2: -0.35, 3: -0.15, 4: 0.05}


def base_attack(team: str) -> float:
    return _TIER_ATTACK[TEAM_TIERS.get(team, 3)]


def base_defense(team: str) -> float:
    """Contributo difensivo: più negativo = difesa più forte (concede meno)."""
    return _TIER_DEFENSE[TEAM_TIERS.get(team, 3)]


def group_of(team: str) -> str | None:
    for g, teams in GROUPS.items():
        if team in teams:
            return g
    return None


# ---------------------------------------------------------------------------
# TREND STORICI VERIFICATI — da usare nel modello e nella selezione
# Fonti: VegasInsider, ActionNetwork, WinnersAndWhiners (1998–2022).
# ---------------------------------------------------------------------------
WORLD_CUP_TRENDS: dict[str, float | bool] = {
    "avg_goals_group_stage": 2.54,
    "avg_goals_knockout": 2.11,
    "over_2_5_group": 0.53,
    "over_2_5_knockout": 0.38,
    # Edge storico STRUTTURALE: Under 2.5 nei knockout, +18.7% ROI dal 1998.
    "under_2_5_knockout_roi": 0.187,
    "favorite_wins_first_match": 0.65,
    "top_seed_wins_group": 0.72,
    "host_goal_diff_boost": 0.64,
    "host_wins_tournament": 6 / 22,
    "defending_champion_group_exit": 3 / 4,
    "draw_90min_knockout": 0.32,
    "debutant_loses_first_match": 0.78,
    "warm_weather_team_boost": 0.37,
    "third_place_advances": True,
}

# ---------------------------------------------------------------------------
# CORRELAZIONE — quanto due selezioni sono dipendenti (0 = indipendenti)
# REGOLA ASSOLUTA: mai combinare in schedina due match dello stesso girone
# alla 3ª giornata (si giocano in contemporanea, esiti fortemente correlati).
# ---------------------------------------------------------------------------
CORRELATION: dict[str, float] = {
    "same_group_matchday_3": 0.95,
    "same_group_same_day": 0.85,
    "same_group_diff_day": 0.40,
    "same_confederation": 0.10,
    "independent": 0.0,
}
