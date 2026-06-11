"""Test dell'ensemble: feature, fallback senza ML, addestramento se disponibile."""
import unittest

from src.backtest.sample_data import sample_history
from src.ml.ensemble import (
    EnsembleModel,
    match_features,
    sklearn_available,
    train_ensemble,
)


class TestFeatures(unittest.TestCase):
    def test_match_features_shape(self):
        mp = {"1": 0.5, "X": 0.3, "2": 0.2}
        mk = {"1": 0.45, "X": 0.30, "2": 0.25}
        feats = match_features(mp, mk)
        self.assertEqual(len(feats), 6)
        self.assertEqual(feats[0], 0.5)


class TestFallback(unittest.TestCase):
    def test_untrained_returns_normalised_probs(self):
        # Senza classificatore → Poisson calibrato sul mercato.
        model = EnsembleModel()  # clf=None
        self.assertFalse(model.trained)
        p = model.predict_1x2("Brasile", "Haiti", 1.5, 4.0, 7.0)
        self.assertEqual(set(p), {"1", "X", "2"})
        self.assertAlmostEqual(sum(p.values()), 1.0, places=6)

    def test_train_requires_history(self):
        with self.assertRaises(RuntimeError):
            train_ensemble([])


@unittest.skipUnless(sklearn_available(), "scikit-learn non installato")
class TestTrainingWhenAvailable(unittest.TestCase):
    def test_trains_and_predicts(self):
        model = train_ensemble(sample_history())
        self.assertTrue(model.trained)
        p = model.predict_1x2("Francia", "Marocco", 1.7, 3.6, 5.0)
        self.assertAlmostEqual(sum(p.values()), 1.0, places=6)
        self.assertTrue(all(0.0 <= v <= 1.0 for v in p.values()))


if __name__ == "__main__":
    unittest.main()
