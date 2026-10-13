"""Guardrail: regole che impediscono all'automazione di fare danni.

- conformità prodotto (vietati / regolati / marchi) e testi (claims ingannevoli);
- cap di spesa giornaliero e per campagna;
- approvazione umana obbligatoria (pubblicazione, attivazione campagna, aumento budget);
- kill switch globale.
"""

from dropship.guardrails.approvals import ApprovalStore
from dropship.guardrails.compliance import ComplianceResult, check_copy, check_product
from dropship.guardrails.errors import GuardrailViolation, KillSwitchActive, SpendCapExceeded
from dropship.guardrails.killswitch import KillSwitch
from dropship.guardrails.spend import SpendGuard

__all__ = [
    "ApprovalStore",
    "ComplianceResult",
    "GuardrailViolation",
    "KillSwitch",
    "KillSwitchActive",
    "SpendCapExceeded",
    "SpendGuard",
    "check_copy",
    "check_product",
]
