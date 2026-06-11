"""Test del value engine."""
import unittest

from src.betting.value_engine import (
    bookmaker_margin,
    expected_value,
    has_value,
    implied_prob,
    remove_margin,
)
from src.models.schemas import Outcome, Selection


def _sel(model_prob, odds):
    return Selection("m1", "A", "B", Outcome.HOME, model_prob, odds)


class TestValueEngine(unittest.TestCase):
    def test_implied_prob(self):
        self.assertAlmostEqual(implied_prob(2.0), 0.5)
        self.assertEqual(implied_prob(0), 0.0)

    def test_has_value(self):
        # Modello 60%, quota 2.0 (implicita 50%): edge 10% → valore.
        self.assertTrue(has_value(_sel(0.60, 2.0)))
        # Modello 48%, quota 2.0: edge negativo → niente valore.
        self.assertFalse(has_value(_sel(0.48, 2.0)))

    def test_edge_property(self):
        self.assertAlmostEqual(_sel(0.60, 2.0).edge, 0.10)

    def test_remove_margin_sums_to_one(self):
        fair = remove_margin(2.0, 3.4, 3.6)
        self.assertAlmostEqual(sum(fair.values()), 1.0, places=6)

    def test_bookmaker_margin_positive(self):
        # Quote che implicano overround > 1 → margine positivo.
        self.assertGreater(bookmaker_margin(1.9, 3.4, 3.8), 0.0)

    def test_expected_value_positive_when_edge(self):
        ev = expected_value(_sel(0.60, 2.0), stake=10.0)
        self.assertGreater(ev, 0.0)


if __name__ == "__main__":
    unittest.main()
