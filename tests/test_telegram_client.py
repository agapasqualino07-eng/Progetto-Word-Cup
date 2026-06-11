"""Test del client Telegram stdlib (costruzione payload, niente rete)."""
import unittest

from src.notifications.telegram_client import (
    CONFIRM_BUTTONS,
    build_send_payload,
    get_chat_id_hint,
    send_message,
)


class TestTelegramClient(unittest.TestCase):
    def test_payload_basic(self):
        p = build_send_payload("123", "ciao")
        self.assertEqual(p["chat_id"], "123")
        self.assertEqual(p["text"], "ciao")
        self.assertNotIn("reply_markup", p)

    def test_payload_with_buttons(self):
        p = build_send_payload("123", "ciao", CONFIRM_BUTTONS)
        kb = p["reply_markup"]["inline_keyboard"]
        self.assertEqual(len(kb), len(CONFIRM_BUTTONS))
        self.assertEqual(kb[0][0]["callback_data"], "confirm_all")

    def test_send_requires_credentials(self):
        with self.assertRaises(RuntimeError):
            send_message("", "123", "ciao")
        with self.assertRaises(RuntimeError):
            send_message("tok", "", "ciao")

    def test_chat_id_hint_url(self):
        self.assertIn("getUpdates", get_chat_id_hint("TOK"))


if __name__ == "__main__":
    unittest.main()
