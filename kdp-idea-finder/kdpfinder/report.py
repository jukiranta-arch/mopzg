"""Terminal output, the next-actions queue and the markdown shortlist."""

import os
from datetime import date

from . import ideas as ideas_mod, seeds as seeds_mod


def money(value, store, cfg):
    if value is None:
        return "?"
    return "%s%s" % (cfg["currency"].get(store, ""), format(value, ",.2f") if value < 100 else format(int(value), ","))


def niche_text(rep, cfg):
    m = rep.metrics
    name = rep.keyword + "".join(" + %s" % label for label in rep.extra_layers)
    lines = ["%s  [%s]  score %d/100 -> %s (confidence: %s)" % (
        name, rep.store, rep.score, rep.verdict.upper(), rep.confidence)]
    if rep.layers:
        lines.append("  layers: " + ", ".join("%s (%s)" % (label, cat) for cat, label, _ in rep.layers))
    if not rep.books:
        lines += ["  ! " + f for f in rep.flags]
        return "\n".join(lines)
    lines.append("  score parts: " + ", ".join("%s %.0f" % kv for kv in rep.parts.items()))
    lines.append("  demand: %d of %d books sell >= %.0f/day; top-5 median %.1f/day; field ~%s copies/month"
                 % (m["sellers"], m["field"], cfg["selling_daily"], m["top5_median_daily"],
                    format(m["field_monthly_units"], ",")))
    lines.append("  money: typical %s, %s pages -> %s royalty/copy; a median seller earns ~%s/month"
                 % (money(m["typical_price"], rep.store, cfg), m["typical_pages"] or "?",
                    money(m["royalty_per_copy"], rep.store, cfg),
                    money(m["median_seller_monthly_royalty"], rep.store, cfg)))
    lines.append("  direct competitors: %d (%d selling, strength %.2f, best BSR %s)"
                 % (m["direct"], m["direct_sellers"], m["direct_strength"],
                    format(m["best_direct_bsr"], ",") if m["best_direct_bsr"] else "-"))
    lines.append("  beatable: %d sellers with <100 reviews, %d indie sellers, %d sellers under 6 months old"
                 % (m["low_review_sellers"], m["indie_sellers"], m["young_sellers"]))
    lines += ["  ! " + f for f in rep.flags]
    lines.append("  %-3s %-6s %9s %7s %7s %5s %4s  %s" % ("#", "rel", "BSR", "/day", "reviews", "age", "ind", "title"))
    for i, b in enumerate(rep.books, 1):
        lines.append("  %-3d %-6s %9s %7.1f %7d %5s %4s  %s" % (
            i, "DIRECT" if b.relation == "direct" else "-", format(b.bsr, ",") if b.bsr else "-",
            b.daily, b.reviews, "%dd" % b.age_days if b.age_days is not None else "?",
            "yes" if b.indie else "", (b.title or "")[:70]))
    return "\n".join(lines)


def idea_text(i, n):
    lines = ["%2d. %s  [%s]  %d/100  (%s)" % (n, i.concept, i.store, i.score, i.status)]
    lines.append("    base '%s' sells (top-5 median %.1f/day, niche score %d); layer '%s' (%s)"
                 % (i.base, i.base_top5_daily, i.base_score, i.layer, i.category))
    if i.status == "verified":
        m = i.verified_report.metrics
        lines.append("    verified search: %d direct (%d selling), strength %.2f, confidence %s"
                     % (m["direct"], m["direct_sellers"], m["direct_strength"], i.verified_report.confidence))
    else:
        lines.append("    in the base field this layer is served with strength %.2f (0 = nobody)" % i.gap_strength)
    for title, bsr, niche in i.evidence_books:
        lines.append("    + sells elsewhere: BSR %s  %s  (in '%s')" % (format(bsr, ",") if bsr else "?", title[:60], niche))
    for s in i.evidence_searches:
        lines.append("    + buyers type: '%s'" % s)
    lines.append("    next: " + i.next_step)
    return "\n".join(lines)


def next_actions(conn, cfg, lib, store, limit=12):
    """The to-do list that keeps the loop going. Most valuable first."""
    actions = []
    ideas, reports = ideas_mod.generate(conn, cfg, lib, store)
    if not reports and not conn.execute("SELECT 1 FROM lists WHERE store = ?", (store,)).fetchone():
        return [
            "Open Amazon Best Sellers > Books and click KDP Capture on 3-5 categories you like "
            "(Movers & Shakers and New Releases are the best idea sources).",
            "Or search Amazon (Books) for a niche you already have in mind and click KDP Capture.",
        ]
    for i in ideas:
        if i.status == "estimated" and i.score >= 40:
            actions.append((i.score + 10, "Search '%s' on %s and click KDP Capture (idea scored %d, unverified)"
                            % (i.concept, store, i.score)))
        elif i.status == "verified" and i.verified_report.confidence != "high" and i.score >= cfg["verdict"]["average"]:
            actions.append((i.score + 5, "Re-capture '%s' on a different day (confidence %s, score %d)"
                            % (i.concept, i.verified_report.confidence, i.score)))
    for kw, rep in reports.items():
        if rep.score >= cfg["verdict"]["average"] and rep.confidence != "high" and rep.layers:
            actions.append((rep.score, "Re-capture '%s' on a different day (confidence %s, score %d)"
                            % (kw, rep.confidence, rep.score)))
        if rep.verdict == "good" and rep.confidence == "high":
            actions.append((rep.score + 20, "Write a brief for '%s' (score %d, high confidence)" % (kw, rep.score)))
    for g, s, _ in seeds_mod.discover(conn, store, limit=5):
        actions.append((35, "Search '%s' on %s and click KDP Capture (trending in your captured lists)" % (g, store)))
    for rep in reports.values():
        if rep.metrics.get("sellers", 0) >= 3 and not conn.execute(
                "SELECT 1 FROM suggestions WHERE seed = ? AND store = ?", (rep.keyword, store)).fetchone():
            actions.append((30, "Run `kdp expand \"%s\"` to see what buyers type after it" % rep.keyword))
    seen, out = set(), []
    for _, a in sorted(actions, key=lambda x: x[0], reverse=True):
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out[:limit]


def write_markdown(conn, cfg, lib, store, out_dir, top=15):
    ideas, reports = ideas_mod.generate(conn, cfg, lib, store)
    today = date.today().isoformat()
    lines = ["# KDP shortlist: %s, %s" % (store, today), "",
             "Scoring model %s. Sales are estimates from BSR; see config for the table used." % cfg["scoring_model"],
             "", "## Next actions", ""]
    lines += ["- " + a for a in next_actions(conn, cfg, lib, store)]
    lines += ["", "## Top ideas (proven demand + weak/no direct competition)", ""]
    if not ideas:
        lines.append("_No ideas yet: capture more niches with proven demand._")
    for n, i in enumerate(ideas[:top], 1):
        lines += ["```", idea_text(i, n), "```", ""]
    lines += ["## Captured niches", "",
              "| niche | score | verdict | confidence | sellers | top-5 /day | direct (selling) | captured |",
              "|---|---|---|---|---|---|---|---|"]
    for kw, rep in sorted(reports.items(), key=lambda kv: kv[1].score, reverse=True):
        m = rep.metrics
        lines.append("| %s | %d | %s | %s | %s | %s | %s (%s) | %s |" % (
            kw, rep.score, rep.verdict, rep.confidence, m.get("sellers", "-"), m.get("top5_median_daily", "-"),
            m.get("direct", "-"), m.get("direct_sellers", "-"), rep.searched_on or "-"))
    lines += ["", "## Niche details", ""]
    for kw, rep in sorted(reports.items(), key=lambda kv: kv[1].score, reverse=True):
        lines += ["```", niche_text(rep, cfg), "```", ""]
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "%s_%s_shortlist.md" % (today, store.replace(".", "-")))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path
