"""
Provider del modello di default — un solo punto di verità per TUTTI i canali.

Bot Telegram, API FastAPI e dashboard devono usare lo STESSO modello (rating
FIFA reali se disponibili, fasce base altrimenti). Prima questo codice viveva
solo nel bot: l'API usava le fasce → pronostici incoerenti tra i canali.
"""
from __future__ import annotations

from ..ml.poisson_model import PoissonModel

MODEL_NOTE_RATINGS = "🧠 Modello: rating reali"


def get_default_model() -> tuple[PoissonModel | None, str | None]:
    """
    (modello, nota) — modello con rating REALI se presenti, altrimenti (None, None)
    e il chiamante usa il PoissonModel base a fasce. File rating malformato →
    avviso a console e fallback (mai bloccare il piano per un file sporco).
    """
    from ..ml.ratings_loader import RatingsLoadError, load_ratings_model

    try:
        model = load_ratings_model()
    except RatingsLoadError as exc:
        print(f"[ratings] file rating non valido: {exc} → uso le fasce base")
        return None, None
    if model is not None:
        return model, MODEL_NOTE_RATINGS
    return None, None
