"""Servizio ordini: valida, inoltra al fornitore (una sola volta), traccia.

Regole:
- mai acquistare dal fornitore per ordini NON pagati;
- solo SKU pubblicati da noi;
- quantità 1..MAX_QUANTITY (anti-frode / anti-errore);
- indirizzo completo e paese ISO-2;
- idempotenza: lo stesso order_id non viene inoltrato due volte;
- kill switch blocca l'inoltro;
- lo stato su disco NON contiene PII del cliente.
"""

import re
from dataclasses import dataclass
from typing import Optional, Tuple

from dropship.models import SupplierOrder
from dropship.storage import read_json, write_json

MAX_QUANTITY = 10
_COUNTRY_RE = re.compile(r"^[A-Z]{2}$")


@dataclass(frozen=True)
class ForwardResult:
    order_id: str
    status: str  # FORWARDED | DUPLICATE | REJECTED
    reasons: Tuple[str, ...] = ()
    supplier_order: Optional[SupplierOrder] = None


class OrderService:
    def __init__(self, supplier, kill_switch, state_path, known_skus):
        self.supplier = supplier
        self.kill_switch = kill_switch
        self.state_path = state_path
        self.known_skus = set(known_skus)

    def _state(self):
        data = read_json(self.state_path, {})
        return data if isinstance(data, dict) else {}

    def validate(self, order):
        reasons = []
        if not order.paid:
            reasons.append("ordine non pagato: mai acquistare dal fornitore prima dell'incasso")
        if order.sku not in self.known_skus:
            reasons.append("SKU non pubblicato da questo store")
        if not isinstance(order.quantity, int) or not 1 <= order.quantity <= MAX_QUANTITY:
            reasons.append(f"quantità fuori range (1..{MAX_QUANTITY}): verifica manuale")
        c = order.customer
        for field_name in ("name", "address_line", "city", "postal_code"):
            if not str(getattr(c, field_name, "") or "").strip():
                reasons.append(f"indirizzo incompleto: manca {field_name}")
        if not _COUNTRY_RE.match(str(c.country or "")):
            reasons.append("paese non valido (atteso codice ISO a 2 lettere)")
        return reasons

    def forward(self, order):
        self.kill_switch.assert_inactive("inoltro ordine")
        state = self._state()
        if order.order_id in state:
            return ForwardResult(order.order_id, "DUPLICATE", ("ordine già inoltrato",))
        reasons = self.validate(order)
        if reasons:
            return ForwardResult(order.order_id, "REJECTED", tuple(reasons))
        sup = self.supplier.place_order(order)
        state[order.order_id] = {
            "sku": order.sku,
            "quantity": order.quantity,
            "supplier_order_id": sup.supplier_order_id,
            "supplier_status": sup.status,
            "source": sup.source,
        }
        write_json(self.state_path, state)
        return ForwardResult(order.order_id, "FORWARDED", (), sup)

    def tracking(self, order_id):
        entry = self._state().get(order_id)
        if not entry:
            raise KeyError(order_id)
        return self.supplier.get_tracking(entry["supplier_order_id"])
