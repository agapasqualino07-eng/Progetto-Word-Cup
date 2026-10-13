"""Pulizia testo, redazione dati personali, tokenizzazione IT+EN (solo stdlib)."""

import html
import re
import unicodedata
from html.parser import HTMLParser

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_MENTION_RE = re.compile(r"(?<![\w/])(?:@[\w.]{2,}|/?u/[\w-]{2,})", re.I)
_PHONE_RE = re.compile(r"(?<!\w)\+?\d[\d .\-/]{7,}\d(?!\w)")
_WS_RE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"[a-z0-9]+")


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "code", "pre", "blockquote"):
            # blockquote: spesso cita altri utenti -> non è la voce dell'autore
            self._skip += 1
        elif tag in ("br", "p", "li", "div"):
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "code", "pre", "blockquote") and self._skip:
            self._skip -= 1
        elif tag in ("p", "li", "div"):
            self.parts.append(". ")

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def strip_html(raw):
    if not raw:
        return ""
    if "<" not in raw:
        return html.unescape(raw)
    parser = _TextExtractor()
    try:
        parser.feed(raw)
        parser.close()
    except Exception:  # HTML malformato: meglio vuoto che codice
        return ""
    return "".join(parser.parts)


def redact(text):
    """Rimuove dati personali tipici: email, @utente, u/utente, telefoni, URL."""
    text = _EMAIL_RE.sub("[email]", text)
    text = _URL_RE.sub("[link]", text)
    text = _MENTION_RE.sub("[utente]", text)
    text = _PHONE_RE.sub("[numero]", text)
    return text


def clean_text(raw, max_chars):
    text = unicodedata.normalize("NFKC", strip_html(raw or ""))
    text = redact(text)
    text = _WS_RE.sub(" ", text).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rstrip()
    return text


def fold(text):
    """minuscolo + senza accenti (perché == perche) per il matching."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.replace("’", "'").replace("`", "'")


STOPWORDS = frozenset(
    """
    a ad al allo ai agli all alla alle anche ancora avere avete abbiamo ho hai ha hanno che chi ci con
    come cosa cui da dal dallo dai dagli dalla dalle de del dello dei degli della delle di e ed era
    essere fa fare faccio fatto gli ha ho i il in io la le lei lo loro lui ma me mi mia mio ne nei
    nel nello nella nelle no noi non o od per perche piu poi qua quale quando quanto quello questa
    questo qui se sei si sia siamo sono su sul sulla sui suo sua ti tra tu tua tuo un una uno vi voi
    gia molto tutto tutti tutte ogni sempre mai qualcuno qualcosa sa sapete riesco riuscire modo
    esiste c e' l un' dove compro comprare consigli consigliate odio quando rompe rotto rompono
    prodotto prodotti grazie ciao salve buongiorno aiuto problema problemi
    the a an and are as at be been but by can do does did doing for from has have had how i if in
    into is it its just me my no not of on or our so some than that the their them then there
    these they this to too up us was we were what when where which who why will with you your
    anyone know there's product products keeps keep breaking break hate way thanks help problem
    issue issues any get got really very also would could should one
    """.split()
)

_IT_SUFFIXES = ("amenti", "imenti", "azione", "azioni", "mente", "atore", "atori", "ando", "endo",
                "ata", "ate", "ati", "ato", "ita", "ite", "iti", "ito", "are", "ere", "ire",
                "i", "e", "a", "o")
_EN_SUFFIXES = ("ingly", "ings", "ing", "edly", "ed", "ies", "es", "s")


def stem(token):
    """Stemming leggerissimo (non linguistico): basta per far collidere singolare/plurale."""
    if len(token) <= 4 or token.isdigit():
        return token
    for suf in _IT_SUFFIXES + _EN_SUFFIXES:
        if token.endswith(suf) and len(token) - len(suf) >= 4:
            return token[: -len(suf)]
    return token


def tokenize(text):
    out = []
    for tok in _TOKEN_RE.findall(fold(text)):
        if len(tok) < 3 or tok in STOPWORDS or tok.isdigit():
            continue
        out.append(stem(tok))
    return tuple(out)
