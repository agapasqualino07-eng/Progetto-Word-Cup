"""Test end-to-end della CLI in modalità mock (nessuna rete, dati in tmpdir)."""

import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from dropship import cli


class TestCliEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.env = {"DROPSHIP_DATA_DIR": str(self.dir)}

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli.main(list(args), environ=dict(self.env))
        return code, buf.getvalue()

    def test_scan_shows_mock_results_and_blocks(self):
        code, out = self.run_cli("scan")
        self.assertEqual(code, 0)
        self.assertIn("MOCK", out)
        self.assertIn("BLOCCATO", out)  # almeno un prodotto vietato nel catalogo mock
        self.assertIn("OK", out)

    def test_full_flow(self):
        code, out = self.run_cli("publish")
        self.assertEqual(code, 0)
        self.assertIn("IN ATTESA DI APPROVAZIONE", out)
        ids = re.findall(r"richiesta ([0-9a-f]{8})", out)
        self.assertTrue(ids)

        # nessuna campagna senza prodotti pubblicati
        code, out = self.run_cli("campaign")
        self.assertIn("Nessun prodotto pubblicato", out)

        for rid in ids:
            code, _ = self.run_cli("approve", rid, "--by", "Mario")
            self.assertEqual(code, 0)

        code, out = self.run_cli("publish")
        self.assertIn("PUBBLICATO", out)
        self.assertTrue((self.dir / "site" / "index.html").exists())
        published = json.loads((self.dir / "published.json").read_text())
        self.assertTrue(published)

        code, out = self.run_cli("campaign", "--budget", "10")
        self.assertEqual(code, 0)
        self.assertIn("PAUSED", out)
        self.assertIn("ROAS break-even", out)

        code, out = self.run_cli("orders")
        self.assertEqual(code, 0)
        self.assertIn("FORWARDED", out)
        self.assertIn("tracking", out.lower())
        self.assertNotIn("@example", out)  # niente PII in output

    def test_kill_switch_blocks_cli_actions(self):
        self.run_cli("kill", "on", "--reason", "test")
        code, out = self.run_cli("publish")
        self.assertNotEqual(code, 0)
        self.assertIn("KILL SWITCH", out)
        self.run_cli("kill", "off")
        code, _ = self.run_cli("publish")
        self.assertEqual(code, 0)

    def test_invalid_budget_rejected(self):
        code, out = self.run_cli("campaign", "--budget", "-5")
        self.assertNotEqual(code, 0)

    def test_status_shows_modes(self):
        code, out = self.run_cli("status")
        self.assertEqual(code, 0)
        self.assertIn("MOCK", out)


if __name__ == "__main__":
    unittest.main()
