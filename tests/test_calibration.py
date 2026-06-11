"""Test della calibrazione (shrinkage verso il mercato)."""
import unittest

from src.ml.calibration import calibrate_1x2, shrink_to_market


class TestCalibration(unittest.TestCase):
    def test_shrink_midpoint(self):
        self.assertAlmostEqual(shrink_to_market(0.8, 0.4, weight=0.5), 0.6)

    def test_shrink_weights_clamped(self):
        self.assertEqual(shrink_to_market(0.8, 0.4, weight=2.0), 0.8)   # w→1
        self.assertEqual(shrink_to_market(0.8, 0.4, weight=-1.0), 0.4)  # w→0

    def test_calibrate_sums_to_one(self):
        model = {"1": 0.7, "X": 0.2, "2": 0.1}
        market = {"1": 0.45, "X": 0.30, "2": 0.25}
        cal = calibrate_1x2(model, market, weight=0.5)
        self.assertAlmostEqual(sum(cal.values()), 1.0, places=6)

    def test_calibration_moves_toward_market(self):
        # Modello sicurissimo sull'1; calibrato deve abbassarsi verso il mercato.
        model = {"1": 0.9, "X": 0.06, "2": 0.04}
        market = {"1": 0.5, "X": 0.27, "2": 0.23}
        cal = calibrate_1x2(model, market, weight=0.5)
        self.assertLess(cal["1"], model["1"])
        self.assertGreater(cal["1"], market["1"])


if __name__ == "__main__":
    unittest.main()
