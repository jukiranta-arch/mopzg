import json
import os
import unittest

from helpers import Ctx, book, product, search

from kdpfinder import autocomplete, importer, report, seeds
from kdpfinder.analysis import analyze, classify, concept_layers
from kdpfinder.ideas import generate
from kdpfinder.sales import daily_sales, royalty_per_copy
from kdpfinder.text import parse_date, parse_float, parse_int, token_coverage
from kdpfinder import config


class TextTests(unittest.TestCase):
    def test_numbers(self):
        self.assertEqual(parse_int("#12,345"), 12345)
        self.assertEqual(parse_int("Nr. 12.345"), 12345)
        self.assertEqual(parse_int("1,234 ratings"), 1234)
        self.assertAlmostEqual(parse_float("$8.99"), 8.99)
        self.assertAlmostEqual(parse_float("8,99 €"), 8.99)
        self.assertAlmostEqual(parse_float("$1,234.50"), 1234.5)
        self.assertAlmostEqual(parse_float("4.6 out of 5 stars"), 4.6)
        self.assertAlmostEqual(parse_float("4,6 von 5 Sternen"), 4.6)

    def test_currency(self):
        from kdpfinder.sales import to_store_currency
        from kdpfinder.text import parse_currency
        self.assertEqual(parse_currency("EUR 12.79"), "EUR")
        self.assertEqual(parse_currency("\u00a37.99"), "GBP")
        self.assertIsNone(parse_currency("$9.99"))
        cfg = config.load("/nonexistent")
        self.assertAlmostEqual(to_store_currency(10.0, "EUR", "amazon.com", cfg), 11.0)
        self.assertEqual(to_store_currency(9.99, None, "amazon.com", cfg), 9.99)

    def test_bought(self):
        from kdpfinder.text import parse_bought
        self.assertEqual(parse_bought("1K+ bought in past month"), 1000)
        self.assertEqual(parse_bought("50+ bought in past month"), 50)
        self.assertIsNone(parse_bought(""))

    def test_dates(self):
        self.assertEqual(parse_date("March 3, 2024"), "2024-03-03")
        self.assertEqual(parse_date("3 March 2024"), "2024-03-03")
        self.assertEqual(parse_date("3. März 2024"), "2024-03-03")
        self.assertEqual(parse_date("Sept. 14, 2025"), "2025-09-14")
        self.assertEqual(parse_date("Independently published (Jan. 5, 2026)"), "2026-01-05")
        self.assertIsNone(parse_date("English"))

    def test_ranks(self):
        ranks = importer.parse_ranks(
            "#12,345 in Books (See Top 100 in Books) #12 in Grief & Bereavement (Books) #45 in Journal Writing")
        self.assertEqual(ranks[0], (12345, "Books"))
        self.assertEqual([r[0] for r in ranks], [12345, 12, 45])
        self.assertEqual(importer.overall_rank(ranks), (12345, "Books"))
        de = importer.parse_ranks("Nr. 3.210 in Bücher (Siehe Top 100 in Bücher) Nr. 5 in Tagebücher")
        self.assertEqual(importer.overall_rank(de)[0], 3210)

    def test_coverage(self):
        self.assertEqual(token_coverage("grief journals", "The Grief Journal"), 1.0)


class SalesTests(unittest.TestCase):
    def setUp(self):
        self.cfg = config.load("/nonexistent")

    def test_bsr_curve(self):
        self.assertAlmostEqual(daily_sales(100000, "amazon.com", self.cfg), 1.0)
        values = [daily_sales(r, "amazon.com", self.cfg) for r in (500, 5000, 50000, 500000)]
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertLess(daily_sales(10000, "amazon.co.uk", self.cfg), daily_sales(10000, "amazon.com", self.cfg))

    def test_royalty(self):
        # $9.99 clears the 60% floor: 9.99*0.6 - (1.00 + 120*0.012)
        self.assertAlmostEqual(royalty_per_copy(9.99, 120, "amazon.com", self.cfg), 5.994 - 2.44, places=3)
        # $8.99 is below it: 50%
        self.assertAlmostEqual(royalty_per_copy(8.99, 100, "amazon.com", self.cfg), 4.495 - 2.30, places=3)


class ImportTests(unittest.TestCase):
    def test_product_fields(self):
        p = importer.parse_product(product("B0TEST0001", "Grief Journal", bsr=23456, reviews=1234,
                                           pages=140, pub="Jan. 5, 2026"))
        self.assertEqual(p["bsr"], 23456)
        self.assertEqual(p["pages"], 140)
        self.assertEqual(p["pub_date"], "2026-01-05")
        self.assertEqual(p["publisher"], "Independently published")
        self.assertEqual(p["indie"], 1)
        self.assertEqual(p["reviews"], 1234)
        self.assertEqual(p["format"], "Paperback")

    def test_file_import_skips_duplicates(self):
        ctx = Ctx()
        path = os.path.join(ctx.dir, "kdp_capture_x.json")
        with open(path, "w") as fh:
            json.dump(search("grief journal", [book(1, "Grief Journal", 5000)]), fh)
        first = importer.import_paths(ctx.conn, [os.path.join(ctx.dir, "kdp_capture_*.json")])
        second = importer.import_paths(ctx.conn, [path])
        self.assertIn("1 with BSR", first[0][1])
        self.assertEqual(second[0][1], "already imported")

    def test_same_day_empty_snapshot_does_not_replace(self):
        ctx = Ctx()
        ctx.load(search("grief journal", [book(1, "Grief Journal", 5000)]))
        empty = search("grief journal", [book(1, "Grief Journal", None, reviews=0)])
        empty["items"][0]["product"]["price_text"] = ""
        ctx.load(empty)
        row = ctx.conn.execute("SELECT bsr FROM snapshots").fetchone()
        self.assertEqual(row["bsr"], 5000)


# ---------------------------------------------------------------- scenario data
# A proven "prayer journal" niche where the "for men" layer sells,
# a proven "grief journal" niche where nobody serves men yet,
# and a crowded "gratitude journal for women" niche.

PRAYER = [
    book(1, "Prayer Journal for Women: 52 Week Scripture Devotional", 4000, 3000, prefix="B0P"),
    book(2, "Prayer Journal for Men: A Guided Journal to Grow in Faith", 15000, 400, prefix="B0P"),
    book(3, "The One Year Prayer Journal", 9000, 900, prefix="B0P"),
    book(4, "Prayer Journal for Teen Girls", 30000, 150, prefix="B0P"),
    book(5, "My Prayer Journal", 60000, 40, prefix="B0P"),
]
GRIEF = [
    book(1, "Grief Journal: Prompts for Healing After Loss", 6000, 800, prefix="B0G"),
    book(2, "The Grief Workbook: Guided Exercises for Loss", 12000, 300, prefix="B0G"),
    book(3, "Grief Journal for Kids", 45000, 60, pub="August 20, 2026", prefix="B0G"),
    book(4, "Healing Grief Journal for Moms", 80000, 20, prefix="B0G"),
    book(5, "A Grief Journal", 25000, 90, prefix="B0G"),
    book(6, "Journal of Loss and Love", 300000, 5, prefix="B0G"),
]
CROWDED = [
    book(i, "Gratitude Journal for Women %d: Daily Prompts" % i, bsr, reviews, prefix="B0C")
    for i, (bsr, reviews) in enumerate([(800, 9000), (2500, 4000), (5000, 2500), (9000, 1200), (20000, 600)], 1)
]


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.ctx = Ctx()
        self.ctx.load(search("prayer journal", PRAYER), search("grief journal", GRIEF),
                      search("gratitude journal for women", CROWDED))

    def test_classify(self):
        layers = concept_layers("grief journal for men", [], self.ctx.lib)
        self.assertIn("for men", [label for _, label, _ in layers])
        self.assertEqual(classify("grief journal for men", layers, "Grief Journal for Men: Prompts"), "direct")
        self.assertEqual(classify("grief journal for men", layers, "Grief Journal for Women"), "non_direct")

    def test_crowded_niche_scores_low_gap(self):
        rep = analyze(self.ctx.conn, self.ctx.cfg, "gratitude journal for women", "amazon.com", self.ctx.lib)
        self.assertEqual(rep.metrics["direct"], 5)
        self.assertGreater(rep.metrics["direct_strength"], 0.9)
        self.assertLess(rep.parts["gap"], 5)
        self.assertNotEqual(rep.verdict, "good")

    def test_layered_concept_with_no_direct_competitor(self):
        rep = analyze(self.ctx.conn, self.ctx.cfg, "grief journal", "amazon.com", self.ctx.lib, ["for men"])
        self.assertEqual(rep.metrics["direct"], 0)
        self.assertEqual(rep.parts["gap"], 35)
        self.assertGreaterEqual(rep.metrics["sellers"], 3)
        self.assertEqual(rep.metrics["new_books"], 1)

    def test_unknown_layer(self):
        with self.assertRaises(ValueError):
            analyze(self.ctx.conn, self.ctx.cfg, "grief journal", "amazon.com", self.ctx.lib, ["for wizards"])

    def test_ideas_transplant_proven_layer(self):
        ideas, _ = generate(self.ctx.conn, self.ctx.cfg, self.ctx.lib, "amazon.com")
        by_concept = {i.concept: i for i in ideas}
        self.assertIn("grief journal for men", by_concept)
        idea = by_concept["grief journal for men"]
        self.assertEqual(idea.status, "estimated")
        self.assertEqual(idea.gap_strength, 0.0)
        self.assertTrue(any("Prayer Journal for Men" in t for t, _, _ in idea.evidence_books))
        # "for kids" is already served inside the grief field: its idea is weaker than "for men"
        kids = by_concept.get("grief journal for kids")
        self.assertTrue(kids is None or kids.score < idea.score)

    def test_capturing_the_layered_search_verifies_the_idea(self):
        self.ctx.load(search("grief journal for men", [
            book(1, "Grief Journal: Prompts for Healing After Loss", 6000, 800, prefix="B0G"),
            book(7, "Grief Recovery for Men: Workbook", 200000, 3, prefix="B0M"),
            book(2, "The Grief Workbook: Guided Exercises for Loss", 12000, 300, prefix="B0G"),
            book(5, "A Grief Journal", 25000, 90, prefix="B0G"),
        ], day="2026-09-02"))
        ideas, _ = generate(self.ctx.conn, self.ctx.cfg, self.ctx.lib, "amazon.com")
        idea = {i.concept: i for i in ideas}["grief journal for men"]
        self.assertEqual(idea.status, "verified")
        self.assertEqual(idea.verified_report.metrics["direct"], 1)
        self.assertIn("re-capture", idea.next_step)

    def test_trademark_caps_score(self):
        self.ctx.load(search("minecraft journal", PRAYER))
        rep = analyze(self.ctx.conn, self.ctx.cfg, "minecraft journal", "amazon.com", self.ctx.lib)
        self.assertLessEqual(rep.score, 30)
        self.assertTrue(any("TRADEMARK" in f for f in rep.flags))

    def test_confidence_grows_with_snapshot_days(self):
        rep = analyze(self.ctx.conn, self.ctx.cfg, "grief journal", "amazon.com", self.ctx.lib)
        self.assertEqual(rep.confidence, "low")
        self.ctx.load(search("grief journal", GRIEF, day="2026-09-03"), search("grief journal", GRIEF, day="2026-09-05"))
        rep = analyze(self.ctx.conn, self.ctx.cfg, "grief journal", "amazon.com", self.ctx.lib)
        self.assertEqual(rep.confidence, "high")

    def test_report_and_next(self):
        actions = report.next_actions(self.ctx.conn, self.ctx.cfg, self.ctx.lib, "amazon.com")
        self.assertTrue(any("grief journal for men" in a for a in actions))
        path = report.write_markdown(self.ctx.conn, self.ctx.cfg, self.ctx.lib, "amazon.com",
                                     os.path.join(self.ctx.dir, "reports"))
        with open(path) as fh:
            text = fh.read()
        self.assertIn("grief journal for men", text)
        self.assertIn("| prayer journal |", text)


class SeedAndAutocompleteTests(unittest.TestCase):
    def test_seeds_from_lists(self):
        ctx = Ctx()
        titles = ["Bird Watching Journal for Beginners", "Bird Watching Log Book", "Dragon Coloring Book",
                  "Bird Watching Journal: Birding Log", "Cozy Dragon Coloring Book for Adults"]
        from datetime import date
        ctx.load({"tool": "kdp-capture", "type": "list", "store": "amazon.com", "url": "https://x/movers",
                  "captured_at": date.today().isoformat() + "T00:00:00Z",
                  "list": {"kind": "movers", "name": "Movers & Shakers in Hobbies"},
                  "items": [{"position": i, "asin": "B0L%07d" % i, "title": t} for i, t in enumerate(titles, 1)]})
        found = [g for g, _, _ in seeds.discover(ctx.conn, "amazon.com")]
        self.assertIn("bird watching journal", found)
        self.assertIn("dragon coloring", found)

    def test_seeds_from_broad_search_sellers(self):
        ctx = Ctx()
        ctx.load(search("gift for women", [
            book(1, "Tell Me Your Story Mom: A Guided Journal", 3000, prefix="B0W"),
            book(2, "Tell Me Your Story Grandma", 9000, prefix="B0W"),
            book(3, "Wine Tasting Journal", 400000, prefix="B0W"),
            book(4, "Wine Tasting Log Book", 500000, prefix="B0W"),
        ]))
        found = [g for g, _, _ in seeds.discover(ctx.conn, "amazon.com", cfg=ctx.cfg)]
        self.assertIn("tell me your story", found)
        self.assertNotIn("wine tasting", found)          # those books don't sell

    def test_batch_and_suggestion_files(self):
        ctx = Ctx()
        cap = search("gift for nurses", [book(1, "Nurse Journal", 20000, prefix="B0N")])
        # A page-2 book that was not opened, only "bought in past month" is known.
        cap["items"].append({"position": 2, "asin": "B0N0000009", "sponsored": False,
                             "title": "Funny Nurse Coloring Book", "reviews": "12 ratings",
                             "bought_text": "300+ bought in past month"})
        ctx.load({"tool": "kdp-capture", "type": "batch", "store": "amazon.com",
                  "captured_at": "2026-09-01T00:00:00Z", "captures": [cap]},
                 {"tool": "kdp-capture", "type": "suggestions", "store": "amazon.com",
                  "captured_at": "2026-09-01T00:00:00Z",
                  "rows": [{"seed": "gift for", "suggestion": "gift for nurses", "position": 3}]})
        from kdpfinder.analysis import search_books
        books = {b.asin: b for b in search_books(ctx.conn, ctx.cfg, "gift for nurses", "amazon.com")}
        self.assertAlmostEqual(books["B0N0000009"].daily, 10.0)
        self.assertEqual(len(ctx.conn.execute("SELECT * FROM suggestions").fetchall()), 1)

    def test_expand_with_fake_fetcher(self):
        ctx = Ctx()
        fake = {"grief journal for": ["grief journal for men", "grief journal for loss of mother"]}
        got = autocomplete.expand(ctx.conn, "Grief Journal", "amazon.com",
                                  fetcher=lambda prefix, store: fake.get(prefix, []), delay=0, log=lambda m: None)
        self.assertEqual(got, ["grief journal for men", "grief journal for loss of mother"])
        self.assertEqual(len(ctx.conn.execute("SELECT * FROM suggestions").fetchall()), 2)

    def test_autocomplete_counts_as_evidence(self):
        ctx = Ctx()
        ctx.load(search("grief journal", GRIEF))
        autocomplete.import_list(ctx.conn, "grief journal", "amazon.com", ["grief journal for nurses"])
        ideas, _ = generate(ctx.conn, ctx.cfg, ctx.lib, "amazon.com")
        idea = {i.concept: i for i in ideas}.get("grief journal for nurses")
        self.assertIsNotNone(idea)
        self.assertEqual(idea.evidence_searches, ["grief journal for nurses"])


if __name__ == "__main__":
    unittest.main()
