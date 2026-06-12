# 🖥️ Quando hai il PC — guida passo-passo

Lavoro diviso in **step chiari e indipendenti**. Fai gli step in ordine; ognuno
dice **cosa fare**, **i comandi esatti** e **come capire che è andato bene**.
Tempo totale: ~30–40 minuti.

> Hai già: il bot Telegram **@BetMondiale_bot** (token di BotFather) e il tuo
> **chat_id = 931898568**. Ti serviranno allo STEP 4.

> ⚠️ Gioco responsabile. Non andare live con denaro vero finché lo STEP 6
> (backtest con dati reali) non dà ROI e CLV positivi. In Italia: 800 558822.

---

## STEP 0 — Installa i prerequisiti  ⏱️ 5 min

**Cosa:** ti servono Python 3.11+ e Git.

- Windows: installa da [python.org](https://www.python.org/downloads/) (spunta
  *"Add Python to PATH"*) e [git-scm.com](https://git-scm.com/download/win).
- Mac: `brew install python git` (oppure scaricali dai siti).

**Verifica (deve stampare le versioni):**
```bash
python --version      # o python3 --version  → 3.11 o superiore
git --version
```
✅ **Fatto se:** vedi i numeri di versione.

---

## STEP 1 — Scompatta e fai girare tutto in locale  ⏱️ 5 min

**Cosa:** verificare che il sistema funziona, senza chiavi.

```bash
tar -xzf worldcupedge.tar.gz
cd worldcupedge

# 1) i test (zero dipendenze)
python -m unittest discover -s tests

# 2) demo del piano 4-4-2
python -m examples.demo_piano

# 3) backtester (dati di esempio)
python -m src.backtest.backtester
```
✅ **Fatto se:** i test dicono `OK` (142 test), la demo stampa un piano, il
backtester stampa un verdetto PASS/FAIL.

---

## STEP 2 — Avvia l'API web  ⏱️ 3 min  (opzionale ma consigliato)

```bash
python -m venv .venv
# attiva l'ambiente:  Windows → .venv\Scripts\activate   |   Mac → source .venv/bin/activate
pip install fastapi "uvicorn[standard]" pydantic
uvicorn src.main:app --reload
```
Apri nel browser:
- `http://127.0.0.1:8000/dashboard` → **Dashboard**: partite di oggi + modulo per
  chiedere QUALSIASI partita (es. Argentina vs Messico) e avere il report con il
  consiglio di scommessa.
- `http://127.0.0.1:8000/piano` → il piano in JSON.
- `http://127.0.0.1:8000/report?home=Argentina&away=Messico&odds_1=1.85&odds_x=3.7&odds_2=4.5`
  → report di una singola partita.
- `http://127.0.0.1:8000/docs` → tutte le API.

✅ **Fatto se:** la Dashboard si apre e il report di una partita compare. (Ctrl+C per fermare.)

> 💬 Su **Telegram** (quando il bot gira con `python -m src.notifications.telegram_bot`):
> `/oggi` mostra il piano con un **pulsante report per ogni partita**, e
> `/partita Argentina - Messico` dà il report completo di quella partita.

---

## STEP 3 — Metti il progetto su GitHub  ⏱️ 5 min

**Cosa:** serve per l'invio automatico (STEP 5).

1. Su [github.com](https://github.com/new) crea un repo **vuoto** chiamato
   `worldcupedge`, **Private**. NON aggiungere README/.gitignore.
2. Dalla cartella del progetto:
   ```bash
   git remote add origin https://github.com/agapasqualino07-eng/worldcupedge.git
   git branch -M main
   git push -u origin main
   ```
   (Se chiede login, usa un *Personal Access Token* di GitHub come password:
   github.com → Settings → Developer settings → Tokens.)

✅ **Fatto se:** ricaricando la pagina del repo vedi tutti i file.

---

## STEP 4 — Configura i Secret su GitHub  ⏱️ 5 min

**Cosa:** dare a GitHub le credenziali, in modo sicuro (non finiscono nel codice).

Vai su: repo → **Settings** → **Secrets and variables** → **Actions** →
**New repository secret**, e crea questi:

| Nome del secret | Valore |
|---|---|
| `TELEGRAM_BOT_TOKEN` | il token che ti ha dato @BotFather |
| `TELEGRAM_CHAT_ID` | `931898568` |
| `ODDS_API_KEY` | *(opzionale per ora)* la chiave di [the-odds-api.com](https://the-odds-api.com) |

✅ **Fatto se:** nella lista Secrets vedi i nomi (i valori restano nascosti).

> 🔒 Visto che il token l'avevi incollato in chat, ti conviene rigenerarlo:
> @BotFather → `/revoke` → scegli BetMondiale_bot → copia il NUOVO token e
> mettilo nel secret.

---

## STEP 5 — Attiva l'invio automatico giornaliero  ⏱️ 3 min

**Cosa:** il workflow `.github/workflows/telegram-daily.yml` è già nel progetto.

1. Repo → tab **Actions**. Se chiede di abilitare i workflow, conferma.
2. Apri **"Piano Telegram giornaliero"** → **Run workflow** (avvio manuale di prova).
3. Controlla Telegram: deve arrivare il piano.

✅ **Fatto se:** ricevi il messaggio su Telegram. Da qui in poi parte **da solo
ogni mattina alle 08:00**, senza che tu faccia nulla.

---

## STEP 6 — Backtest con dati reali  ⏱️ variabile  (PRIMA del denaro vero)

**Cosa:** oggi il backtester gira su dati **sintetici** (`src/backtest/sample_data.py`).
Per un giudizio valido servono risultati storici reali (Mondiale 2022, Euro 2024)
con quote di apertura e chiusura.

1. Procurati i dati (CSV) e sostituisci `sample_history()` con un loader dal CSV.
2. `python -m src.backtest.backtester`
3. **Vai live solo se il verdetto è PASS** (ROI > 0 **e** CLV medio > 0).

> Se mi dai i dati (o la fonte), il loader te lo scrivo io.

---

## Dopo: cosa posso costruire io (quando vuoi)

Dimmi solo "procedi con X" e lo sviluppo in autonomia (gira con dati di esempio):

- **Ensemble ML** (XGBoost/LightGBM + stacking) e calibrazione avanzata ECE<0.05
- **Scraper SNAI** (LIV 1) + dati squadre reali (ELO, ranking FIFA, xG)
- **Dashboard** web con grafici (bankroll, equity curve)
- **Update live** durante le partite + market movement detector
- **News engine** con sentiment

---

## Riepilogo a colpo d'occhio

| Step | Cosa | Ti serve |
|---|---|---|
| 0 | Installa Python + Git | — |
| 1 | Test/demo/backtest in locale | — |
| 2 | API web | — |
| 3 | Repo su GitHub + push | account GitHub |
| 4 | Secret (token, chat_id) | token BotFather |
| 5 | Attiva il workflow giornaliero | — |
| 6 | Backtest con dati reali | dati storici |
