"""Amazon search autocomplete: what buyers actually type.

A suggestion only appears when enough people search for it, so it is cheap
evidence of demand for a specific layered phrase. Requests are slow on purpose
(one every ~1.5 s, ~30 per seed). Run this on your own computer.
"""

import json
import random
import string
import time
import urllib.parse
import urllib.request
from datetime import date

from .text import normalize

MARKETPLACES = {
    "amazon.com": ("completion.amazon.com", "ATVPDKIKX0DER", "en_US"),
    "amazon.co.uk": ("completion.amazon.co.uk", "A1F83G8C2ARO7P", "en_GB"),
    "amazon.ca": ("completion.amazon.com", "A2EUQ1WTGCTBG2", "en_CA"),
    "amazon.com.au": ("completion.amazon.com.au", "A39IBJ37TRP1C6", "en_AU"),
    "amazon.de": ("completion.amazon.co.uk", "A1PA6795UKMFR9", "de_DE"),
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"


def prefixes(seed):
    seed = normalize(seed)
    out = [seed, seed + " for", seed + " with"]
    out += ["%s %s" % (seed, c) for c in string.ascii_lowercase]
    return out


def fetch(prefix, store, timeout=15):
    host, mid, lop = MARKETPLACES[store]
    query = urllib.parse.urlencode({
        "limit": 11, "prefix": prefix, "suggestion-type": "KEYWORD", "page-type": "Gateway",
        "alias": "stripbooks", "site-variant": "desktop", "version": 3, "mid": mid, "lop": lop,
    })
    req = urllib.request.Request("https://%s/api/2017/suggestions?%s" % (host, query),
                                 headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return [normalize(s.get("value", "")) for s in data.get("suggestions", []) if s.get("value")]


def expand(conn, seed, store, fetcher=fetch, delay=1.5, log=print):
    """Collect autocomplete suggestions for a seed and store them."""
    seed = normalize(seed)
    found = []
    for prefix in prefixes(seed):
        try:
            suggestions = fetcher(prefix, store)
        except Exception as exc:        # network hiccup or throttling: keep what we have
            log("  stopped at '%s': %s" % (prefix, exc))
            break
        for s in suggestions:
            if s not in found:
                found.append(s)
        if delay:
            time.sleep(delay + random.random() * delay)
    today = date.today().isoformat()
    for s in found:
        conn.execute("INSERT OR REPLACE INTO suggestions (seed, store, suggestion, taken_at) VALUES (?,?,?,?)",
                     (seed, store, s, today))
    conn.commit()
    return found


def import_list(conn, seed, store, lines):
    """Store suggestions typed/pasted by hand (one per line)."""
    seed = normalize(seed)
    today = date.today().isoformat()
    found = [normalize(line) for line in lines if normalize(line)]
    for s in found:
        conn.execute("INSERT OR REPLACE INTO suggestions (seed, store, suggestion, taken_at) VALUES (?,?,?,?)",
                     (seed, store, s, today))
    conn.commit()
    return found
