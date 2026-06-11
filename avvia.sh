#!/usr/bin/env bash
# Avvio "un click" per Mac/Linux: prepara tutto e apre la Dashboard.
set -e
cd "$(dirname "$0")"

PY="$(command -v python3 || command -v python)"
if [ -z "$PY" ]; then
  echo "Python non trovato. Installa Python 3.11+ da https://www.python.org/downloads/"
  exit 1
fi

# Ambiente virtuale + dipendenze minime.
[ -d .venv ] || "$PY" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements-local.txt

# Apri il browser sulla Dashboard appena il server è su.
( sleep 2
  if command -v open >/dev/null;     then open http://127.0.0.1:8000/dashboard
  elif command -v xdg-open >/dev/null; then xdg-open http://127.0.0.1:8000/dashboard
  fi ) >/dev/null 2>&1 &

echo "WorldCupEdge avviato → http://127.0.0.1:8000/dashboard  (Ctrl+C per fermare)"
exec uvicorn src.main:app --host 127.0.0.1 --port 8000
