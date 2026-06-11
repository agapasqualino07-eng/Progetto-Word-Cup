"""Test del formattatore messaggi Telegram."""
import unittest
from datetime import date

from src.data.odds_api import mock_matchday
from src.notifications.message_formatter import format_daily_plan, format_help
from src.notifications.telegram_bot import send_daily_plan
from src.services.pipeline import generate_plan


class TestMessageFormatter(unittest.TestCase):
    def setUp(self):
        self.plan = generate_plan(mock_matchday(), 142.0, date(2026, 6, 16))

    def test_plan_message_has_sections(self):
        msg = format_daily_plan(self.plan, target_bankroll=1000.0)
        self.assertIn("PIANO DI GIOCO", msg)
        self.assertIn("Bankroll: €142.00", msg)
        self.assertIn("VERIFICA SU SNAI", msg)

    def test_help_lists_commands(self):
        self.assertIn("/oggi", format_help())

    def test_send_dry_run_returns_text(self):
        # dry-run: non invia nulla, ritorna il testo formattato.
        text = send_daily_plan(self.plan, dry_run=True)
        self.assertIn("PIANO DI GIOCO", text)


if __name__ == "__main__":
    unittest.main()
