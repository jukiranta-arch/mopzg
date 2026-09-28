"""Seed discovery: phrases that keep showing up in captured Best Sellers,
Movers & Shakers and New Releases lists. These are base niches to search next."""

from collections import defaultdict

from .text import STOPWORDS, normalize

JUNK = {"edition", "paperback", "hardcover", "large", "print", "gift", "gifts", "ideas",
        "perfect", "cute", "notebook", "pages", "inches", "x", "8", "5", "11", "6", "9",
        "lined", "blank", "size", "cover", "matte", "glossy", "unique", "best", "great",
        "new", "ultimate", "complete"}


def _ngrams(words, n):
    return [" ".join(words[i:i + n]) for i in range(len(words) - n + 1)]


def discover(conn, store, days=30, limit=30, cfg=None):
    """Phrases shared by several books that sell right now.

    Sources: captured Best Sellers / Movers / New Releases lists (weighted by
    rank), and every selling book in captured searches, all pages (weighted by
    estimated sales). Broad searches like "gift for women" feed this well.
    """
    from . import config
    from .analysis import demand_factor, search_books
    cfg = cfg or config.DEFAULTS
    captured = {r["keyword"] for r in conn.execute("SELECT DISTINCT keyword FROM searches WHERE store = ?",
                                                   (store,))}
    entries = []        # (title, weight, example)
    for r in conn.execute(
            "SELECT li.title, li.rank, l.name, l.kind FROM list_items li JOIN lists l ON l.id = li.list_id "
            "WHERE l.store = ? AND l.taken_at >= date('now', ?)", (store, "-%d days" % days)):
        weight = 1.0 / (1 + (r["rank"] or 50) / 25)
        if r["kind"] == "movers":
            weight *= 1.5                       # rising right now
        entries.append((r["title"], weight, "#%s %s (%s)" % (r["rank"], (r["title"] or "")[:70], r["name"])))
    seen = set()
    for kw in captured:
        for b in search_books(conn, cfg, kw, store):
            if b.selling and b.asin not in seen:
                seen.add(b.asin)
                entries.append((b.title, demand_factor(b.daily),
                                "BSR %s %s (in '%s')" % (format(b.bsr, ","), (b.title or "")[:70], kw)))

    score = defaultdict(float)
    examples = defaultdict(list)
    books = defaultdict(set)
    for title, weight, example in entries:
        words = [w for w in normalize(title).split() if not w.isdigit()]
        grams = set()
        for n in (2, 3, 4):
            for g in _ngrams(words, n):
                parts = g.split()
                if parts[0] in STOPWORDS or parts[-1] in STOPWORDS or any(p in JUNK for p in parts):
                    continue
                grams.add(g)
        for g in grams:
            score[g] += weight
            books[g].add(title)
            if len(examples[g]) < 2:
                examples[g].append(example)
    ranked = [(g, s) for g, s in score.items() if len(books[g]) >= 2 and g not in captured]
    ranked.sort(key=lambda x: (round(x[1], 3), len(x[0])), reverse=True)
    # Drop short phrases that are just part of an equally strong longer one.
    out = []
    for g, s in ranked:
        if any(g in o and s <= os_ * 1.2 for o, os_, _ in out):
            continue
        out.append((g, s, examples[g]))
        if len(out) >= limit:
            break
    return out
