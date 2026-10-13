"""Estrazione di frasi-problema da post (pattern IT+EN), normalizzazione, deduplica.

Le euristiche sono lessicali e dichiarate: non "capiscono" il testo. Servono a
filtrare e ordinare, la decisione finale resta umana (vedi docs/06).
"""

import difflib
import re

from dropship.problems.models import ProblemMention
from dropship.problems.text import fold, tokenize

# (nome, regex su testo "fold"-ato: minuscolo, senza accenti)
PROBLEM_PATTERNS = (
    # italiano
    ("it:non_riesco", r"\bnon riesco a\b|\bnon riesco piu\b"),
    ("it:come_faccio", r"\bcome (?:faccio|posso|si fa) (?:a|per)\b"),
    ("it:qualcuno_sa", r"\bqualcuno (?:sa|conosce|ha (?:provato|trovato|risolto))\b"),
    ("it:odio_quando", r"\bodio quando\b|\bodio che\b"),
    ("it:si_rompe", r"\bsi (?:rompe|rompono|stacca|staccano|sporca|rovina|rovinano|blocca|bloccano)"
                    r" (?:sempre|di continuo|ogni volta|dopo)\b|\bsi (?:rompe|rompono) sempre\b"),
    ("it:ce_un_modo", r"\bc'?e un modo (?:per|di)\b|\besiste (?:qualcosa|un modo|un prodotto|un oggetto)\b"),
    ("it:non_funziona", r"\bnon funziona(?:no)? (?:piu|bene|mai)\b"),
    ("it:non_ne_posso", r"\bnon ne posso piu\b|\bsono stuf[oa]\b|\bmi fa impazzire\b"),
    ("it:perde_sempre", r"\b(?:perde|perdono|cade|cadono|scivola|scivolano) (?:sempre|di continuo)\b"),
    ("it:aiuto", r"\b(?:help|aiuto)[,! ]+(?:come|non)\b"),
    ("it:si_aggrovigliano", r"\bsi aggroviglia(?:no)?\b|\bsi incastra(?:no)?\b"),
    # inglese
    ("en:how_do_i", r"\bhow (?:do|can|should) (?:i|you|we) (?:stop|keep|fix|prevent|get|organi[sz]e|clean|store)\b"),
    ("en:is_there_product", r"\bis there (?:a|any) (?:product|tool|device|gadget|way|thing)\b"),
    ("en:keeps_breaking", r"\bkeeps? (?:breaking|falling|slipping|leaking|tangling|getting)\b"),
    ("en:i_hate_when", r"\bi hate (?:when|it when|how)\b"),
    ("en:cant_find", r"\bi can'?t (?:find|get|seem to|stop)\b"),
    ("en:struggling", r"\b(?:struggling|struggle) (?:with|to)\b"),
    ("en:anyone_know", r"\b(?:does )?anyone (?:know|have|recommend)\b"),
    ("en:annoying", r"\bso annoying\b|\bdrives me (?:crazy|nuts)\b"),
)

PURCHASE_PATTERNS = (
    r"\bdove (?:lo|la|li|le)? ?(?:compro|trovo|posso comprare|posso trovare|acquist)",
    r"\bconsigli(?:ate|ati)? (?:un |una |qualche )?(?:prodott|acquist|oggett|marca|modell)",
    r"\bconsigli prodotto\b",
    r"\bche (?:prodotto|marca|modello) (?:mi )?(?:consigli|compr|prend)",
    r"\bquale (?:comprare|prendere|mi consigliate)\b",
    r"\bvale la pena (?:comprar|prender)",
    r"\bcosa (?:mi )?(?:consigliate|compro)\b",
    r"\bqualcuno (?:sa|conosce) (?:un|una|qualche)\b",
    r"\bis there (?:a|any) (?:product|tool|device|gadget)\b",
    r"\bwhere (?:can|do|should) i (?:buy|get|find)\b",
    r"\b(?:any|product) recommendations?\b",
    r"\b(?:can you|would you|anyone) recommend\b",
    r"\bwhat (?:should|do you) (?:i )?(?:buy|use|recommend)\b",
    r"\bworth (?:buying|it)\b",
)

INTENSITY_WORDS = (
    "odio", "frustrant", "disperat", "impazzire", "impazzisco", "stufo", "stufa", "non ne posso",
    "incubo", "urgente", "aiuto", "ogni volta", "ogni giorno", "sempre", "di continuo", "terribile",
    "pessim", "schifo", "esasperat",
    "hate", "frustrat", "desperate", "nightmare", "urgent", "every time", "every day", "always",
    "constantly", "terrible", "awful", "annoying", "drives me", "fed up", "sick of",
)

# Indizi che la soluzione è un OGGETTO FISICO spedibile (casa, cucina, auto, animali, viaggio...).
PHYSICAL_HINTS = (
    "cavi", "cavo", "organizer", "organizzator", "supporto", "porta", "contenitor", "scatol", "borraccia",
    "bottiglia", "cuscin", "lampad", "luce", "gancio", "ganci", "tappetin", "custodia", "cover",
    "spazzol", "filtro", "ventilator", "umidificator", "deumidific", "zaino", "borsa", "valigia",
    "scarpe", "calz", "guant", "pentol", "padella", "coltell", "tagliere", "frigo", "armadio",
    "cassett", "mensol", "scrivania", "sedia", "letto", "materasso", "piumino", "lenzuol", "asciugaman",
    "doccia", "lavandino", "scarico", "rubinett", "caricabatter", "cuffie", "auricolar", "telecomando",
    "guinzaglio", "cuccia", "lettiera", "ciotola", "giocattol", "passeggino", "seggiolin", "biberon",
    "pianta", "piante", "vaso", "vasi", "giardin", "auto", "bici", "casco", "ombrell", "occhiali", "orologio", "polvere",
    "peli", "muffa", "zanzar", "odore", "condensa", "umidita",
    "cable", "cord", "holder", "stand", "mount", "rack", "shelf", "drawer", "box", "bottle", "pillow",
    "lamp", "light", "hook", "mat", "case", "brush", "filter", "fan", "humidifier", "backpack", "bag",
    "shoe", "sock", "glove", "pan", "knife", "fridge", "closet", "desk", "chair", "bed", "mattress",
    "towel", "shower", "sink", "drain", "charger", "headphone", "earbud", "remote", "leash", "litter",
    "bowl", "toy", "stroller", "plant", "garden", "car", "bike", "helmet", "umbrella", "glasses",
    "dust", "pet hair", "mold", "mosquito", "smell", "tangl",
)

# Indizi che il problema NON si risolve con un prodotto fisico (software, burocrazia, servizi)
# o che il prodotto sarebbe vietato/rischioso (farmaci, dispositivi medici).
NON_PHYSICAL_HINTS = (
    "app", "software", "login", "password", "account", "email", "sito", "website", "bug", "codice",
    "code", "server", "api", "excel", "windows", "android", "iphone update", "aggiornamento",
    "contratto", "bolletta", "abbonamento", "banca", "bank", "assicurazion", "insurance", "tasse",
    "tax", "visto", "visa", "avvocat", "lawyer", "spid", "inps", "isee", "mutuo", "lavoro", "job",
    "farmac", "medicin", "diagnos", "terapia", "prescri", "drug", "dosage",
)

_SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+|\s+\.\s+|\n+")
_COMPILED = tuple((n, re.compile(p)) for n, p in PROBLEM_PATTERNS)
_PURCHASE = tuple(re.compile(p) for p in PURCHASE_PATTERNS)


def _has(text, needle):
    """Prefisso di parola; le voci corte (<= 4 lettere) devono essere parola intera
    (con plurale inglese opzionale), così "app" non scatta su "appena"."""
    esc = re.escape(needle)
    if len(needle) <= 4:
        return re.search(rf"(?<![a-z]){esc}(?:s|es)?(?![a-z])", text) is not None
    return re.search(rf"(?<![a-z]){esc}", text) is not None


def intensity_score(folded):
    hits = sum(1 for w in INTENSITY_WORDS if _has(folded, w))
    bangs = min(folded.count("!"), 3)
    return min(1.0, 0.25 * hits + 0.1 * bangs)


def purchase_intent(folded):
    return any(p.search(folded) for p in _PURCHASE)


def physical_score(folded):
    pos = sum(1 for w in PHYSICAL_HINTS if _has(folded, w))
    neg = sum(1 for w in NON_PHYSICAL_HINTS if _has(folded, w))
    if pos == 0:
        return 0.0
    return max(0.0, min(1.0, 0.4 + 0.2 * pos - 0.35 * neg))


def split_sentences(text):
    return [s.strip(" .") for s in _SENT_SPLIT.split(text) if s and len(s.strip(" .")) >= 12]


def extract_mentions(post):
    """Una ``ProblemMention`` per frase che contiene un pattern-problema.

    Il contesto (intenzione d'acquisto, oggetto fisico) è valutato sul post
    intero, perché spesso "dove lo compro?" sta nella frase successiva.
    """
    folded_post = fold(post.text)
    intent_post = purchase_intent(folded_post)
    phys_post = physical_score(folded_post)
    out = []
    for sentence in split_sentences(post.text):
        folded = fold(sentence)
        matched = tuple(name for name, rx in _COMPILED if rx.search(folded))
        if not matched:
            continue
        toks = tokenize(sentence)
        if not toks:
            continue
        out.append(ProblemMention(
            post=post,
            sentence=sentence,
            patterns=matched,
            intensity=max(intensity_score(folded), intensity_score(folded_post) * 0.5),
            purchase_intent=intent_post,
            physical=max(physical_score(folded), phys_post * 0.8),
            tokens=toks,
        ))
    return out


_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_sentence(sentence):
    return _NON_ALNUM.sub(" ", fold(sentence)).strip()


def dedupe(mentions, near_ratio=0.95, near_min_len=40):
    """Rimuove copie (crosspost, citazioni, stesso post visto da due query).

    - stessa URL + stessa frase -> duplicato;
    - stesso testo normalizzato (o quasi identico, ratio >= 0.95 su frasi lunghe)
      -> duplicato anche su fonti diverse: un copia-incolla NON è una fonte indipendente.
    Persone diverse che descrivono lo stesso problema con parole simili NON sono
    duplicati: è proprio il segnale che cerchiamo (lo raggruppa il clustering).
    Si tiene la menzione più vecchia (data nota prima).
    """
    def key(m):
        dt = m.post.created_at
        return (dt is None, dt.timestamp() if dt else 0.0, m.post.url)

    kept, seen = [], set()
    long_kept = []
    for m in sorted(mentions, key=key):
        norm = normalize_sentence(m.sentence)
        if norm in seen:
            continue
        if len(norm) >= near_min_len and any(
                difflib.SequenceMatcher(None, norm, other).ratio() >= near_ratio for other in long_kept):
            continue
        seen.add(norm)
        if len(norm) >= near_min_len:
            long_kept.append(norm)
        kept.append(m)
    return kept
