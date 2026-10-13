"""Client HTTP JSON minimale (urllib) usato SOLO dagli adapter reali.

Sicurezza:
- solo HTTPS;
- timeout obbligatorio;
- i messaggi d'errore non includono URL con query, body di risposta o header
  (potrebbero contenere token).
I test iniettano un ``transport`` finto: nessuna chiamata di rete.
"""

import json
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_TIMEOUT = 15.0
MAX_RESPONSE_BYTES = 5 * 1024 * 1024


class ExternalServiceError(RuntimeError):
    pass


def urllib_transport(method, url, headers, body, timeout):
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (https verificato)
            return resp.status, resp.read(MAX_RESPONSE_BYTES)
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ExternalServiceError(f"errore di rete ({type(exc).__name__})") from None


def request_json(
    method,
    url,
    *,
    headers=None,
    payload=None,
    form=None,
    params=None,
    transport=None,
    timeout=DEFAULT_TIMEOUT,
    service="servizio esterno",
):
    if not isinstance(url, str) or not url.startswith("https://"):
        raise ExternalServiceError(f"{service}: solo HTTPS consentito")
    if params:
        sep = "&" if "?" in url else "?"
        url = url + sep + urllib.parse.urlencode(params)
    hdrs = {"Accept": "application/json", "User-Agent": "dropship-mvp/0.1"}
    hdrs.update(headers or {})
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    elif form is not None:
        body = urllib.parse.urlencode(form).encode("utf-8")
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"

    status, raw = (transport or urllib_transport)(method, url, hdrs, body, timeout)
    if status >= 400:
        raise ExternalServiceError(f"{service}: HTTP {status}")
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise ExternalServiceError(f"{service}: risposta non JSON") from None
