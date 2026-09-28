"""Text helpers: normalising titles, tokenising keywords, parsing Amazon values."""

import re
import unicodedata
from datetime import date, datetime

STOPWORDS = {
    "a", "an", "and", "the", "of", "for", "to", "in", "on", "with", "your", "you",
    "my", "our", "by", "from", "at", "is", "it", "this", "that", "book", "books",
    "edition", "volume", "vol", "paperback", "hardcover", "kindle", "vs", "or",
}


def normalize(text):
    """Lowercase, strip accents and punctuation, collapse whitespace."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("'", "").replace("’", "")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def stem(word):
    """Very light English stemmer: enough to match journal/journals, diaries/diary."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith(("ches", "shes", "sses", "xes", "zes")):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def tokens(text):
    """Content tokens (stemmed, stopwords removed)."""
    return [stem(w) for w in normalize(text).split() if w not in STOPWORDS]


def token_coverage(keyword, text):
    """Share of the keyword's content tokens that appear in text (0..1)."""
    kw = set(tokens(keyword))
    if not kw:
        return 0.0
    return len(kw & set(tokens(text))) / len(kw)


# ---------------------------------------------------------------- value parsers

def parse_int(value):
    """'#12,345' / 'Nr. 12.345' / '1,234 ratings' -> 12345 / 12345 / 1234."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    m = re.search(r"\d[\d,.\s  ]*", str(value))
    if not m:
        return None
    digits = re.sub(r"\D", "", m.group(0))
    return int(digits) if digits else None


_CURRENCIES = [("CDN$", "CAD"), ("CA$", "CAD"), ("C$", "CAD"), ("AU$", "AUD"), ("A$", "AUD"),
               ("US$", "USD"), ("USD", "USD"), ("EUR", "EUR"), ("\u20ac", "EUR"), ("GBP", "GBP"),
               ("\u00a3", "GBP"), ("CAD", "CAD"), ("AUD", "AUD")]


def parse_currency(value):
    """'EUR 12.79' -> 'EUR', '\u00a37.99' -> 'GBP'; a bare '$' returns None (the store's own currency)."""
    text = str(value or "")
    for mark, code in _CURRENCIES:
        if mark in text:
            return code
    return None


def parse_float(value):
    """'$8.99' / '8,99 €' / '4.6 out of 5 stars' -> 8.99 / 8.99 / 4.6."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = re.search(r"\d+(?:[.,\s ]\d{3})*(?:[.,]\d{1,2})?", str(value))
    if not m:
        return None
    num = re.sub(r"[\s ]", "", m.group(0))
    if re.search(r",\d{1,2}$", num):          # European decimal comma
        num = num.replace(".", "").replace(",", ".")
    else:
        num = num.replace(",", "")
    try:
        return float(num)
    except ValueError:
        return None


_MONTHS = {
    # English
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
    # German
    "januar": 1, "februar": 2, "marz": 3, "mai": 5, "juni": 6, "juli": 7,
    "okt": 10, "oktober": 10, "dez": 12, "dezember": 12,
    # French / Spanish / Italian (common forms)
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "juin": 6, "juillet": 7,
    "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12,
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11,
    "diciembre": 12, "gennaio": 1, "febbraio": 2, "aprile": 4, "maggio": 5,
    "giugno": 6, "luglio": 7, "settembre": 9, "ottobre": 10, "dicembre": 12,
}


def _month(word):
    word = normalize(word)
    if word in _MONTHS:
        return _MONTHS[word]
    for length in (4, 3):
        if word[:length] in _MONTHS:
            return _MONTHS[word[:length]]
    return None


def parse_date(value):
    """Parse the date formats Amazon product pages use; returns ISO string or None."""
    if not value:
        return None
    s = str(value).strip()
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return m.group(0)
    norm = normalize(s)
    # "march 3 2024"
    m = re.search(r"([a-z]+) (\d{1,2}) (\d{4})", norm)
    if m and _month(m.group(1)):
        return _iso(int(m.group(3)), _month(m.group(1)), int(m.group(2)))
    # "3 march 2024" / "3 marz 2024"
    m = re.search(r"(\d{1,2}) (?:de )?([a-z]+) (?:de )?(\d{4})", norm)
    if m and _month(m.group(2)):
        return _iso(int(m.group(3)), _month(m.group(2)), int(m.group(1)))
    # "3/4/2024" is ambiguous across stores; accept only if unambiguous day > 12
    m = re.search(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", s)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if a > 12:
            return _iso(y, b, a)
        if b > 12:
            return _iso(y, a, b)
    return None


def _iso(y, mth, d):
    try:
        return date(y, mth, d).isoformat()
    except ValueError:
        return None


def days_between(earlier_iso, later_iso):
    if not earlier_iso or not later_iso:
        return None
    a = datetime.fromisoformat(earlier_iso[:10]).date()
    b = datetime.fromisoformat(later_iso[:10]).date()
    return (b - a).days
