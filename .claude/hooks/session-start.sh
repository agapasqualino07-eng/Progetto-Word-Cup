#!/bin/bash
# SessionStart hook per Claude Code sul web.
# Prepara l'ambiente cosi' che test, API e Dashboard siano subito eseguibili.
#
# Nota: il CORE del progetto gira con la sola standard library (i 77 test non
# richiedono nulla). Qui installiamo solo le dipendenze leggere del web server
# (FastAPI/uvicorn/pydantic) da requirements-local.txt. Le librerie ML/scraping
# pesanti (xgboost, lightgbm, spacy, playwright...) sono roadmap non ancora usata
# e vengono volutamente saltate per uno startup veloce e affidabile.
set -euo pipefail

# Esegui solo nell'ambiente remoto (Claude Code sul web).
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

# Dipendenze leggere per far girare API + Dashboard (idempotente).
python -m pip install --quiet -r requirements-local.txt

# Rendi importabile 'src' senza prefissi e per tutta la sessione.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export PYTHONPATH="."' >> "$CLAUDE_ENV_FILE"
fi

echo "Ambiente pronto: requirements-local installati. Test: python -m unittest discover -s tests"
