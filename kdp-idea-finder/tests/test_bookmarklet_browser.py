"""Runs the real bookmarklet in headless Chromium against mock Amazon pages.

Skipped when Node or Playwright is missing. The mock pages copy the structure of
Amazon's markup (detail bullets, search result cards, best seller grid); Amazon
changes its markup now and then, so if real captures come back empty, save the
page (Ctrl+S) and add it here as a fixture.
"""

import json
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from helpers import Ctx

from kdpfinder import bookmarklet, importer
from kdpfinder.analysis import analyze

HERE = os.path.dirname(os.path.abspath(__file__))
# The browser runs exactly what the bookmark holds: the minified code decoded from its URL.
_CODE_DIR = tempfile.mkdtemp(prefix="kdp-bm-")
CAPTURE_JS = os.path.join(_CODE_DIR, "bookmarklet.js")
with open(CAPTURE_JS, "w", encoding="utf-8") as _fh:
    _fh.write(urllib.parse.unquote(bookmarklet.url()[len("javascript:"):]))
NODE_MODULES = "/opt/node22/lib/node_modules"

BOOKS = {
    "B0AAAAAAA1": ("Grief Journal: Guided Prompts for Healing After Loss", "#6,012 in Books", 812, "$9.99",
                   "Independently published (March 3, 2024)", 120),
    "B0AAAAAAA2": ("The Grief Workbook for Adults", "#48,700 in Books", 64, "$12.99",
                   "New Harbinger Publications; 1st edition (May 1, 2019)", 208),
    "B0AAAAAAA3": ("Grief Journal for Kids: Draw and Write", "#150,321 in Books", 9, "$7.99",
                   "Independently published (August 20, 2026)", 100),
}

PRODUCT = """<!doctype html><html><body>
<div id="centerCol">
<h1><span id="productTitle"> {title} </span></h1>
<div id="bylineInfo"><span class="author"><a href="#">Jane Writer</a> (Author)</span></div>
<span id="productSubtitle">Paperback &ndash; March 3, 2024</span>
<span id="acrPopover" title="4.7 out of 5 stars"><span class="a-icon-alt">4.7 out of 5 stars</span></span>
<span id="acrCustomerReviewText">{reviews:,} ratings</span>
</div>
<div id="tmmSwatches"><ul><li><span class="a-button a-button-selected"><span class="slot-title">Paperback</span>
<span class="slot-price"><span>{price}</span></span></span></li></ul></div>
<div id="detailBulletsWrapper_feature_div">
<div id="detailBullets_feature_div"><ul class="a-unordered-list">
<li><span class="a-list-item"><span class="a-text-bold">Publisher &rlm; : &lrm;</span> <span>{publisher}</span></span></li>
<li><span class="a-list-item"><span class="a-text-bold">Language &rlm; : &lrm;</span> <span>English</span></span></li>
<li><span class="a-list-item"><span class="a-text-bold">Paperback &rlm; : &lrm;</span> <span>{pages} pages</span></span></li>
<li><span class="a-list-item"><span class="a-text-bold">ISBN-13 &rlm; : &lrm;</span> <span>979-8000000000</span></span></li>
</ul></div>
<ul class="a-unordered-list a-nostyle a-vertical a-spacing-none detail-bullet-list">
<li><span class="a-list-item"><span class="a-text-bold">Best Sellers Rank:</span> {rank} (<a href="#">See Top 100 in Books</a>)
<ul class="a-unordered-list a-nostyle a-vertical zg_hrsr">
<li><span class="a-list-item">#12 in <a href="#">Grief &amp; Bereavement</a></span></li>
<li><span class="a-list-item">#40 in <a href="#">Journal Writing Self-Help</a></span></li>
</ul></span></li>
<li><span class="a-list-item"><span class="a-text-bold">Customer Reviews:</span> 4.7 out of 5 stars
<script>P.when('A', 'ready').execute(function(A) {{ }});</script></span></li>
</ul></div>
</body></html>"""

PAGE2 = {
    "B0AAAAAAA4": ("Grief Journal for Men: Prompts After Losing Dad", "#88,000 in Books", 14, "$10.99",
                   "Independently published (June 1, 2026)", 110),
}
BOOKS.update(PAGE2)

CARD = """<div data-component-type="s-search-result" data-asin="{asin}" class="s-result-item">
{sponsored}<h2 aria-label="{title}" class="a-size-medium"><a href="/dp/{asin}"><span>{title}</span></a></h2>
<a href="/dp/{asin}#customerReviews"><span aria-label="{reviews:,} ratings">{reviews:,}</span></a></div>"""

SPONSORED = '<span class="puis-sponsored-label-text">Sponsored</span>'


def search_page(page=1):
    if page >= 3:
        return "<!doctype html><html><body><div class='s-main-slot'>No results</div></body></html>"
    cards = [CARD.format(asin="B0SPONSOR1", title="Sponsored Grief Book", reviews=5, sponsored=SPONSORED)]
    for asin, (title, _, reviews, _, _, _) in BOOKS.items():
        if (asin in PAGE2) == (page == 2):
            cards.append(CARD.format(asin=asin, title=title, reviews=reviews, sponsored=""))
    return "<!doctype html><html><body><div class='s-main-slot'>%s</div></body></html>" % "".join(cards)


def list_page():
    items = "".join(
        '<div id="gridItemRoot"><span class="zg-bdg-text">#%d</span>'
        '<a href="/Some-Title/dp/%s/ref=zg_bs"><img alt="%s" src="x.jpg"></a>'
        '<a href="/Some-Title/dp/%s/ref=zg_bs"><span><div>%s</div></span></a>'
        '<a href="/product-reviews/%s"><span>%d</span></a></div>'
        % (i, asin, t[0], asin, t[0], asin, t[2]) for i, (asin, t) in enumerate(
            ((a, b) for a, b in BOOKS.items() if a not in PAGE2), 1))
    return "<!doctype html><html><body><h1>Best Sellers in Grief &amp; Bereavement</h1>%s</body></html>" % items


SUGGESTIONS = {
    "gift for": ["gift for", "gift for women", "gift for nurses"],
    "gift for n": ["gift for nurses", "gift for new moms"],
}


def review(rid, stars, title, body, hook="review-star-rating", verified=True):
    return ('<li id="%s" data-hook="review" class="review aok-relative">'
            '<div class="a-profile-content"><span class="a-profile-name">Reader</span></div>'
            '<a data-hook="review-title" class="review-title" href="#"><i data-hook="%s" '
            'class="a-icon a-icon-star a-star-%d review-rating"><span class="a-icon-alt">%d.0 out of 5 stars</span></i>'
            '<span class="a-letter-space"></span><span>%s</span></a>'
            '<span data-hook="review-date">Reviewed in the United States on September 1, 2026</span>%s'
            '<span data-hook="review-body" class="review-text"><span>%s</span></span>'
            '<span data-hook="helpful-vote-statement">12 people found this helpful</span></li>'
            % (rid, hook, stars, stars, title, '<span data-hook="avp-badge">Verified Purchase</span>' if verified else "",
               body))


R1 = review("R1CRIT", 2, "Two names left at the end", "I followed every clue and was left with two names. Clue 7 is ambiguous.")
R2 = review("R2CRIT", 1, "Print too small", "The font is tiny and the names run together.", verified=False)
R3 = review("R3CRIT", 3, "Fun but no story", "The ending was a let-down.")
R4 = review("R4POS", 5, "Addictive", "Took me three weeks with highlighters. Loved it.")
P1 = review("P1PAGE", 4, "Great gift", "Bought it for my mum.", hook="cmps-review-star-rating")
PRODUCT_REVIEWS = {"B0AAAAAAA1": P1 + R1, "B0AAAAAAA2": P1.replace("P1PAGE", "P2PAGE")}


def review_page(asin, star, page):
    if asin != "B0AAAAAAA1":
        return ("<!doctype html><html><body><form name='signIn'><input id='ap_email'></form>"
                "Sign in</body></html>")
    if star == "critical":
        items = [R1, R2] if page == 1 else [R3]
    else:
        items = [R4]
    nxt = ('<li class="a-last"><a href="?pageNumber=%d">Next page</a></li>' % (page + 1) if star == "critical"
           and page == 1 else '<li class="a-disabled a-last">Next page</li>')
    return ("<!doctype html><html><body><div id='cm_cr-review_list'><ul>%s</ul></div>"
            "<ul class='a-pagination'>%s</ul></body></html>" % ("".join(items), nxt))


CAPTCHA = ("<!doctype html><html><body><form action='/errors/validateCaptcha'>"
           "Enter the characters you see below</form></body></html>")


class Handler(BaseHTTPRequestHandler):
    block_once = set()          # search terms that answer with a captcha the first time

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path
        if path == "/api/2017/suggestions":
            prefix = parse_qs(url.query)["prefix"][0]
            data = json.dumps({"suggestions": [{"value": v} for v in SUGGESTIONS.get(prefix, [])]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/":
            body = "<!doctype html><html><body><h1>Amazon front page</h1></body></html>"
        elif path == "/s":
            term = parse_qs(url.query).get("k", [""])[0]
            if term in Handler.block_once:
                Handler.block_once.discard(term)
                body = CAPTCHA
            else:
                body = search_page(int(parse_qs(url.query).get("page", ["1"])[0]))
        elif path.startswith("/spa/dp/"):
            # A page that intercepts every link click, as single-page-app routers do.
            b = BOOKS[path.split("/")[3]]
            body = PRODUCT.format(title=b[0], rank=b[1], reviews=b[2], price=b[3], publisher=b[4], pages=b[5])
            body = body.replace("<body>", "<body><script>document.addEventListener('click', function (e) {"
                                "var a = e.target.closest && e.target.closest('a'); if (a) { e.preventDefault(); }"
                                "}, true);</script>")
        elif path.startswith("/dp/"):
            b = BOOKS.get(path.split("/")[2])
            if not b:
                self.send_error(404)
                return
            body = PRODUCT.format(title=b[0], rank=b[1], reviews=b[2], price=b[3], publisher=b[4], pages=b[5])
            body = body.replace("</body>", PRODUCT_REVIEWS.get(path.split("/")[2], "") + "</body>")
        elif path.startswith("/product-reviews/"):
            q = parse_qs(url.query)
            body = review_page(path.split("/")[2], q.get("filterByStar", ["critical"])[0],
                               int(q.get("pageNumber", ["1"])[0]))
        elif path.startswith("/gp/bestsellers"):
            body = list_page()
        else:
            self.send_error(404)
            return
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def have_playwright():
    return shutil.which("node") and os.path.isdir(os.path.join(NODE_MODULES, "playwright"))


@unittest.skipUnless(have_playwright(), "node + playwright not available")
class BookmarkletBrowserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = "http://127.0.0.1:%d" % cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def capture(self, path):
        env = dict(os.environ, NODE_PATH=NODE_MODULES)
        out = subprocess.run(["node", os.path.join(HERE, "browser", "run_capture.js"), self.base + path, CAPTURE_JS],
                             capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        result = json.loads(out.stdout)
        result["store"] = "amazon.com"         # served from 127.0.0.1 in the test
        return result

    def test_search_capture_end_to_end(self):
        cap = self.capture("/s?k=grief+journal&i=stripbooks")
        self.assertEqual(cap["type"], "search")
        self.assertEqual(cap["keyword"], "grief journal")
        self.assertTrue(cap["items"][0]["sponsored"])
        self.assertNotIn("product", cap["items"][0])           # sponsored books are not opened
        organic = [i for i in cap["items"] if not i["sponsored"]]
        self.assertEqual(cap["pages"], 2)                      # page 3 was empty
        self.assertEqual(len(organic), 4)                      # sponsored repeat on page 2 is deduped
        self.assertEqual([i["position"] for i in cap["items"]], list(range(1, 6)))
        self.assertEqual(importer.parse_product(organic[3]["product"])["bsr"], 88000)
        self.assertNotIn("P.when", json.dumps(organic[0]["product"]["details"]))   # inline scripts stripped
        p = importer.parse_product(organic[0]["product"])
        self.assertEqual(p["title"], BOOKS["B0AAAAAAA1"][0])
        self.assertEqual(p["bsr"], 6012)
        self.assertEqual(p["reviews"], 812)
        self.assertAlmostEqual(p["price"], 9.99)
        self.assertEqual(p["pages"], 120)
        self.assertEqual(p["pub_date"], "2024-03-03")
        self.assertEqual(p["indie"], 1)
        p2 = importer.parse_product(organic[1]["product"])
        self.assertEqual((p2["bsr"], p2["indie"], p2["publisher"]), (48700, 0, "New Harbinger Publications"))
        self.assertEqual(p2["pub_date"], "2019-05-01")

        ctx = Ctx()
        ctx.load(cap)
        rep = analyze(ctx.conn, ctx.cfg, "grief journal", "amazon.com", ctx.lib)
        self.assertEqual(rep.metrics["field"], 4)
        self.assertEqual(rep.books[0].bsr, 6012)

    def test_autopilot_discovers_captures_and_resumes(self):
        Handler.block_once = {"gift for women"}
        env = dict(os.environ, NODE_PATH=NODE_MODULES)
        out = subprocess.run(["node", os.path.join(HERE, "browser", "run_autopilot.js"), self.base, CAPTURE_JS],
                             capture_output=True, text=True, env=env, timeout=90)
        self.assertEqual(out.returncode, 0, out.stderr)
        result = json.loads(out.stdout)
        # "gift for nurses" shows up twice, high in the list: it ranks first.
        self.assertEqual(result["ticked"][0], "gift for nurses")
        self.assertEqual(len(result["ticked"]), 2)
        self.assertEqual(result["ticked"][1], "gift for women")
        first = result["first"]
        # The captcha on the second search stops the run. Nothing downloads by
        # itself; the first search and the autocomplete list are kept in the tab.
        self.assertEqual(first["downloads"], [])
        self.assertEqual([c["keyword"] for c in first["kept"]["captures"]], ["gift for nurses"])
        self.assertEqual(first["kept"]["captures"][0]["books_read"], 4)
        self.assertEqual(len({r["suggestion"] for r in first["kept"]["suggestions"]}), 3)
        self.assertIn("captcha", first["status"])
        self.assertEqual(first["state"]["remaining"], ["gift for women"])
        # Clicking KDP Capture again offers to continue; continuing adds the rest.
        self.assertIn("1 left from your last run", result["resumeText"])
        second = result["second"]
        self.assertEqual(second["downloads"], [])
        self.assertEqual([c["keyword"] for c in second["kept"]["captures"]], ["gift for nurses", "gift for women"])
        self.assertIsNone(second["state"])
        # "Save file" downloads everything kept, as one batch file named with the time.
        self.assertEqual(result["saveAgain"], 1)
        ctx = Ctx()
        batch = {"tool": "kdp-capture", "version": 1, "type": "batch", "store": "amazon.com",
                 "captured_at": "2026-09-28T00:00:00Z", "captures": second["kept"]["captures"],
                 "suggestions": second["kept"]["suggestions"]}
        for c in batch["captures"]:
            c["store"] = "amazon.com"
        importer.import_capture(ctx.conn, batch)
        rep = analyze(ctx.conn, ctx.cfg, "gift for nurses", "amazon.com", ctx.lib)
        self.assertEqual(rep.metrics["field"], 4)
        self.assertEqual(len(ctx.conn.execute("SELECT * FROM suggestions").fetchall()), 3)

    def test_download_survives_pages_that_intercept_link_clicks(self):
        env = dict(os.environ, NODE_PATH=NODE_MODULES)
        out = subprocess.run(["node", os.path.join(HERE, "browser", "run_download.js"),
                              self.base + "/spa/dp/B0AAAAAAA1", CAPTURE_JS],
                             capture_output=True, text=True, env=env, timeout=90)
        self.assertEqual(out.returncode, 0, out.stderr)
        result = json.loads(out.stdout)
        self.assertIsNone(result["auto"])                 # nothing downloads by itself
        self.assertTrue(result["again"].startswith("kdp_capture_product_"), result)
        self.assertEqual(result["copied"]["type"], "product")

    def test_product_capture(self):
        cap = self.capture("/dp/B0AAAAAAA3")
        self.assertEqual(cap["type"], "product")
        p = importer.parse_product(cap["product"])
        self.assertEqual((p["asin"], p["bsr"], p["pub_date"]), ("B0AAAAAAA3", 150321, "2026-08-20"))

    def test_review_page_capture(self):
        cap = self.capture("/product-reviews/B0AAAAAAA1/?filterByStar=critical")
        self.assertEqual((cap["type"], cap["asin"]), ("reviews", "B0AAAAAAA1"))
        self.assertFalse(cap.get("signed_out"))
        by_id = {r["id"]: r for r in cap["reviews"]}
        self.assertEqual(sorted(by_id), ["P1PAGE", "R1CRIT", "R2CRIT", "R3CRIT", "R4POS"])   # R1 twice, kept once
        self.assertEqual(by_id["R1CRIT"]["source"], "product page")
        self.assertEqual(by_id["R3CRIT"]["source"], "critical")                  # followed the Next link
        self.assertEqual(by_id["R4POS"]["source"], "positive")
        self.assertEqual(by_id["R2CRIT"]["stars"], 1)
        self.assertEqual(by_id["P1PAGE"]["stars"], 4)                              # newer star markup
        self.assertEqual(by_id["R2CRIT"]["title"], "Print too small")              # no star text in the title
        self.assertFalse(by_id["R2CRIT"]["verified"])
        self.assertTrue(by_id["R1CRIT"]["verified"])
        self.assertIn("Clue 7 is ambiguous", by_id["R1CRIT"]["body"])
        ctx = Ctx()
        importer.import_capture(ctx.conn, cap)
        importer.import_capture(ctx.conn, cap)                                     # importing twice adds nothing
        from kdpfinder import db
        rows = db.reviews(ctx.conn, "amazon.com", max_stars=3)
        self.assertEqual([r["review_key"] for r in rows], ["R2CRIT", "R1CRIT", "R3CRIT"])
        self.assertEqual(rows[0]["book_title"], BOOKS["B0AAAAAAA1"][0])
        importer.import_capture(ctx.conn, dict(cap, store="amazon.co.uk"))       # same book, UK site
        self.assertEqual(len(db.reviews(ctx.conn, max_stars=3)), 6)                 # every site by default
        self.assertEqual(len(db.reviews(ctx.conn, "amazon.co.uk", max_stars=3)), 3)

    def test_autopilot_captures_reviews_and_reports_signed_out(self):
        env = dict(os.environ, NODE_PATH=NODE_MODULES)
        out = subprocess.run(["node", os.path.join(HERE, "browser", "run_reviews.js"), self.base, CAPTURE_JS,
                              "https://www.amazon.com/Some-Book/dp/B0AAAAAAA1/ref=sr_1_1\nB0AAAAAAA2 and B0AAAAAAA1\nB0NOTSOLD1"],
                             capture_output=True, text=True, env=env, timeout=90)
        self.assertEqual(out.returncode, 0, out.stderr)
        result = json.loads(out.stdout)
        caps = result["kept"]["captures"]
        self.assertEqual([c["asin"] for c in caps], ["B0AAAAAAA1", "B0AAAAAAA2", "B0NOTSOLD1"])   # deduped
        self.assertTrue(caps[2]["not_found"])                                        # not sold here: skipped
        self.assertEqual(caps[2]["reviews"], [])
        self.assertEqual(len(caps[0]["reviews"]), 5)
        self.assertTrue(caps[1]["signed_out"])
        self.assertEqual([r["id"] for r in caps[1]["reviews"]], ["P2PAGE"])         # book-page reviews still kept
        self.assertEqual(len(result["dialogs"]), 1)                                  # told once about signing in
        self.assertIn("reviews of 3 books", result["saved"])
        ctx = Ctx()
        self.assertIn("not sold on", importer.import_capture(ctx.conn, dict(caps[2], store="amazon.co.uk")))

    def test_clicking_the_bookmark_url_runs_it(self):
        href = os.path.join(_CODE_DIR, "href.txt")
        with open(href, "w", encoding="utf-8") as fh:
            fh.write(bookmarklet.url())
        env = dict(os.environ, NODE_PATH=NODE_MODULES)
        out = subprocess.run(["node", os.path.join(HERE, "browser", "run_link.js"), self.base + "/dp/B0AAAAAAA3", href],
                             capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        cap = json.loads(out.stdout)
        self.assertEqual(cap["type"], "product")
        self.assertEqual(importer.parse_product(cap["product"])["bsr"], 150321)

    def test_list_capture(self):
        cap = self.capture("/gp/bestsellers/books/1234")
        self.assertEqual(cap["type"], "list")
        self.assertEqual(cap["list"]["kind"], "bestsellers")
        self.assertEqual([i["asin"] for i in cap["items"]], [a for a in BOOKS if a not in PAGE2])
        self.assertEqual(cap["items"][0]["title"], BOOKS["B0AAAAAAA1"][0])


if __name__ == "__main__":
    unittest.main()
