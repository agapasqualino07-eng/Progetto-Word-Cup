"""Kill switch: blocca TUTTE le azioni che spendono o pubblicano.

Attivabile in due modi:
- file ``<data_dir>/KILL_SWITCH`` (``dropship.cli kill on|off``);
- variabile d'ambiente ``DROPSHIP_KILL_SWITCH=1`` (non disattivabile da CLI:
  serve rimuoverla dall'ambiente).
"""

from datetime import datetime, timezone
from pathlib import Path

from dropship.config import is_truthy
from dropship.guardrails.errors import KillSwitchActive

ENV_VAR = "DROPSHIP_KILL_SWITCH"
FILE_NAME = "KILL_SWITCH"


class KillSwitch:
    def __init__(self, data_dir, environ):
        self.path = Path(data_dir) / FILE_NAME
        self._env = environ

    def is_active(self):
        return is_truthy(self._env.get(ENV_VAR)) or self.path.exists()

    def reason(self):
        if is_truthy(self._env.get(ENV_VAR)):
            return f"variabile {ENV_VAR} attiva"
        if self.path.exists():
            return self.path.read_text(encoding="utf-8").strip() or "file KILL_SWITCH presente"
        return ""

    def activate(self, reason):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.path.write_text(f"{stamp} {reason}".strip()[:500], encoding="utf-8")

    def deactivate(self):
        if self.path.exists():
            self.path.unlink()

    def assert_inactive(self, action):
        if self.is_active():
            raise KillSwitchActive(f"KILL SWITCH attivo: azione '{action}' bloccata ({self.reason()})")
