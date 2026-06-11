@echo off
REM Avvio "un click" per Windows: prepara tutto e apre la Dashboard.
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo Python non trovato. Installa Python 3.11+ da https://www.python.org/downloads/
  echo Ricordati di spuntare "Add Python to PATH" durante l'installazione.
  pause
  exit /b 1
)

if not exist .venv ( python -m venv .venv )
call .venv\Scripts\activate
python -m pip install -q --upgrade pip
pip install -q -r requirements-local.txt

start "" http://127.0.0.1:8000/dashboard
echo WorldCupEdge avviato. Apri http://127.0.0.1:8000/dashboard  (chiudi questa finestra per fermare)
uvicorn src.main:app --host 127.0.0.1 --port 8000
