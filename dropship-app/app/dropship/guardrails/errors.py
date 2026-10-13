class GuardrailViolation(RuntimeError):
    """Base per ogni blocco imposto dai guardrail."""


class KillSwitchActive(GuardrailViolation):
    pass


class SpendCapExceeded(GuardrailViolation):
    pass
