# ISTRUZIONI — cosa resta da fare a te

Il **codice** è pronto e gira (154 test verdi, API + backtester + bot funzionanti
con dati mock). Quello che segue è ciò che **solo tu** puoi fare: serve la TUA
macchina, i TUOI account/chiavi e il TUO repo. Tutto il resto (codice) lo faccio io.

> ⚠️ **Gioco responsabile.** Questo sistema ha valore atteso negativo per
> natura. Non andare MAI live senza un backtest con dati reali che dia ROI e
> CLV positivi. Gioca solo soldi che puoi perdere. Supporto in Italia: 800 558822.

---

## 📱 ADESSO: Telegram da telefono (passo-passo)

Tutto questo si fa **dal telefono**, senza PC. Alla fine ricevi il piano del
giorno su Telegram, automaticamente ogni mattina, **senza tenere acceso nulla**.

### A) Crea il bot (2 minuti, dentro Telegram)
1. Apri Telegram, cerca **@BotFather**, avvialo.
2. Invia `/newbot`, scegli un nome e uno username (deve finire per `bot`).
3. BotFather ti dà un **token** tipo `123456:ABC-DEF...`. Copialo.

### B) Trova il tuo chat_id (dal browser del telefono)
1. Apri una chat col tuo nuovo bot e mandagli un messaggio qualsiasi (es. "ciao").
2. Nel browser apri: `https://api.telegram.org/bot<IL_TUO_TOKEN>/getUpdates`
   (sostituisci `<IL_TUO_TOKEN>`).
3. Cerca `"chat":{"id": ...}`: quel numero è il tuo **chat_id**.

> 👉 Se mi incolli qui **token + chat_id**, ti mando subito un **messaggio di
> prova reale** sul telefono da questa sessione, così vedi che funziona. (Il
> token è una credenziale: dopo le prove puoi rigenerarlo da BotFather con
> `/revoke` quando vuoi.)

### C) Invio automatico ogni mattina (GitHub Actions, niente server)
Una volta che il repo è su GitHub (passo 2), il file
`.github/workflows/telegram-daily.yml` è già pronto. Devi solo aggiungere i
**Secrets** (dal sito/app GitHub, quindi anche da telefono):

1. Repo → **Settings** → **Secrets and variables** → **Actions** → **New secret**:
   - `TELEGRAM_BOT_TOKEN` = il token di BotFather
   - `TELEGRAM_CHAT_ID` = il tuo chat_id
   - `ODDS_API_KEY` = (opzionale) chiave The Odds API
2. Tab **Actions** → workflow "Piano Telegram giornaliero" → **Run workflow** per
   provarlo subito; poi parte da solo alle **08:00** ogni giorno.

Senza secret il workflow gira lo stesso ma in **dry-run** (non invia nulla): è
sicuro per provare.

---

## 1. Far girare il sistema sul TUO computer (5 minuti, senza chiavi)

Ti serve **Python 3.11+**. Poi:

```bash
tar -xzf worldcupedge.tar.gz
cd worldcupedge

# (opzionale ma consigliato) ambiente virtuale
python3 -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate

# 1) i test del core girano SENZA installare nulla
python -m unittest discover -s tests

# 2) demo: genera un piano 4-4-2
python -m examples.demo_piano

# 3) backtester (su dati di esempio)
python -m src.backtest.backtester

# 4) API web (serve fastapi+uvicorn)
pip install fastapi "uvicorn[standard]" pydantic
uvicorn src.main:app --reload
#   → apri http://127.0.0.1:8000/piano  (piano da dati mock)
#   → docs interattive: http://127.0.0.1:8000/docs
```

Per l'intero stack (PostgreSQL + Redis) serve **Docker**: `docker-compose up -d`.

---

## 2. Mettere il progetto su GitHub

Io non posso crearti il repository (l'integrazione non ha il permesso). Tu sì:

1. Vai su github.com → **New repository** → nome `worldcupedge` → **Private** → *Create*
   (NON aggiungere README/.gitignore: il progetto li ha già).
2. Dalla cartella del progetto:
   ```bash
   git remote add origin https://github.com/agapasqualino07-eng/worldcupedge.git
   git push -u origin main
   ```
3. Se vuoi che da qui in poi lavori io sul repo, **aggiungilo allo scope di
   questa sessione** (dalle impostazioni dell'ambiente Claude Code) e dimmelo:
   da lì posso committare e pushare i prossimi moduli da solo.

---

## 3. Le chiavi/credenziali (servono per i DATI REALI)

Senza queste il sistema gira ma con dati **mock**. Per quote e dati veri:

| Chiave | Dove ottenerla | Costo | Variabile `.env` |
|---|---|---|---|
| **The Odds API** | [the-odds-api.com](https://the-odds-api.com) → registrati → copia la API key | Free tier disponibile | `ODDS_API_KEY` |
| **Dati partite** (risultati/calendario) | [API-Football](https://www.api-football.com) (o simile) | Free tier limitato | `FOOTBALL_API_KEY` |
| **Bot Telegram** | Su Telegram apri **@BotFather** → `/newbot` → copia il token | Gratis | `TELEGRAM_BOT_TOKEN` |
| **Il tuo chat_id** | Scrivi al tuo bot, poi apri `https://api.telegram.org/bot<TOKEN>/getUpdates` e leggi `chat.id` | Gratis | `TELEGRAM_CHAT_ID` |

> **SNAI:** lo scraping diretto del sito SNAI (Playwright) è in roadmap ed è
> fragile/da valutare. Per ora la fonte quote è **The Odds API** (LIV 2). Le quote
> mostrate vanno comunque **verificate su SNAI** prima di piazzare.

### Compila `.env`
```bash
cp .env.example .env
# apri .env e incolla le chiavi sopra
```

### Prova con dati reali
```bash
# quote reali da The Odds API (con ODDS_API_KEY nel .env)
python -c "from src.data.odds_api import OddsCollector; \
from src.config import settings; \
print(OddsCollector(settings.odds_api_key).get_odds(use_mock=False)[:3])"

# avvia il bot Telegram (con TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID)
python -m src.notifications.telegram_bot     # comandi: /oggi /stato /aiuto
```

---

## 4. Backtest con dati REALI (obbligatorio prima del denaro)

Il backtester gira già, ma su dati **sintetici** (`src/backtest/sample_data.py`,
chiaramente etichettati: NON sono risultati veri). Per un backtest valido:

1. Procurati i risultati storici reali (Mondiale 2022, Euro 2024) con quote di
   apertura e chiusura.
2. Sostituisci `sample_history()` con un loader da CSV/DB (stesso formato di
   `HistoricalMatch`).
3. Esegui `python -m src.backtest.backtester`: **vai live solo se PASS**
   (ROI > 0 **e** CLV medio > 0).

Se mi dai i dati (o l'accesso alla fonte), il loader te lo scrivo io.

---

## 5. Cosa posso ancora costruire io (non ti serve fare nulla)

Roadmap che sviluppo in autonomia con dati mock/di esempio, appena mi dici di procedere:

- **Ensemble ML** (Logistic/RF/XGBoost/LightGBM + stacking) e **calibrazione**
  (ECE < 0.05) per superare i prior grezzi del Poisson — è il pezzo che oggi
  fa "sballare" il modello sugli underdog.
- **Persistenza** PostgreSQL + Alembic (oggi i piani non vengono salvati).
- **Cashout advisor** live, **warm-up manager**, **market movement detector**.
- **Dashboard** Plotly Dash con aggiornamenti WebSocket.
- **Scheduler** (report mattutino automatico alle 08:00, ecc.).
- **News engine** (sentiment + impact, con fonte+URL).

---

## In sintesi — la tua to-do

- [ ] Installa Python 3.11 e fai girare i test/demo (passo 1)
- [ ] Crea il repo GitHub `worldcupedge` e fai `git push` (passo 2)
- [ ] *(opzionale)* aggiungi il repo allo scope della sessione così pusho io
- [ ] Registra le chiavi: Odds API, API-Football, bot Telegram (passo 3)
- [ ] Compila `.env`
- [ ] Procurati i dati storici reali per un backtest valido (passo 4)
- [ ] Dimmi quale modulo della roadmap vuoi che costruisca dopo (passo 5)
