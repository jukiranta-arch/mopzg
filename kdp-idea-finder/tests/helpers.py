"""Builders for synthetic capture files. All data here is made up for tests."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kdpfinder import config, db, importer, layers  # noqa: E402


def product(asin, title, bsr=None, reviews=0, price=9.99, pages=120,
            pub="March 3, 2024", publisher="Independently published"):
    details = {"Publisher": "%s (%s)" % (publisher, pub), "Language": "English",
               "Paperback": "%d pages" % pages}
    return {
        "asin": asin, "title": title, "author": "A. Author",
        "format_text": "Paperback – %s" % pub,
        "price_text": "$%.2f" % price, "reviews_text": "%s ratings" % format(reviews, ","),
        "rating_text": "4.5 out of 5 stars",
        "ranks_text": ("#%s in Books (See Top 100 in Books) #7 in Journal Writing" % format(bsr, ",")) if bsr else "",
        "details": details,
    }


def search(keyword, books, day="2026-09-01", store="amazon.com", sponsored=()):
    items = []
    for i, b in enumerate(books, 1):
        p = product(**b)
        items.append({"position": i, "asin": p["asin"], "sponsored": p["asin"] in sponsored,
                      "title": p["title"], "product": p})
    return {"tool": "kdp-capture", "version": 1, "type": "search", "store": store,
            "url": "https://www.%s/s?k=%s" % (store, keyword.replace(" ", "+")),
            "captured_at": day + "T10:00:00Z", "keyword": keyword, "items": items}


def book(n, title, bsr, reviews=50, pub="March 3, 2024", publisher="Independently published", prefix="B0T"):
    return {"asin": "%s%07d" % (prefix, n), "title": title, "bsr": bsr, "reviews": reviews,
            "pub": pub, "publisher": publisher}


class Ctx:
    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="kdp-test-")
        self.conn = db.connect(self.dir)
        self.cfg = config.load(self.dir)
        self.lib = layers.library(self.dir)

    def load(self, *captures):
        for c in captures:
            importer.import_capture(self.conn, c)
        self.conn.commit()
