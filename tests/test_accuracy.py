"""Test del backtest di accuratezza (metriche su risultati reali)."""
import unittest
from pathlib import Path

from src.backtest.accuracy import (
    DEFAULT_RESULTS_PATH,
    RealMatch,
    evaluate_accuracy,
    load_results,
)
from src.ml.poisson_model import PoissonModel
from src.ml.ratings_loader import load_ratings_model


class TestMetrics(unittest.TestCase):
    def test_perfect_model_has_zero_error(self):
        # Modello che dà tutto all'esito giusto → Brier e log-loss ~0, hit 100%.
        class Perfect(PoissonModel):
            def predict_match(self, home, away, venue_country=None):
                from src.ml.poisson_model import MatchProbabilities
                return MatchProbabilities(1.0, 0.0, 0.0, 0.5, 0.5, 1.0, 0.1)
        matches = [RealMatch("2024", "A", "B", "1", True),
                   RealMatch("2024", "C", "D", "1", True)]
        res = evaluate_accuracy(Perfect(), matches)
        self.assertEqual(res.hit_rate, 1.0)
        self.assertAlmostEqual(res.brier, 0.0, places=6)
        self.assertAlmostEqual(res.log_loss, 0.0, places=4)

    def test_metrics_bounded(self):
        matches = [RealMatch("2024", "Brasile", "Haiti", "1", False),
                   RealMatch("2024", "Haiti", "Brasile", "2", False)]
        res = evaluate_accuracy(PoissonModel(), matches)
        self.assertTrue(0.0 <= res.hit_rate <= 1.0)
        self.assertGreater(res.brier, 0.0)


class TestRealDataset(unittest.TestCase):
    """Usa il dataset reale committato, se presente."""

    def setUp(self):
        if not Path(DEFAULT_RESULTS_PATH).exists():
            self.skipTest("dataset risultati reali assente")
        self.matches = load_results()

    def test_dataset_nonempty_and_valid(self):
        self.assertGreater(len(self.matches), 50)
        self.assertTrue(all(m.actual in {"1", "X", "2"} for m in self.matches))

    def test_ratings_not_worse_than_tiers(self):
        # Sui dati reali i rating FIFA non devono peggiorare il Brier rispetto
        # al modello a fasce (atteso: lo migliorano).
        ratings = load_ratings_model()
        if ratings is None:
            self.skipTest("file rating assente")
        tier = evaluate_accuracy(PoissonModel(), self.matches)
        real = evaluate_accuracy(ratings, self.matches)
        self.assertLessEqual(real.brier, tier.brier + 1e-9)


if __name__ == "__main__":
    unittest.main()
