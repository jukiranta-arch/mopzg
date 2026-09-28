"""kdp: find KDP book ideas with proven demand and weak or no direct competition."""

import argparse
import os
import sys

from . import autocomplete, bookmarklet, config, db, importer, layers, report, seeds
from .analysis import analyze
from .ideas import generate
from .text import normalize

DEFAULT_DATA = os.environ.get("KDP_DATA", os.path.expanduser("~/kdp-data"))
DEFAULT_STORE = os.environ.get("KDP_STORE", "amazon.com")


def _ctx(args):
    conn = db.connect(args.data)
    return conn, config.load(args.data), layers.library(args.data)


def cmd_setup(args):
    conn, _, _ = _ctx(args)
    path = bookmarklet.install_page(os.path.join(args.data, "install_bookmarklet.html"))
    print("Data folder: %s" % args.data)
    print("Open this file in your browser and drag the button to your bookmarks bar:\n  %s" % path)


def cmd_import(args):
    conn, _, _ = _ctx(args)
    paths = args.paths or [os.path.expanduser("~/Downloads/kdp_capture_*.json")]
    for path, result in importer.import_paths(conn, paths):
        print("%s: %s" % (os.path.basename(path), result))


def cmd_analyze(args):
    conn, cfg, lib = _ctx(args)
    rep = analyze(conn, cfg, args.keyword, args.store, lib, args.layer)
    print(report.niche_text(rep, cfg))


def cmd_niches(args):
    conn, cfg, lib = _ctx(args)
    rows = [analyze(conn, cfg, r["keyword"], args.store, lib) for r in db.niches(conn, args.store)]
    if not rows:
        print("No niches captured for %s yet. Run `kdp next`." % args.store)
        return
    print("%-40s %5s %-8s %-7s %7s %8s %9s" % ("niche", "score", "verdict", "conf", "sellers", "top5/day", "direct"))
    for rep in sorted(rows, key=lambda r: r.score, reverse=True):
        m = rep.metrics
        print("%-40s %5d %-8s %-7s %7s %8s %9s" % (
            rep.keyword[:40], rep.score, rep.verdict, rep.confidence, m.get("sellers", "-"),
            m.get("top5_median_daily", "-"), "%s(%s)" % (m.get("direct", "-"), m.get("direct_sellers", "-"))))


def cmd_ideas(args):
    conn, cfg, lib = _ctx(args)
    ideas, reports = generate(conn, cfg, lib, args.store, include_unproven=args.unproven)
    if not ideas:
        print("No ideas yet. Ideas need at least one captured niche with proven demand "
              "(3+ books selling >= %.0f/day). Run `kdp next`." % cfg["selling_daily"])
        return
    for n, i in enumerate(ideas[:args.top], 1):
        print(report.idea_text(i, n))
        print()


def cmd_seeds(args):
    conn, _, _ = _ctx(args)
    found = seeds.discover(conn, args.store, days=args.days, limit=args.top)
    if not found:
        print("No seeds yet: capture some Best Sellers / Movers & Shakers / New Releases pages first.")
        return
    for g, s, examples in found:
        print("%-35s %5.1f   e.g. %s" % (g, s, examples[0] if examples else ""))


def cmd_expand(args):
    conn, _, lib = _ctx(args)
    if args.paste:
        with open(args.paste, encoding="utf-8") as fh:
            found = autocomplete.import_list(conn, args.seed, args.store, fh.read().splitlines())
    else:
        print("Asking Amazon autocomplete (about a minute, slow on purpose)...")
        found = autocomplete.expand(conn, args.seed, args.store)
    seed = normalize(args.seed)
    unmatched = []
    for s in found:
        hits = [label for cat, label in layers.detect(s, lib) if not layers.matches(lib[cat][label], seed)]
        print("  %-55s %s" % (s, ", ".join(hits)))
        if not hits and s != seed:
            unmatched.append(s)
    print("\n%d suggestions saved." % len(found))
    if unmatched:
        print("Not in the layer library (new layer ideas? add them to %s):"
              % os.path.join(args.data, "layers.json"))
        for s in unmatched[:15]:
            print("  " + s)


def cmd_mark(args):
    conn, _, _ = _ctx(args)
    conn.execute("INSERT OR REPLACE INTO marks (keyword, store, asin, relation) VALUES (?,?,?,?)",
                 (normalize(args.keyword), args.store, args.asin, args.relation))
    conn.commit()
    print("Marked %s as %s in '%s'." % (args.asin, args.relation, normalize(args.keyword)))


def cmd_next(args):
    conn, cfg, lib = _ctx(args)
    for n, action in enumerate(report.next_actions(conn, cfg, lib, args.store), 1):
        print("%2d. %s" % (n, action))


def cmd_report(args):
    conn, cfg, lib = _ctx(args)
    path = report.write_markdown(conn, cfg, lib, args.store, os.path.join(args.data, "reports"))
    print("Wrote %s" % path)


def cmd_layers(args):
    _, _, lib = _ctx(args)
    for cat, items in lib.items():
        print("%s:" % cat)
        print("  " + ", ".join(items))


def build_parser():
    p = argparse.ArgumentParser(prog="kdp", description=__doc__)
    p.add_argument("--data", default=DEFAULT_DATA, help="data folder (default %(default)s, env KDP_DATA)")
    p.add_argument("--store", default=DEFAULT_STORE, help="amazon.com, amazon.co.uk, ... (env KDP_STORE)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("setup", help="create the data folder and the bookmarklet installer").set_defaults(fn=cmd_setup)

    s = sub.add_parser("import", help="import kdp_capture_*.json files (default: ~/Downloads)")
    s.add_argument("paths", nargs="*")
    s.set_defaults(fn=cmd_import)

    s = sub.add_parser("next", help="what to capture or check next")
    s.set_defaults(fn=cmd_next)

    s = sub.add_parser("ideas", help="layered book ideas on proven demand, best first")
    s.add_argument("--top", type=int, default=15)
    s.add_argument("--unproven", action="store_true", help="also show layers with no demand evidence yet")
    s.set_defaults(fn=cmd_ideas)

    s = sub.add_parser("analyze", help="score one captured niche")
    s.add_argument("keyword")
    s.add_argument("--layer", action="append", help="treat this layer as part of the concept (repeatable)")
    s.set_defaults(fn=cmd_analyze)

    sub.add_parser("niches", help="all captured niches with scores").set_defaults(fn=cmd_niches)

    s = sub.add_parser("seeds", help="base niche ideas from captured Best Sellers / Movers lists")
    s.add_argument("--days", type=int, default=30)
    s.add_argument("--top", type=int, default=30)
    s.set_defaults(fn=cmd_seeds)

    s = sub.add_parser("expand", help="Amazon autocomplete for a seed (what buyers type)")
    s.add_argument("seed")
    s.add_argument("--paste", metavar="FILE", help="read suggestions from a text file instead of fetching")
    s.set_defaults(fn=cmd_expand)

    s = sub.add_parser("mark", help="override direct / non-direct for a book in a niche")
    s.add_argument("keyword")
    s.add_argument("asin")
    s.add_argument("relation", choices=["direct", "non_direct", "unrelated"])
    s.set_defaults(fn=cmd_mark)

    sub.add_parser("report", help="write a markdown shortlist to <data>/reports").set_defaults(fn=cmd_report)
    sub.add_parser("layers", help="list the layer library").set_defaults(fn=cmd_layers)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.fn(args)
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
