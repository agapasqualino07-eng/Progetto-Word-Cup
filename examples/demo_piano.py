"""
Demo end-to-end: dal modello al piano di giornata 4-4-2.

NB: le quote qui sono di ESEMPIO. Nel sistema reale arrivano da SNAI (con
fallback) e ogni dato porta con sé fonte e completezza. Qui dimostriamo solo
che la pipeline produce un piano coerente.

    python -m examples.demo_piano
"""
from __future__ import annotations

from datetime import date

from src.anti_hallucination import ConfidenceLevel
from src.ml.poisson_model import PoissonModel
from src.models.schemas import Outcome, Phase, Selection


def main() -> None:
    model = PoissonModel()

    # 6 partite di esempio (gironi diversi), 16 giugno 2026.
    fixtures = [
        ("Francia", "Senegal", "I", "USA"),
        ("Argentina", "Algeria", "J", "USA"),
        ("Austria", "Giordania", "J", "USA"),
        ("Norvegia", "Iraq", "I", "USA"),
        ("Spagna", "Capo Verde", "H", "USA"),
        ("Brasile", "Haiti", "C", "USA"),
    ]
    # Quote ILLUSTRATIVE: simuliamo un mercato "soft" mettendo le quote il 12%
    # SOPRA il fair value del modello, così esiste edge e la pipeline si attiva.
    # Nel sistema reale le quote arrivano da SNAI e l'edge va MISURATO, non creato.
    VALUE_MARGIN = 0.12

    selections: list[Selection] = []
    for i, (home, away, group, venue) in enumerate(fixtures, start=1):
        probs = model.predict_match(home, away, venue)
        fair_odds = 1.0 / probs.prob_1
        odds = round(fair_odds * (1 + VALUE_MARGIN), 2)
        selections.append(
            Selection(
                match_id=f"m{i}",
                home=home,
                away=away,
                outcome=Outcome.HOME,
                model_prob=probs.prob_1,
                odds=odds,
                group=group,
                matchday=1,
                kickoff_date=date(2026, 6, 16),
                phase=Phase.GROUP,
                data_completeness=0.95,
                confidence=ConfidenceLevel.ALTA,
            )
        )

    # build_plan vive in src.main per essere riusabile anche fuori da FastAPI.
    from src.main import build_plan

    plan = build_plan(selections, bankroll=142.0, plan_date=date(2026, 6, 16))

    print(f"☀️  PIANO — {plan.plan_date}  |  Bankroll €{plan.bankroll}  "
          f"|  Budget €{plan.budget}  |  Stake €{plan.stake}")
    print("\n🎯 SINGOLE")
    for b in plan.singole:
        s = b.legs[0]
        print(f"  {s.home} ({s.outcome.value}) @ {s.odds}  "
              f"edge {s.edge:+.1%}  → €{b.stake}")
    print("\n🎫 DOPPIE")
    for b in plan.doppie:
        legs = " + ".join(f"{l.home}" for l in b.legs)
        print(f"  {legs} @ {b.combined_odds}  edge {b.edge:+.1%}  → €{b.stake}")
    print("\n🎰 TRIPLE")
    for b in plan.triple:
        legs = " + ".join(f"{l.home}" for l in b.legs)
        print(f"  {legs} @ {b.combined_odds}  edge {b.edge:+.1%}  → €{b.stake}")
    print(f"\nTotale puntato: €{plan.total_staked}  su {len(plan.all_bets)} bet")


if __name__ == "__main__":
    main()
