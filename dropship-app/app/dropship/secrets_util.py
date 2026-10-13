"""Wrapper per segreti: impedisce che una chiave finisca in log, repr o eccezioni."""


class Secret:
    __slots__ = ("_value",)

    def __init__(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Segreto vuoto o non valido")
        self._value = value.strip()

    def reveal(self):
        """Restituisce il valore in chiaro: usare SOLO per costruire header di richiesta."""
        return self._value

    def __repr__(self):
        return "Secret('***')"

    __str__ = __repr__

    def __format__(self, spec):
        return "***"

    def __eq__(self, other):
        return isinstance(other, Secret) and other._value == self._value

    def __hash__(self):
        return hash(("Secret", self._value))
