# Cartella dati REALI (privata)

Qui va il file con le **partite storiche vere** per il backtest:

    data/raw/history.csv

## Come crearlo (3 passi)
1. Copia il template che trovi in `data/history_template.csv`.
2. Rinominalo in `history.csv` e mettilo **in questa cartella** (`data/raw/`).
3. Riempilo con partite reali (Mondiale 2022, Euro 2024…), quote di apertura
   e chiusura incluse. Una partita per riga.

Poi lancia il backtest:

    python -m src.backtest.backtester

## Regole
- ⚠️ Inserisci solo dati **verificati**: niente quote o risultati inventati.
- Il file `history.csv` **non viene caricato su GitHub** (resta solo sul tuo PC):
  è giusto così, sono dati tuoi. Solo questo README è versionato, per ricordarti
  dove va il file.
- Senza questo file il backtester usa dati di esempio (sintetici) e lo dice:
  quel risultato **non è indicativo**.
