"""
Ensemble (roadmap #3) — combina più segnali per stimare 1/X/2.

Onesto e "gated", nel rispetto dei vincoli del progetto:
  - Le librerie ML (scikit-learn) sono OPZIONALI: import lazy, fallback se assenti
    (il core resta eseguibile con la sola standard library).
  - Il classificatore si allena SOLO su dati storici REALI (history_loader).
    Niente addestramento su dati finti: senza storico → niente modello ML.
  - Senza modello allenato → si usa il Poisson CALIBRATO sul mercato (esattamente
    il comportamento attuale della pipeline). Nessun peggioramento "a sorpresa".
  - Prima di fidarsi del modello ML per soldi veri: backtest (ROI + CLV positivi).

Segnali combinati come feature trasparenti: probabilità del Poisson + probabilità
"fair" del mercato (quote de-vigate). Il classificatore impara dai dati reali come
pesarli. È l'ossatura su cui innestare poi feature ricche (rating, news, xG).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..betting.value_engine import remove_margin
from ..ml.calibration import calibrate_1x2
from ..ml.poisson_model import PoissonModel

OUTCOMES = ("1", "X", "2")


def sklearn_available() -> bool:
    """True se scikit-learn è installato (le librerie ML sono opzionali)."""
    try:
        import sklearn  # noqa: F401
        return True
    except Exception:
        return False


def match_features(model_probs: dict[str, float], market_fair: dict[str, float]) -> list[float]:
    """Feature trasparenti per una partita: prob Poisson + prob mercato de-vigato."""
    return [
        model_probs["1"], model_probs["X"], model_probs["2"],
        market_fair["1"], market_fair["X"], market_fair["2"],
    ]


@dataclass
class EnsembleModel:
    """Poisson + (opzionale) classificatore ML allenato sui dati reali."""
    poisson: PoissonModel | None = None
    clf: object | None = None            # classificatore allenato, o None
    classes: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        self.poisson = self.poisson or PoissonModel()

    @property
    def trained(self) -> bool:
        return self.clf is not None

    def predict_1x2(
        self,
        home: str,
        away: str,
        odds_1: float,
        odds_x: float,
        odds_2: float,
        venue_country: str | None = None,
    ) -> dict[str, float]:
        """Probabilità 1/X/2. Con modello allenato usa il classificatore; senza,
        ripiega sul Poisson calibrato sul mercato (comportamento attuale)."""
        probs = self.poisson.predict_match(home, away, venue_country)
        mp = {"1": probs.prob_1, "X": probs.prob_x, "2": probs.prob_2}
        market = remove_margin(odds_1, odds_x, odds_2)

        if not self.trained:
            return calibrate_1x2(mp, market)

        feats = match_features(mp, market)
        proba = self.clf.predict_proba([feats])[0]
        out = {c: float(p) for c, p in zip(self.classes or OUTCOMES, proba)}
        # Garantisce le tre chiavi e la normalizzazione.
        full = {k: out.get(k, 0.0) for k in OUTCOMES}
        s = sum(full.values())
        return {k: v / s for k, v in full.items()} if s > 0 else mp


def train_ensemble(history: list) -> EnsembleModel:
    """
    Allena il classificatore sui dati storici REALI.
    Richiede scikit-learn e almeno qualche partita. Solleva RuntimeError altrimenti.
    """
    if not history:
        raise RuntimeError("Nessun dato storico: impossibile allenare (carica data/raw/history.csv).")
    if not sklearn_available():
        raise RuntimeError("scikit-learn non installato: 'pip install scikit-learn'.")

    from sklearn.linear_model import LogisticRegression

    poisson = PoissonModel()
    X: list[list[float]] = []
    y: list[str] = []
    for m in history:
        probs = poisson.predict_match(m.home, m.away, None)
        mp = {"1": probs.prob_1, "X": probs.prob_x, "2": probs.prob_2}
        market = remove_margin(m.open_1, m.open_x, m.open_2)
        X.append(match_features(mp, market))
        y.append(m.actual)

    if len(set(y)) < 2:
        raise RuntimeError("Servono esiti storici di più tipi (1/X/2) per allenare.")

    clf = LogisticRegression(max_iter=1000).fit(X, y)
    return EnsembleModel(poisson=poisson, clf=clf, classes=tuple(clf.classes_))


if __name__ == "__main__":
    # Allena dai dati reali se presenti + librerie disponibili; altrimenti spiega.
    from ..backtest.history_loader import HistoryLoadError, load_real_history

    try:
        history = load_real_history()
    except HistoryLoadError as exc:
        raise SystemExit(f"⚠️  Storico non valido: {exc}")

    if not history:
        print("⚠️  Nessun dato storico reale (data/raw/history.csv).")
        print("    L'ensemble ML si attiva solo con storico reale. Per ora: Poisson calibrato.")
    elif not sklearn_available():
        print("⚠️  scikit-learn non installato: 'pip install scikit-learn'.")
        print(f"    ({len(history)} partite pronte: si allenerà appena la libreria è presente.)")
    else:
        model = train_ensemble(history)
        print(f"✅ Ensemble allenato su {len(history)} partite (classi: {model.classes}).")
        print("   Prossimo passo OBBLIGATORIO: validare sul backtest (ROI + CLV) prima del live.")
