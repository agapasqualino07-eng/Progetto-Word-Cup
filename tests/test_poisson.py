"""Test del modello Poisson."""
import unittest

from src.ml.poisson_model import PoissonModel, poisson_pmf


class TestPoisson(unittest.TestCase):
    def test_pmf_sums_to_one(self):
        total = sum(poisson_pmf(k, 1.5) for k in range(30))
        self.assertAlmostEqual(total, 1.0, places=6)

    def test_pmf_zero_lambda(self):
        self.assertEqual(poisson_pmf(0, 0.0), 1.0)
        self.assertEqual(poisson_pmf(1, 0.0), 0.0)

    def test_probabilities_sum_to_one(self):
        probs = PoissonModel().predict_match("Francia", "Senegal", "USA")
        s = probs.prob_1 + probs.prob_x + probs.prob_2
        self.assertAlmostEqual(s, 1.0, places=6)

    def test_favorite_more_likely(self):
        # Tier 1 vs Tier 4: la favorita deve avere prob_1 nettamente maggiore.
        probs = PoissonModel().predict_match("Argentina", "Curaçao")
        self.assertGreater(probs.prob_1, probs.prob_2)
        self.assertGreater(probs.prob_1, 0.5)

    def test_host_advantage_increases_home_lambda(self):
        model = PoissonModel()
        with_host = model.expected_goals("USA", "Paraguay", "USA")[0]
        without = model.expected_goals("USA", "Paraguay", "Brasile")[0]
        self.assertGreater(with_host, without)

    def test_over_under_complementary(self):
        probs = PoissonModel().predict_match("Brasile", "Scozia")
        self.assertAlmostEqual(probs.over_2_5 + probs.under_2_5, 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
