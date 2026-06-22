# CLAUDE.md

Guida per assistenti AI che lavorano in questo repository. Leggere prima di modificare.

## Cos'è

**WorldCupEdge** — sistema di ricerca quantitativa sulle scommesse per la FIFA
World Cup 2026. Stima la probabilità "vera" di ogni partita, la confronta con la
quota del bookmaker e propone un piano giornaliero di bet (allocazione 4-4-2)
**solo** dove c'è edge sufficiente. Tutta la comunicazione è in **italiano**;
codice e identificatori in **inglese**.

Leggere `README.md` per il quadro completo (strategia, roadmap, premessa onesta
sui rischi). Questo file è la guida operativa al codice.

## Stato: fondazione, non sistema completo

Implementato e testato (147 test): core quantitativo (constants, Poisson, value
engine, allocatore 4-4-2, correlazione, risk manager, anti-allucinazione),
**collector quote** (The Odds API + mock), **calibrazione** (shrinkage al mercato),
**pipeline** end-to-end, **backtester** (ROI+CLV), **portafoglio** SQLite,
**warm-up**, **cashout advisor**, **API** FastAPI (`/piano`, `/piano/genera`),
**Telegram** (piano mattutino + report serale + `/partita` + invio stdlib +
GitHub Action), **report on-demand** (`match_report` + `/report` + `/dashboard`),
**news engine** (RSS testate → sentiment/impatto/morale, in `data/news/` +
`features/news_features.py`). Roadmap (NON implementato): scraper SNAI, ensemble
ML (xgboost/lightgbm), dashboard ricca con grafici, migrazione PostgreSQL/Celery,
update live, loader dati storici reali. Vedi README §Roadmap, `ISTRUZIONI.md`,
`QUANDO_HAI_IL_PC.md`. Regola news: fonte+data+URL sempre; offline → `DATO
MANCANTE`, mai notizie inventate (i `mock_news` sono solo per demo/test).

## Comandi

```bash
python -m unittest discover -s tests   # 147 test (standard library, zero deps)
python -m examples.demo_piano          # demo end-to-end
python -m src.backtest.backtester      # backtest (dati di esempio)
uvicorn src.main:app --reload          # API (richiede fastapi+uvicorn)
docker-compose up -d                   # stack completo (FastAPI + PG + Redis)
```

Dati esterni: il collector usa **mock** senza chiave (`source="MOCK"`, mai
spacciato per reale); con `ODDS_API_KEY` chiama The Odds API. Il bot Telegram va
in **dry-run** (stampa) senza `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`. Mantieni
questo pattern "degrada con grazia, mai dati finti spacciati per veri" per ogni
nuova fonte dati.

**Vincolo chiave:** il core deve restare **senza dipendenze esterne** ed eseguibile
con la sola standard library — i test girano così. Il Poisson è in puro Python
(`poisson_pmf`), non scipy. Se aggiungi un modulo che richiede numpy/scipy/ecc.,
isolalo (es. sotto `ml/`) e rendi l'import opzionale (vedi `main.py` con FastAPI),
così i test del core continuano a girare senza installare nulla.

## Architettura e convenzioni

- **Modelli dominio** (`src/models/schemas.py`): `Selection` (un esito su una
  partita, con `model_prob` + `odds` → `edge`/`implied_prob` calcolati),
  `Bet` (1/2/3 gambe), `DailyPlan`. Sono **dataclass**, non Pydantic, per non
  introdurre dipendenze nel core. Pydantic è previsto solo per il layer API/DB.
- **Flusso:** `PoissonModel.predict_match` → `Selection` → `value_engine`
  (filtra per edge ≥ 5%) → `DailyAllocator.allocate` (costruisce 4-4-2 con vincoli
  di correlazione) → `DailyPlan`. `src/main.build_plan()` incapsula il flusso.
- **Convenzione difesa nel Poisson:** `base_defense` più **negativo** = difesa più
  forte; il lambda avversario si calcola **sommando** la difesa
  (`attack + defense`), non sottraendola. (Un test cattura questa inversione —
  non "correggerla" cambiando il segno senza capire.)
- **Regole immutabili** (codificate, non opinioni):
  - edge < 5% → **SKIP** (`value_engine.MIN_EDGE_SINGLE`);
  - completezza dati < 60% → bet esclusa (`anti_hallucination.MIN_DATA_COMPLETENESS`);
  - mai combinare due match **stesso girone, 3ª giornata** in una schedina
    (`correlation_matrix.is_forbidden_pair`);
  - stake floor €5 / cap €20 (`risk_manager`);
  - mai dire "sicuro" → solo `ConfidenceLevel` ALTA/MEDIA/BASSA/INSUFFICIENTE.
- **Anti-allucinazione** (`src/anti_hallucination.py`): è il cuore etico. Quando
  un dato manca usa i placeholder testuali (`DATO MANCANTE`, `VERIFICA SU SNAI`,
  `NON CONFERMATA`), **mai** un numero inventato. Vale anche per le risposte in chat.

## Test

`tests/` usa `unittest` (no pytest necessario). Ogni regola critica ha un test
(allocazione 4-4-2, correlazione vietata, edge → SKIP, adaptive confidence,
Poisson normalizzato). **Aggiungi un test per ogni nuova regola di scommessa** e
fai girare la suite prima di considerare fatto un cambiamento.

## Onestà (vale per il codice e per la chat)

Questo è uno strumento a valore atteso negativo per natura (margine del book).
Non promettere profitti, non inventare numeri, non rimuovere i filtri prudenziali
(edge minimo, completezza dati, correlazione) per "produrre più bet". Il backtest
è il gate verso il denaro reale: senza ROI/CLV positivi, niente live.
