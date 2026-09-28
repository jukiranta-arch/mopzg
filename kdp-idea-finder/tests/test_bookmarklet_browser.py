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
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from helpers import Ctx

from kdpfinder import importer
from kdpfinder.analysis import analyze

HERE = os.path.dirname(os.path.abspath(__file__))
CAPTURE_JS = os.path.join(os.path.dirname(HERE), "kdpfinder", "capture.js")
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
<li><span class="a-list-item"><span class="a-text-bold">Customer Reviews:</span> 4.7 out of 5 stars</span></li>
</ul></div>
</body></html>"""

CARD = """<div data-component-type="s-search-result" data-asin="{asin}" class="s-result-item">
{sponsored}<h2 aria-label="{title}" class="a-size-medium"><a href="/dp/{asin}"><span>{title}</span></a></h2>
<a href="/dp/{asin}#customerReviews"><span aria-label="{reviews:,} ratings">{reviews:,}</span></a></div>"""

SPONSORED = '<span class="puis-sponsored-label-text">Sponsored</span>'


def search_page():
    cards = [CARD.format(asin="B0SPONSOR1", title="Sponsored Grief Book", reviews=5, sponsored=SPONSORED)]
    for asin, (title, _, reviews, _, _, _) in BOOKS.items():
        cards.append(CARD.format(asin=asin, title=title, reviews=reviews, sponsored=""))
    return "<!doctype html><html><body><div class='s-main-slot'>%s</div></body></html>" % "".join(cards)


def list_page():
    items = "".join(
        '<div id="gridItemRoot"><span class="zg-bdg-text">#%d</span>'
        '<a href="/Some-Title/dp/%s/ref=zg_bs"><img alt="%s" src="x.jpg"></a>'
        '<a href="/Some-Title/dp/%s/ref=zg_bs"><span><div>%s</div></span></a>'
        '<a href="/product-reviews/%s"><span>%d</span></a></div>'
        % (i, asin, t[0], asin, t[0], asin, t[2]) for i, (asin, t) in enumerate(BOOKS.items(), 1))
    return "<!doctype html><html><body><h1>Best Sellers in Grief &amp; Bereavement</h1>%s</body></html>" % items


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/s":
            body = search_page()
        elif path.startswith("/dp/"):
            b = BOOKS.get(path.split("/")[2])
            if not b:
                self.send_error(404)
                return
            body = PRODUCT.format(title=b[0], rank=b[1], reviews=b[2], price=b[3], publisher=b[4], pages=b[5])
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
        self.assertEqual(len(organic), 3)
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
        self.assertEqual(rep.metrics["field"], 3)
        self.assertEqual(rep.books[0].bsr, 6012)

    def test_product_capture(self):
        cap = self.capture("/dp/B0AAAAAAA3")
        self.assertEqual(cap["type"], "product")
        p = importer.parse_product(cap["product"])
        self.assertEqual((p["asin"], p["bsr"], p["pub_date"]), ("B0AAAAAAA3", 150321, "2026-08-20"))

    def test_list_capture(self):
        cap = self.capture("/gp/bestsellers/books/1234")
        self.assertEqual(cap["type"], "list")
        self.assertEqual(cap["list"]["kind"], "bestsellers")
        self.assertEqual([i["asin"] for i in cap["items"]], list(BOOKS))
        self.assertEqual(cap["items"][0]["title"], BOOKS["B0AAAAAAA1"][0])


if __name__ == "__main__":
    unittest.main()
