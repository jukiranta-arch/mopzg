"""Niche analysis: proven demand, direct vs non-direct competition, and a 0-100 score.

Definitions used throughout:
- The *field* of a niche is the first `field_size` organic results of its Amazon search.
- A book *sells* when its estimated sales are >= `selling_daily` copies/day.
- A competitor is *direct* when it serves the same buyer, problem and format as the
  concept: its title covers the concept's keyword and every layer the concept adds.
  Everything else in the field is *non-direct*: it proves people buy in this space,
  but a buyer looking for the concept would not see it as the same book.
"""

import math
from dataclasses import dataclass, field
from datetime import date
from statistics import median

from . import db, layers as layers_mod
from .sales import daily_sales, royalty_per_copy, to_store_currency
from .text import days_between, normalize, token_coverage


@dataclass
class BookView:
    asin: str
    title: str
    bsr: int = None
    daily: float = 0.0
    reviews: int = 0
    rating: float = None
    price: float = None
    pages: int = None
    pub_date: str = None
    age_days: int = None
    indie: bool = False
    snapshot_days: int = 0
    last_seen: str = None
    relation: str = "non_direct"
    selling: bool = False


@dataclass
class NicheReport:
    keyword: str
    store: str
    layers: list
    extra_layers: list = field(default_factory=list)
    searched_on: str = None
    books: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    parts: dict = field(default_factory=dict)
    score: int = 0
    verdict: str = "skip"
    confidence: str = "low"
    flags: list = field(default_factory=list)

    @property
    def direct(self):
        return [b for b in self.books if b.relation == "direct"]

    @property
    def sellers(self):
        return [b for b in self.books if b.selling]


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def demand_factor(daily):
    """0 at 0.3 copies/day, 1 at 20 copies/day, log scale."""
    if daily <= 0:
        return 0.0
    return _clamp(math.log10(daily / 0.3) / math.log10(20 / 0.3))


def review_factor(reviews):
    """0 at 0 reviews, 1 at 500+ reviews, log scale."""
    return _clamp(math.log10((reviews or 0) + 1) / math.log10(501))


def book_strength(b, cfg):
    """How hard a single competitor is to beat (0..1)."""
    if b.daily < cfg["selling_daily"] * 0.3:
        return 0.0
    return demand_factor(b.daily) ** 0.7 * max(0.2, review_factor(b.reviews))


def combined_strength(books, cfg):
    remaining = 1.0
    for b in books:
        remaining *= 1 - book_strength(b, cfg)
    return 1 - remaining


def load_book(conn, cfg, asin, store):
    row = db.book(conn, asin, store)
    snaps = db.snapshots(conn, asin, store)
    b = BookView(asin=asin, title=(row["title"] if row else None) or asin)
    if row:
        b.pages, b.pub_date, b.indie = row["pages"], row["pub_date"], bool(row["indie"])
    with_bsr = [s for s in snaps if s["bsr"]]
    if with_bsr:
        recent = [s["bsr"] for s in with_bsr[-3:]]      # median of last 3 days smooths spikes
        b.bsr = int(median(recent))
        b.daily = daily_sales(b.bsr, store, cfg)
    if snaps:
        last = snaps[-1]
        b.last_seen = last["taken_at"]
        b.reviews = next((s["reviews"] for s in reversed(snaps) if s["reviews"] is not None), 0) or 0
        b.rating = next((s["rating"] for s in reversed(snaps) if s["rating"]), None)
        priced = next((s for s in reversed(snaps) if s["price"]), None)
        if priced:
            b.price = to_store_currency(priced["price"], priced["price_currency"], store, cfg)
    b.snapshot_days = len({s["taken_at"] for s in with_bsr})
    b.age_days = days_between(b.pub_date, b.last_seen or date.today().isoformat())
    return b


def classify(keyword, concept_layers, title):
    """'direct' when the title covers the keyword and every concept layer."""
    if not all(layers_mod.matches(pattern, title) for _, _, pattern in concept_layers):
        return "non_direct"
    return "direct" if token_coverage(keyword, title) >= 0.5 else "non_direct"


def concept_layers(keyword, extra_labels, lib):
    """Layers the concept adds: those named in the keyword plus any given explicitly."""
    found = {(cat, label): lib[cat][label] for cat, label in layers_mod.detect(keyword, lib)}
    for label in extra_labels or []:
        hit = layers_mod.find(label, lib)
        if not hit:
            raise ValueError("unknown layer %r (see `kdp layers`)" % label)
        found[(hit[0], hit[1])] = hit[2]
    return [(cat, label, pattern) for (cat, label), pattern in sorted(found.items())]


def analyze(conn, cfg, keyword, store, lib, extra_layers=None):
    keyword = normalize(keyword)
    rep = NicheReport(keyword=keyword, store=store, extra_layers=list(extra_layers or []),
                      layers=concept_layers(keyword, extra_layers, lib))
    search = db.latest_search(conn, keyword, store)
    if not search:
        rep.flags.append("not captured yet")
        return rep
    rep.searched_on = search["taken_at"]
    overrides = db.marks(conn, keyword, store)
    for asin in db.search_asins(conn, search["id"], cfg["field_size"]):
        b = load_book(conn, cfg, asin, store)
        b.relation = overrides.get(asin) or classify(keyword, rep.layers, b.title)
        if b.relation != "unrelated":
            rep.books.append(b)
    score_niche(rep, cfg)
    if rep.extra_layers:
        phrase = keyword
        for label in rep.extra_layers:
            phrase = layers_mod.search_phrase(phrase, layers_mod.find(label, lib)[1])
        rep.flags.append("estimated from the '%s' search: capture '%s' to verify" % (keyword, phrase))
    return rep


def search_books(conn, cfg, keyword, store):
    """Every organic book of the latest capture of a search, all pages (not just the field)."""
    search = db.latest_search(conn, normalize(keyword), store)
    if not search:
        return []
    books = []
    for asin in db.search_asins(conn, search["id"], 10000):
        b = load_book(conn, cfg, asin, store)
        b.selling = b.daily >= cfg["selling_daily"]
        books.append(b)
    return books


def score_niche(rep, cfg):
    w = cfg["score_weights"]
    books = rep.books
    sell_min = cfg["selling_daily"]
    for b in books:
        b.selling = b.daily >= sell_min
    sellers = [b for b in books if b.selling]
    top5 = sorted((b.daily for b in books), reverse=True)[:5]
    top5_median = median(top5) if top5 else 0.0

    prices = [b.price for b in books if b.price]
    pages = [b.pages for b in books if b.pages]
    typ_price = median(prices) if prices else None
    typ_pages = int(median(pages)) if pages else None
    median_seller_daily = median([b.daily for b in sellers]) if sellers else 0.0
    royalty = royalty_per_copy(typ_price, typ_pages, rep.store, cfg) if typ_price else 0.0

    direct = [b for b in books if b.relation == "direct"]
    direct_sellers = [b for b in direct if b.selling]
    strength = combined_strength(direct, cfg)

    new = [b for b in books if b.age_days is not None and b.age_days <= cfg["new_book_days"]]
    young_sellers = [b for b in sellers if b.age_days is not None and b.age_days <= cfg["young_book_days"]]
    low_review_sellers = [b for b in sellers if b.reviews < 100]
    indie_sellers = [b for b in sellers if b.indie]
    wave = len(books) >= 5 and len(new) >= max(4, 0.3 * len(books))

    text = " ".join([rep.keyword] + [label for _, label, _ in rep.layers])
    trademark = [t for t in cfg["trademark_words"] if layers_mod.matches(t, text)]
    health = [t for t in cfg["health_words"] if layers_mod.matches(t, text)]

    parts = {}
    parts["demand"] = w["demand"] * demand_factor(top5_median) * min(1.0, len(sellers) / 3)
    parts["gap"] = w["gap"] * (1 - strength)
    if sellers:
        parts["beatability"] = w["beatability"] * (
            len(low_review_sellers) / len(sellers) + len(indie_sellers) / len(sellers)
            + min(1.0, len(young_sellers) / 2)) / 3
    else:
        parts["beatability"] = 0.0
    parts["durability"] = max(0.0, w["durability"] - (7 if wave else 0)
                              - (5 if trademark else 0) - (3 if health else 0))
    total = sum(parts.values())

    if not books:
        rep.flags.append("no organic results captured")
    if trademark:
        rep.flags.append("TRADEMARK risk: %s -- do not publish without clearance" % ", ".join(trademark))
        total = min(total, 30)
    if health:
        rep.flags.append("health topic (%s): no medical claims, add disclaimers" % ", ".join(health))
    if wave:
        rep.flags.append("copycat wave: %d of %d books are under %d days old"
                         % (len(new), len(books), cfg["new_book_days"]))
    if not rep.layers:
        rep.flags.append("no layers: every relevant book is a direct competitor; try `kdp ideas`")
    if books and not sellers:
        rep.flags.append("no book in the field sells >= %.0f/day: demand not proven" % sell_min)

    snap_days = sorted(b.snapshot_days for b in books) or [0]
    typical_days = snap_days[len(snap_days) // 2]
    rep.confidence = "high" if typical_days >= 3 else "medium" if typical_days == 2 else "low"

    rep.parts = {k: round(v, 1) for k, v in parts.items()}
    rep.score = int(round(total))
    v = cfg["verdict"]
    rep.verdict = "good" if rep.score >= v["good"] else "average" if rep.score >= v["average"] else "skip"
    rep.metrics = {
        "field": len(books),
        "sellers": len(sellers),
        "top5_median_daily": round(top5_median, 2),
        "field_monthly_units": int(sum(b.daily for b in books) * 30),
        "typical_price": typ_price,
        "typical_pages": typ_pages,
        "royalty_per_copy": round(royalty, 2),
        "median_seller_monthly_royalty": int(median_seller_daily * 30 * royalty),
        "direct": len(direct),
        "direct_sellers": len(direct_sellers),
        "direct_strength": round(strength, 2),
        "best_direct_bsr": min((b.bsr for b in direct if b.bsr), default=None),
        "new_books": len(new),
        "young_sellers": len(young_sellers),
        "low_review_sellers": len(low_review_sellers),
        "indie_sellers": len(indie_sellers),
    }
    return rep
