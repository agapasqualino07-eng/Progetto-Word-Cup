import unittest

from dropship.http import ExternalServiceError, request_json
from tests.helpers import FakeTransport


class TestRequestJson(unittest.TestCase):
    def test_rejects_plain_http(self):
        with self.assertRaises(ExternalServiceError):
            request_json("GET", "http://example.com/x", transport=FakeTransport())

    def test_sends_json_payload_and_parses_response(self):
        t = FakeTransport([(200, {"ok": True})])
        out = request_json(
            "POST",
            "https://api.example.com/x",
            headers={"X-Token": "abc"},
            payload={"a": 1},
            transport=t,
        )
        self.assertEqual(out, {"ok": True})
        self.assertEqual(t.json_body(), {"a": 1})
        self.assertEqual(t.calls[0]["headers"]["Content-Type"], "application/json")
        self.assertEqual(t.calls[0]["headers"]["X-Token"], "abc")

    def test_http_error_does_not_leak_url_query_or_body(self):
        t = FakeTransport([(401, b'{"error":"bad token sk-secret"}')])
        with self.assertRaises(ExternalServiceError) as ctx:
            request_json(
                "GET",
                "https://api.example.com/x?access_token=SEGRETO",
                transport=t,
                service="Esempio",
            )
        msg = str(ctx.exception)
        self.assertIn("401", msg)
        self.assertNotIn("SEGRETO", msg)
        self.assertNotIn("sk-secret", msg)

    def test_redirect_status_is_an_error(self):
        t = FakeTransport([(302, b"")])
        with self.assertRaises(ExternalServiceError):
            request_json("GET", "https://api.example.com/x", transport=t)

    def test_default_opener_does_not_follow_redirects(self):
        # i redirect inoltrerebbero gli header con i token a un altro host
        import urllib.request

        from dropship.http import _NoRedirect

        handler = _NoRedirect()
        req = urllib.request.Request("https://api.example.com/x", headers={"X-Shopify-Access-Token": "t"})
        self.assertIsNone(handler.redirect_request(req, None, 302, "Found", {}, "https://evil.example/"))

    def test_invalid_json_raises(self):
        t = FakeTransport([(200, b"not json")])
        with self.assertRaises(ExternalServiceError):
            request_json("GET", "https://api.example.com/x", transport=t)

    def test_query_params_are_encoded(self):
        t = FakeTransport([(200, {})])
        request_json(
            "GET",
            "https://api.example.com/x",
            params={"q": "a b&c=d"},
            transport=t,
        )
        self.assertIn("q=a+b%26c%3Dd", t.calls[0]["url"])


if __name__ == "__main__":
    unittest.main()
