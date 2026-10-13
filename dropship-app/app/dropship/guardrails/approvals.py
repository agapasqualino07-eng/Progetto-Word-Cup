"""Coda di approvazioni umane.

L'automazione può solo CREARE richieste; l'approvazione avviene da un umano
(``python3 -m dropship.cli approve <id> --by <nome>``). Ogni approvazione è
legata a (azione, soggetto) esatti: approvare un budget di 15 non approva 20.
"""

import re
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional

from dropship.storage import read_json, write_json

PUBLISH_PRODUCT = "publish_product"
RAISE_BUDGET = "raise_budget"
ACTIVATE_CAMPAIGN = "activate_campaign"
ACTIONS = {PUBLISH_PRODUCT, RAISE_BUDGET, ACTIVATE_CAMPAIGN}

_APPROVER_RE = re.compile(r"^[\w .'-]{1,64}$", re.UNICODE)


@dataclass
class ApprovalRequest:
    request_id: str
    action: str
    subject: str
    summary: str
    status: str  # PENDING | APPROVED | REJECTED
    created_at: str
    approver: Optional[str] = None
    decided_at: Optional[str] = None


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ApprovalStore:
    def __init__(self, path):
        self.path = path

    def _load(self):
        data = read_json(self.path, [])
        if not isinstance(data, list):
            return []
        out = []
        for item in data:
            try:
                out.append(ApprovalRequest(**item))
            except TypeError:
                continue
        return out

    def _save(self, items):
        write_json(self.path, [asdict(i) for i in items])

    def request(self, action, subject, summary):
        if action not in ACTIONS:
            raise ValueError(f"azione sconosciuta: {action}")
        items = self._load()
        for it in items:
            if it.action == action and it.subject == subject and it.status in ("PENDING", "APPROVED"):
                return it
        req = ApprovalRequest(
            request_id=secrets.token_hex(4),
            action=action,
            subject=str(subject),
            summary=str(summary)[:300],
            status="PENDING",
            created_at=_now(),
        )
        items.append(req)
        self._save(items)
        return req

    def _decide(self, request_id, approver, status):
        name = approver.strip() if isinstance(approver, str) else ""
        if not name or not _APPROVER_RE.match(name):
            raise ValueError("serve il nome di chi approva (max 64 caratteri)")
        items = self._load()
        for it in items:
            if it.request_id == request_id:
                if it.status != "PENDING":
                    raise ValueError(f"richiesta già {it.status}")
                it.status = status
                it.approver = name
                it.decided_at = _now()
                self._save(items)
                return it
        raise KeyError(request_id)

    def approve(self, request_id, approver):
        return self._decide(request_id, approver, "APPROVED")

    def reject(self, request_id, approver):
        return self._decide(request_id, approver, "REJECTED")

    def is_approved(self, action, subject):
        return any(
            it.action == action and it.subject == subject and it.status == "APPROVED"
            for it in self._load()
        )

    def pending(self):
        return [it for it in self._load() if it.status == "PENDING"]
