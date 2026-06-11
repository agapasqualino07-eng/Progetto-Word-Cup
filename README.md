# WorldCupEdge ⚽🎯

[![Test](https://github.com/agapasqualino07-eng/Progetto-Word-Cup/actions/workflows/tests.yml/badge.svg)](https://github.com/agapasqualino07-eng/Progetto-Word-Cup/actions/workflows/tests.yml)

Sistema di **ricerca quantitativa** sulle scommesse per la **FIFA World Cup 2026**
(48 nazionali, 104 partite, 11 giugno – 19 luglio 2026).

Tratta il torneo come un mercato potenzialmente inefficiente e risponde a una
sola domanda: **"il mercato ha prezzato correttamente questa partita?"**
Se sì → non fa nulla. Se no → quantifica l'errore (edge) e propone una bet.

Tutto il sistema comunica in **italiano**; il codice e le variabili sono in inglese per convenzione.

> ## ⚠️ Premessa onesta — leggere prima di tutto
>
> Le scommesse sportive hanno **valore atteso negativo per costruzione** (il
> margine del bookmaker). Il paper **KellyBench (2026)** ha mostrato che *tutti*
> i modelli AI frontier testati su un campionato reale **hanno perso denaro**.
>
> Questo progetto **non garantisce profitti**. Le cifre del tipo "55% di
> probabilità di arrivare a €1.000" sono ipotesi di simulazione, non risultati
> dimostrati. Il **backtest è obbligatorio** prima di rischiare denaro reale: se
> non mostra ROI e CLV positivi, il sistema **non deve andare live**.
>
> Gioca solo denaro che puoi perdere. Gioco responsabile: in Italia, 800 558822
> (Telefono Verde Nazionale per le problematiche legate al gioco d'azzardo).

---

## Cosa c'è già (implementato e testato)

Il **core quantitativo** è funzionante, senza dipendenze esterne (gira con la
sola standard library) e coperto da test:

| Modulo | File | Cosa fa |
|---|---|---|
| Costanti torneo | `src/constants.py` | Gironi, host, debuttanti, tier squadre, trend storici, matrice correlazione |
| Modello Poisson | `src/ml/poisson_model.py` | Probabilità 1/X/2 e Over/Under 2.5 con vantaggio host |
| Value engine | `src/betting/value_engine.py` | Edge, probabilità implicita, rimozione margine, soglia di valore (≥5%) |
| Allocatore 4-4-2 | `src/betting/daily_allocator.py` | Piano giornaliero: 4 singole + 4 doppie + 2 triple, adattivo al n° partite |
| Correlazione | `src/betting/correlation_matrix.py` | Vieta combo correlate (regola assoluta: mai stesso girone 3ª giornata) |
| Risk manager | `src/betting/risk_manager.py` | Adaptive confidence (riduce dopo 3 perdite), floor/cap stake |
| Anti-allucinazione | `src/anti_hallucination.py` | Livelli di sicurezza, soglie dati, mai "sicuro", mai dati inventati |
| Collector quote | `src/data/odds_api.py` | The Odds API (urllib) con fallback **mock** se manca la chiave |
| **News engine** | `src/data/news/` + `src/features/news_features.py` | RSS testate → sentiment (lessico) + impatto infortuni + morale; fonte+data+URL |
| Calibrazione | `src/ml/calibration.py` | Shrinkage verso il mercato: smorza gli edge spuri (anti-overconfidence) |
| Pipeline | `src/services/pipeline.py` | Quote → modello → **calibrazione** → selezioni → piano |
| Backtester | `src/backtest/backtester.py` | Walk-forward con ROI + **CLV**; gate `passed()` per il live |
| Portafoglio | `src/portfolio/tracker.py` | Persistenza **SQLite**: conferma bet, regola risultati, bankroll, ROI |
| Warm-up | `src/betting/warmup.py` | Stake ridotto nelle prime giornate (anti all-in) |
| Cashout advisor | `src/betting/cashout_advisor.py` | Consiglio live (trigger espulsione/gol tardivo + EV residuo) |
| **Report partita** | `src/services/match_report.py` | Report on-demand di una partita: pronostico + se/cosa scommettere |
| Bot Telegram | `src/notifications/` | Piano mattutino + report serale + `/partita` + pulsanti report + invio stdlib |
| API + Dashboard | `src/main.py` | FastAPI: `/piano`, `/report`, **`/dashboard`** (HTML), `POST /piano/genera` |

### Avvio rapido (senza installare nulla)

```bash
python -m unittest discover -s tests   # 77 test (solo standard library)
python -m examples.demo_piano          # demo: piano 4-4-2
python -m src.backtest.backtester      # backtest (dati reali se presenti, altrimenti sample)
```

### Backtest con dati storici REALI

Il backtester è il **gate prima del denaro reale**: ha senso solo su partite vere.

1. Copia il template e riempilo con partite reali (Mondiale 2022, Euro 2024…),
   quote di **apertura** e **chiusura** incluse:
   ```bash
   cp data/history_template.csv data/raw/history.csv   # poi compila il CSV
   python -m src.backtest.backtester                    # gira sui tuoi dati reali
   ```
   In alternativa indica un percorso: `WCE_HISTORY_CSV=/percorso/file.csv python -m src.backtest.backtester`
2. Il loader **valida** ogni riga (esito 1/X/2, quote > 1.0) e **non inventa nulla**:
   se il file manca, avvisa e ripiega sul sample etichettato (risultato *non* indicativo).
3. Regola d'oro: **live solo se ROI > 0 e CLV medio > 0** sul backtest reale.

> ⚠️ Inserisci solo quote/risultati **verificati**. Il file reale (`data/raw/`) non
> viene versionato.

👉 **Cosa devi fare tu** (chiavi API, repo GitHub, run sul tuo PC, dati storici):
vedi **[`ISTRUZIONI.md`](ISTRUZIONI.md)**.

### Avvio completo (con dipendenze / Docker)

```bash
cp .env.example .env          # compila le chiavi
docker-compose up -d          # FastAPI :8000 + PostgreSQL + Redis
# oppure, in locale:
pip install -r requirements.txt
uvicorn src.main:app --reload
pytest --cov=src
```

---

## La strategia in breve — allocazione 4-4-2

Ogni giorno con ≥4 partite il **bankroll disponibile** si divide in **10 bet**:

```
4 SINGOLE  (40%)   quota target 1.50–2.50
4 DOPPIE   (40%)   quota target 3.00–6.00
2 TRIPLE   (20%)   quota target 6.00–15.00
```

- **Reinvestimento (compound):** lo stake = bankroll / 10, quindi si adatta ogni
  giorno (vinci → punti di più; perdi → punti di meno).
- **Adattamento al calendario:** con <4 partite il piano si riduce
  (1→10%, 2→30%, 3→60% del bankroll) e il budget non usato **resta** per i giorni dopo.
- **Floor €5 / Cap €20** sullo stake per singola bet.
- **SKIP se edge < 5%:** non si scommette su una partita solo perché c'è. Questa è
  la principale contromisura agli errori di KellyBench.
- **Correlazione:** mai combinare in schedina due match dello stesso girone alla
  3ª giornata (si giocano in contemporanea).

---

## Roadmap — cosa manca (scheletri / da costruire)

Questo repo è una **fondazione**. I pezzi seguenti sono progettati ma non ancora
implementati (vedi `ISTRUZIONI.md` §5):

- **Scraper SNAI** (Playwright, LIV 1) + dati squadre (FBref/Transfermarkt/ELO/
  ranking FIFA). *La fonte quote The Odds API (LIV 2) c'è già.*
  ✅ **Iniezione rating reali nel modello** già pronta
  (`src/ml/ratings_loader.py`): basta popolare `data/raw/team_ratings.csv`
  (template + 48 squadre in `data/team_ratings_template.csv`) e il Poisson usa
  forza continua reale al posto delle fasce. Resta da automatizzare il *fetch*.
- **Ensemble ML:** Logistic/RF/XGBoost/LightGBM + stacking, calibrazione avanzata
  (ECE < 0.05), Optuna, SHAP. *Una calibrazione base (shrinkage) c'è già.*
  ✅ **Ossatura ensemble pronta** (`src/ml/ensemble.py`): classificatore
  (LogisticRegression) su feature Poisson+mercato, **gated** — si allena solo con
  scikit-learn installato e storico reale (`data/raw/history.csv`); altrimenti
  ripiega sul Poisson calibrato. Da estendere con feature ricche + XGBoost/Optuna.
- **News engine avanzato:** più testate, sentiment con modello calibrato (oggi:
  RSS + lessico trasparente), risoluzione automatica partita↔squadre.
- ~~**Loader dati storici reali** per il backtest~~ ✅ **FATTO**
  (`src/backtest/history_loader.py`): carica partite reali da CSV con validazione;
  serve ancora popolare il dataset (`data/raw/history.csv`). Vedi sotto.
- **Market movement detector** + integrazione live del cashout advisor.
- **Update live** Telegram durante le partite (oggi: piano mattutino + report serale).
- **Dashboard** Plotly Dash via WebSocket.
- **Migrazione a PostgreSQL** + Alembic (oggi: SQLite), **Celery** + Redis, **APScheduler**.

La struttura cartelle di destinazione è descritta nella specifica originale
(`worldcupedge/src/{data,ml,betting,backtest,portfolio,reporting,notifications,dashboard,api}`).

---

## Struttura attuale

```
worldcupedge/
├── src/
│   ├── config.py               # settings da env
│   ├── constants.py            # gironi, tier, trend, correlazione
│   ├── anti_hallucination.py   # livelli sicurezza, regole di verità
│   ├── main.py                 # FastAPI: /piano, /piano/genera
│   ├── models/schemas.py       # Selection, Bet, DailyPlan (dataclass)
│   ├── ml/poisson_model.py     # modello Poisson
│   ├── data/odds_api.py        # collector quote (The Odds API + mock)
│   ├── services/               # pipeline + serializers
│   ├── backtest/               # backtester + dati di esempio
│   ├── notifications/          # message_formatter + telegram_bot
│   └── betting/
│       ├── value_engine.py · correlation_matrix.py
│       ├── daily_allocator.py  # allocazione 4-4-2
│       └── risk_manager.py
├── tests/                      # 77 test (unittest, zero dipendenze)
├── examples/demo_piano.py      # demo end-to-end
├── requirements.txt · Dockerfile · docker-compose.yml
├── .env.example · pytest.ini
├── ISTRUZIONI.md               # cosa devi fare TU (chiavi, repo, run)
└── CLAUDE.md                   # guida per assistenti AI
```

---

## Principi non negoziabili

1. **Onestà sui dati.** Mai inventare statistiche/quote/formazioni. Se manca un
   dato → `DATO MANCANTE` / `VERIFICA SU SNAI` / `NON CONFERMATA`.
2. **Mai "sicuro".** Solo livelli ALTA / MEDIA / BASSA / INSUFFICIENTE. Sotto
   soglia di completezza dati (60%) → la bet è esclusa dal piano.
3. **Backtest prima del denaro.** Niente live senza ROI e CLV positivi a backtest.
4. **Disciplina sull'edge.** Sotto il 5% non si gioca.
