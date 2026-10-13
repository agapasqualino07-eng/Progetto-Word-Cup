import tests  # noqa: F401  (attiva la guardia anti-rete)
import os
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from dropship.config import ConfigError, load_dotenv, load_settings, parse_dotenv
from dropship.secrets_util import Secret


class TestSettings(unittest.TestCase):
    def test_defaults_without_env(self):
        s = load_settings({})
        self.assertEqual(s.pricing.vat_rate, Decimal("0.22"))
        self.assertEqual(s.pricing.min_margin, Decimal("0.30"))
        self.assertEqual(s.campaigns.daily_spend_cap, Decimal("50"))
        self.assertAlmostEqual(s.thresholds.min_demand_growth, 0.20)
        self.assertFalse(s.force_mock)

    def test_thresholds_are_configurable_from_env(self):
        s = load_settings(
            {
                "DROPSHIP_MIN_DEMAND_GROWTH": "0.5",
                "DROPSHIP_MAX_AD_SATURATION": "0.4",
                "DROPSHIP_MIN_TREND_SCORE": "70",
                "DROPSHIP_DAILY_SPEND_CAP": "100",
                "DROPSHIP_VAT_RATE": "0.10",
            }
        )
        self.assertAlmostEqual(s.thresholds.min_demand_growth, 0.5)
        self.assertAlmostEqual(s.thresholds.max_ad_saturation, 0.4)
        self.assertAlmostEqual(s.thresholds.min_score, 70.0)
        self.assertEqual(s.campaigns.daily_spend_cap, Decimal("100"))
        self.assertEqual(s.pricing.vat_rate, Decimal("0.10"))

    def test_invalid_number_rejected(self):
        with self.assertRaises(ConfigError):
            load_settings({"DROPSHIP_VAT_RATE": "abc"})

    def test_out_of_range_rate_rejected(self):
        with self.assertRaises(ConfigError):
            load_settings({"DROPSHIP_MIN_MARGIN": "1.5"})

    def test_negative_cap_rejected(self):
        with self.assertRaises(ConfigError):
            load_settings({"DROPSHIP_DAILY_SPEND_CAP": "-1"})

    def test_campaign_budget_cannot_exceed_daily_cap(self):
        with self.assertRaises(ConfigError):
            load_settings(
                {"DROPSHIP_DAILY_SPEND_CAP": "10", "DROPSHIP_MAX_CAMPAIGN_BUDGET": "20"}
            )

    def test_force_mock_flag(self):
        self.assertTrue(load_settings({"DROPSHIP_FORCE_MOCK": "1"}).force_mock)


class TestDotenv(unittest.TestCase):
    def test_parse_ignores_comments_and_quotes(self):
        text = '# commento\nA=1\nB="due"\n\nexport C=\'tre\'\nmalformata\n'
        self.assertEqual(parse_dotenv(text), {"A": "1", "B": "due", "C": "tre"})

    def test_load_does_not_override_existing_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("KEY=dal_file\nNEW=nuovo\n")
            env = {"KEY": "da_ambiente"}
            load_dotenv(path, env)
            self.assertEqual(env["KEY"], "da_ambiente")
            self.assertEqual(env["NEW"], "nuovo")

    def test_missing_dotenv_is_noop(self):
        env = {}
        load_dotenv(Path("/nonexistent/.env"), env)
        self.assertEqual(env, {})


class TestSecret(unittest.TestCase):
    def test_secret_is_redacted_in_repr_and_str(self):
        s = Secret("sk-super-segreta")
        self.assertNotIn("sk-super-segreta", repr(s))
        self.assertNotIn("sk-super-segreta", str(s))
        self.assertNotIn("sk-super-segreta", f"{s}")
        self.assertEqual(s.reveal(), "sk-super-segreta")

    def test_empty_secret_rejected(self):
        with self.assertRaises(ValueError):
            Secret("")


class TestNoHardcodedSecrets(unittest.TestCase):
    """Security review: nessuna chiave nel codice sorgente."""

    def test_source_has_no_key_like_literals(self):
        import re

        root = Path(__file__).resolve().parent.parent / "dropship"
        pattern = re.compile(
            r"(sk-ant-[A-Za-z0-9]|shpat_[a-f0-9]{8}|EAA[A-Za-z0-9]{20}|AKIA[0-9A-Z]{16})"
        )
        offenders = [
            str(p)
            for p in root.rglob("*.py")
            if pattern.search(p.read_text(encoding="utf-8"))
        ]
        self.assertEqual(offenders, [])

    def test_gitignore_excludes_env(self):
        gi = Path(__file__).resolve().parent.parent / ".gitignore"
        lines = gi.read_text().splitlines()
        self.assertIn(".env", lines)


if __name__ == "__main__":
    unittest.main()
