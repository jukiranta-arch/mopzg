"""Idea engine: original layered concepts on top of proven demand.

For every captured niche whose demand is proven, try each layer from the
library. Keep a layer when
  1. it has demand evidence of its own: books carrying that layer sell in
     *other* niches, and/or Amazon autocomplete shows buyers typing it with
     this niche; and
  2. nothing in this niche's field already serves it well (no strong direct
     competitor).
If the layered phrase has already been captured as its own search, the real
analysis of that search replaces the estimate ("verified").
"""

from dataclasses import dataclass, field

from . import db, layers as layers_mod
from .analysis import analyze, combined_strength, demand_factor, search_books
from .text import normalize, token_coverage, tokens

# Words that name a format, not a topic. A niche whose keyword is only a layer
# plus these words ("grief journal") is that layer's own home turf, so its
# sellers don't prove the layer works as a modifier on something else.
# Pairs that make no sense as a book, whatever the data says.
KIDS_BASE = r"kids?|children|childrens|toddlers?|boys?|girls?|baby|preschool|ages? \d"
ADULT_SITUATIONS = {"after divorce", "after a breakup", "after miscarriage", "for pregnancy", "for retirement",
                    "for empty nesters", "for sobriety", "for menopause", "for ivf", "for newlyweds",
                    "for weddings", "for a new job", "for military spouses", "for cancer patients", "for dementia",
                    "for chronic illness", "for special needs parents", "for adoption"}
YOUNG_BUYERS = {"for toddlers": {"activity", "coloring", "story", "baby"},
                "for kids": {"activity", "coloring", "story", "puzzle", "journal"}}


def _nonsense(base, base_families, label):
    if label in ADULT_SITUATIONS and layers_mod.matches(KIDS_BASE, base):
        return True
    allowed = YOUNG_BUYERS.get(label)
    return bool(allowed and base_families and not (base_families & allowed))


GENERIC = {"journal", "notebook", "book", "log", "logbook", "planner", "diary", "workbook",
           "coloring", "colouring", "activity", "puzzle", "word", "search", "prompt", "guided",
           "daily", "gift", "kid", "adult", "guide"}


@dataclass
class Idea:
    concept: str
    base: str
    layer: str
    category: str
    store: str
    score: int
    status: str                         # "estimated" or "verified"
    base_score: int
    base_top5_daily: float
    gap_strength: float
    evidence_books: list = field(default_factory=list)       # (title, bsr, niche) where the layer sells
    evidence_searches: list = field(default_factory=list)    # autocomplete strings
    verified_report: object = None

    @property
    def next_step(self):
        if self.status == "verified":
            if self.verified_report.confidence != "high":
                return "re-capture '%s' on another day (BSR days: %s)" % (
                    self.concept, self.verified_report.confidence)
            return "write a brief"
        return "capture the search '%s'" % self.concept


def _is_modifier(pattern, niche_keyword):
    """True when the layer modifies another topic in this niche (not the topic itself)."""
    if not layers_mod.matches(pattern, niche_keyword):
        return True
    return any(t not in GENERIC for t in tokens(layers_mod.strip(pattern, niche_keyword)))


def _layer_sellers(conn, cfg, reports, lib, store):
    """layer -> [(asin, title, bsr, daily, niche)] for selling books that carry the layer as a modifier.
    Uses every captured result page, so broad market searches count as evidence too."""
    out = {}
    seen = set()
    for rep in reports.values():
        for b in search_books(conn, cfg, rep.keyword, store):
            if not b.selling or b.asin in seen:
                continue
            seen.add(b.asin)
            for cat, label in layers_mod.detect(b.title, lib):
                if _is_modifier(lib[cat][label], rep.keyword):
                    out.setdefault((cat, label), []).append((b.asin, b.title, b.bsr, b.daily, rep.keyword))
    return out


def _find_verified(reports, base, pattern):
    for kw, rep in reports.items():
        if kw != base and token_coverage(base, kw) == 1.0 and layers_mod.matches(pattern, kw) and rep.books:
            return rep
    return None


def generate(conn, cfg, lib, store, min_demand=0.35, include_unproven=False, max_per_base=3):
    reports = {r["keyword"]: analyze(conn, cfg, r["keyword"], store, lib)
               for r in db.niches(conn, store)}
    sellers_by_layer = _layer_sellers(conn, cfg, reports, lib, store)
    suggestions = db.suggestions(conn, store)

    ideas = []
    for base, rep in reports.items():
        top5 = rep.metrics.get("top5_median_daily", 0)
        dfrac = demand_factor(top5) * min(1.0, rep.metrics.get("sellers", 0) / 3)
        if dfrac < min_demand:
            continue
        base_cats = {cat for cat, _, _ in rep.layers}
        base_families = layers_mod.families(base)
        names_audience = " for " in " %s " % base      # "activity book for kids" already has its buyer
        field_asins = {b.asin for b in rep.books}
        per_base = []
        for cat, items in lib.items():
            if cat in base_cats:
                continue
            for label, pattern in items.items():
                if layers_mod.matches(pattern, base) or _nonsense(base, base_families, label):
                    continue
                served = [b for b in rep.books if layers_mod.matches(pattern, b.title)]
                strength = combined_strength(served, cfg)
                if strength >= 0.5:
                    continue
                books = [e for e in sellers_by_layer.get((cat, label), [])
                         if e[4] != base and e[0] not in field_asins
                         and (not base_families or base_families & layers_mod.families(e[1]))]
                books.sort(key=lambda e: e[3], reverse=True)
                searches = [s["suggestion"] for s in suggestions
                            if token_coverage(base, s["suggestion"]) == 1.0
                            and layers_mod.matches(pattern, s["suggestion"])]
                sold = sum(demand_factor(e[3]) for e in books)
                if not searches and not include_unproven:
                    if sold < 0.5:                      # needs at least one real seller of the same kind
                        continue
                    if names_audience and cat in ("buyer", "situation"):
                        continue
                evidence = 0.6 * min(1.0, sold / 1.5) + 0.4 * min(len(searches), 2) / 2
                concept = layers_mod.search_phrase(base, label)
                weight = cfg["layer_weight"].get(cat, 0.8)
                thin = weight + (1 - weight) * (1 - rep.metrics.get("direct_strength", 0))
                score = 100 * dfrac * (0.5 + 0.5 * evidence) * (1 - strength) * thin
                verified = _find_verified(reports, base, pattern)
                idea = Idea(concept=concept, base=base, layer=label, category=cat, store=store,
                            score=int(round(score)), status="estimated", base_score=rep.score,
                            base_top5_daily=top5, gap_strength=round(strength, 2),
                            evidence_books=[(t, bsr, n) for _, t, bsr, _, n in books[:3]],
                            evidence_searches=searches[:3])
                if verified:
                    idea.status, idea.verified_report = "verified", verified
                    idea.concept, idea.score = verified.keyword, verified.score
                per_base.append(idea)
        per_base.sort(key=lambda i: i.score, reverse=True)
        ideas.extend(per_base[:max_per_base])

    ideas.sort(key=lambda i: (i.status == "verified", i.score), reverse=True)
    best = {}
    for idea in ideas:
        best.setdefault(idea.concept, idea)
    return sorted(best.values(), key=lambda i: i.score, reverse=True), reports
