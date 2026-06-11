"""Test del risk manager (adaptive confidence + clamp)."""
import unittest

from src.betting.risk_manager import AdaptiveConfidence, clamp_stake


class TestRiskManager(unittest.TestCase):
    def test_clamp_floor_and_cap(self):
        self.assertEqual(clamp_stake(2.0), 5.0)
        self.assertEqual(clamp_stake(100.0), 20.0)
        self.assertEqual(clamp_stake(12.5), 12.5)

    def test_reduces_after_three_losses(self):
        ac = AdaptiveConfidence()
        for _ in range(3):
            ac.update(won=False)
        self.assertEqual(ac.factor, 0.5)
        self.assertEqual(ac.adjusted_stake(10.0), 5.0)

    def test_strong_reduction_after_five_losses(self):
        ac = AdaptiveConfidence()
        for _ in range(5):
            ac.update(won=False)
        self.assertEqual(ac.factor, 0.25)

    def test_scales_up_after_three_wins(self):
        ac = AdaptiveConfidence()
        for _ in range(3):
            ac.update(won=True)
        self.assertGreater(ac.factor, 1.0)
        self.assertLessEqual(ac.factor, 1.2)

    def test_win_resets_negative_streak(self):
        ac = AdaptiveConfidence()
        ac.update(won=False)
        ac.update(won=False)
        ac.update(won=True)  # interrompe la striscia negativa
        self.assertEqual(ac.streak, 1)


if __name__ == "__main__":
    unittest.main()
