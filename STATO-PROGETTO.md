# STATO DEL PROGETTO — punto di ripresa

Documento di passaggio per riprendere il lavoro (anche in una nuova chat /
sessione di Claude Code). Riassume dove siamo, cosa è fatto e i prossimi passi.

## Cos'è
**WorldCupEdge** — sistema di ricerca quantitativa sulle scommesse per la FIFA
World Cup 2026. Genera un piano giornaliero (allocazione 4-4-2) e report
on-demand per partita, integrando quote dei bookmaker e notizie dalle testate.
Comunicazione in italiano, codice in inglese. Vedi `README.md` e `CLAUDE.md`.

## Stato attuale: fondazione completa e testata
- **147 test verdi** (`python -m unittest discover -s tests`), zero dipendenze nel core.
- Implementato: modello Poisson, calibrazione (shrinkage al mercato), value engine
  (edge ≥ 5% o SKIP), allocatore 4-4-2, correlazione, warm-up, risk manager,
  cashout advisor, portafoglio SQLite, backtester (ROI+CLV), collector quote
  (The Odds API + mock), **news engine** (RSS testate → sentiment/infortuni/morale),
  **report on-demand** per partita, API FastAPI (`/piano`, `/report`, `/dashboard`),
  **Telegram** (piano mattutino, `/partita`, pulsanti report, invio stdlib) +
  **GitHub Action** giornaliero, avvio "un click" (`avvia.bat` / `avvia.sh`).

## Roadmap (NON ancora fatto)
Scraper SNAI diretto, ensemble ML (XGBoost/LightGBM) + calibrazione avanzata,
dati squadre reali (xG, ELO), dashboard con grafici (equity curve), update live
durante le partite, migrazione a PostgreSQL, loader dati storici reali per il backtest.

## Stato "operativo" (fatto con l'utente)
- Bot Telegram creato: **@BetMondiale_bot**. chat_id utente: **931898568**.
  (Il token è di @BotFather: NON va messo nel repo; usarlo solo nei Secret.)
- Test di invio Telegram riuscito (via link sendMessage dal telefono).
- L'utente ora ha un **PC Windows**.

## Prossimi passi concordati
1. **Caricare il codice nel repo** `agapasqualino07-eng/Progetto-Word-Cup`
   (con `git push` dal PC; vedi sotto). Finché il repo è vuoto, una nuova
   sessione partirebbe senza file.
2. **Far girare in locale**: doppio click su `avvia.bat` → Dashboard su
   http://127.0.0.1:8000/dashboard
3. (Opzionale) **Automazione Telegram**: Secret su GitHub
   (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID=931898568`, `ODDS_API_KEY`) →
   il workflow invia il piano ogni mattina.
4. (Opzionale) **Deploy su Vercel** per usarlo dal telefono.
5. Poi: scegliere il prossimo modulo della roadmap (consigliato: ensemble ML).

## Caricare il codice su GitHub (dal PC Windows)
Nella cartella `worldcupedge` (barra indirizzo → `cmd` → Invio):
```bat
git init
git add -A
git commit -m "WorldCupEdge"
git branch -M main
git remote add origin https://github.com/agapasqualino07-eng/Progetto-Word-Cup.git
git push -u origin main
```

## Note tecniche per l'assistente che riprende
- Il core deve restare **senza dipendenze esterne** (testabile con sola stdlib).
- Regola anti-allucinazione: mai dati inventati; offline → `DATO MANCANTE`;
  i `mock` sono solo per demo/test ed etichettati.
- Avvio rapido: `python -m unittest discover -s tests`,
  `python -m examples.demo_piano`, `uvicorn src.main:app --reload`.
