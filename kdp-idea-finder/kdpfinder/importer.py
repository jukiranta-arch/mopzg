"""Load capture files written by the browser bookmarklet into the database."""

import glob
import hashlib
import json
import os
import re
from datetime import date

from .text import parse_date, parse_float, parse_int

OVERALL_CATEGORIES = ("books", "bucher", "bücher", "livres", "libros", "libri",
                      "kindle store", "kindle-shop", "boutique kindle", "tienda kindle")

_RANK_RE = re.compile(
    r"(?:#|Nr\.?\s?|n\.?\s?[°º]\s?)\s?(\d[\d,.  ]*)\s+(?:in|en|dans)\s+"
    r"(.+?)(?=\s*\((?:See|Siehe|Voir|Ver|Visualizza)|\s*#\d|\s*Nr\.|\s*n\.?\s?[°º]|$)",
    re.IGNORECASE)


class CaptureError(ValueError):
    pass


def parse_ranks(text):
    """'#12,345 in Books (See Top 100 in Books) #7 in Grief' -> [(12345, 'Books'), (7, 'Grief')]."""
    text = re.sub(r"[‎‏]", "", text or "")
    text = re.sub(r"\s+", " ", text)
    ranks = []
    for num, cat in _RANK_RE.findall(text):
        n = parse_int(num)
        if n:
            ranks.append((n, cat.strip(" :")))
    return ranks


def overall_rank(ranks):
    for n, cat in ranks:
        if cat.lower().startswith(OVERALL_CATEGORIES):
            return n, cat
    return ranks[0] if ranks else (None, None)


def _detail(details, *labels):
    """Find a product-detail value by (partial, case-insensitive) label."""
    for key, value in (details or {}).items():
        k = re.sub(r"[^a-z ]", "", key.lower()).strip()
        for label in labels:
            if k.startswith(label):
                return value
    return None


def parse_product(p):
    """Turn the raw fields the bookmarklet grabbed into clean book + snapshot fields."""
    details = {k: re.sub(r"[‎‏]", "", v or "").strip(" :") for k, v in (p.get("details") or {}).items()}
    ranks_text = p.get("ranks_text") or _detail(details, "best sellers rank", "amazon bestseller",
                                                 "classement des meilleures", "clasificacion",
                                                 "posizione nella classifica") or ""
    ranks = parse_ranks(ranks_text)
    bsr, bsr_cat = overall_rank(ranks)

    publisher = _detail(details, "publisher", "verlag", "editeur", "diteur", "editorial", "editore") or ""
    pub_date = parse_date(_detail(details, "publication date", "erscheinungstermin",
                                  "date de publication", "fecha de publicacion", "data di pubblicazione"))
    if not pub_date:
        m = re.search(r"\(([^()]*\d{4}[^()]*)\)", publisher)
        pub_date = parse_date(m.group(1)) if m else None
    if not pub_date:
        pub_date = parse_date(p.get("format_text"))
    publisher_name = re.sub(r"\s*[;(].*$", "", publisher).strip()

    pages = None
    for value in details.values():
        m = re.search(r"(\d+)\s*(?:pages|seiten|pagine|paginas|páginas)\b", value or "", re.IGNORECASE)
        if m:
            pages = int(m.group(1))
            break

    fmt = (p.get("format_text") or "").split("–")[0].split(" - ")[0].strip() or None
    return {
        "asin": p["asin"],
        "title": (p.get("title") or "").strip() or None,
        "author": (p.get("author") or "").strip() or None,
        "format": fmt,
        "pages": pages,
        "pub_date": pub_date,
        "publisher": publisher_name or None,
        "indie": 1 if re.search(r"independently published", publisher, re.IGNORECASE) else 0,
        "bsr": bsr,
        "bsr_category": bsr_cat,
        "category_ranks": json.dumps(ranks),
        "price": parse_float(p.get("price_text")),
        "reviews": parse_int(p.get("reviews_text")) or 0,
        "rating": parse_float(p.get("rating_text")),
    }


def _upsert_book(conn, store, b):
    old = conn.execute("SELECT * FROM books WHERE asin = ? AND store = ?", (b["asin"], store)).fetchone()
    fields = ("title", "author", "format", "pages", "pub_date", "publisher", "indie")
    if old:
        merged = {f: b.get(f) if b.get(f) is not None else old[f] for f in fields}
        conn.execute("UPDATE books SET title=?, author=?, format=?, pages=?, pub_date=?, publisher=?, indie=? "
                     "WHERE asin=? AND store=?", tuple(merged[f] for f in fields) + (b["asin"], store))
    else:
        conn.execute("INSERT INTO books (asin, store, title, author, format, pages, pub_date, publisher, indie) "
                     "VALUES (?,?,?,?,?,?,?,?,?)", (b["asin"], store) + tuple(b.get(f) for f in fields))


def _save_product(conn, store, day, raw, source):
    b = parse_product(raw)
    _upsert_book(conn, store, b)
    if b["bsr"] is None:
        same_day = conn.execute("SELECT bsr FROM snapshots WHERE asin=? AND store=? AND taken_at=?",
                                (b["asin"], store, day)).fetchone()
        if (same_day and same_day["bsr"]) or (not b["reviews"] and b["price"] is None):
            return b    # don't replace a real snapshot with an empty one
    conn.execute(
        "INSERT OR REPLACE INTO snapshots (asin, store, taken_at, bsr, bsr_category, category_ranks, "
        "price, reviews, rating, source) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (b["asin"], store, day, b["bsr"], b["bsr_category"], b["category_ranks"], b["price"],
         b["reviews"], b["rating"], source))
    return b


def import_capture(conn, capture):
    """Import one capture dict. Returns a short summary string."""
    if capture.get("tool") != "kdp-capture":
        raise CaptureError("not a kdp-capture file")
    store = capture.get("store") or "amazon.com"
    day = (capture.get("captured_at") or date.today().isoformat())[:10]
    kind = capture.get("type")

    if kind == "product":
        b = _save_product(conn, store, day, capture["product"], "product")
        return "product %s  BSR %s" % (b["asin"], b["bsr"])

    if kind == "search":
        keyword = (capture.get("keyword") or "").strip().lower()
        if not keyword:
            raise CaptureError("search capture has no keyword")
        old = conn.execute("SELECT id FROM searches WHERE keyword=? AND store=? AND taken_at=?",
                           (keyword, store, day)).fetchone()
        if old:
            conn.execute("DELETE FROM search_results WHERE search_id = ?", (old["id"],))
            search_id = old["id"]
        else:
            search_id = conn.execute("INSERT INTO searches (keyword, store, taken_at, url) VALUES (?,?,?,?)",
                                     (keyword, store, day, capture.get("url"))).lastrowid
        with_bsr = 0
        for item in capture.get("items", []):
            conn.execute("INSERT OR REPLACE INTO search_results (search_id, position, asin, sponsored) "
                         "VALUES (?,?,?,?)", (search_id, item["position"], item["asin"],
                                             1 if item.get("sponsored") else 0))
            product = item.get("product") or {"asin": item["asin"], "title": item.get("title"),
                                              "reviews_text": item.get("reviews")}
            product.setdefault("asin", item["asin"])
            if not product.get("title"):
                product["title"] = item.get("title")
            b = _save_product(conn, store, day, product, "search")
            with_bsr += 1 if b["bsr"] else 0
        return "search '%s' on %s: %d results, %d with BSR" % (
            keyword, store, len(capture.get("items", [])), with_bsr)

    if kind == "list":
        info = capture.get("list") or {}
        old = conn.execute("SELECT id FROM lists WHERE url=? AND taken_at=?",
                           (capture.get("url"), day)).fetchone()
        if old:
            conn.execute("DELETE FROM list_items WHERE list_id = ?", (old["id"],))
            list_id = old["id"]
        else:
            list_id = conn.execute("INSERT INTO lists (kind, name, store, taken_at, url) VALUES (?,?,?,?,?)",
                                   (info.get("kind"), info.get("name"), store, day,
                                    capture.get("url"))).lastrowid
        for item in capture.get("items", []):
            conn.execute("INSERT OR REPLACE INTO list_items (list_id, rank, asin, title, reviews) "
                         "VALUES (?,?,?,?,?)", (list_id, item["position"], item["asin"],
                                               item.get("title"), parse_int(item.get("reviews"))))
            _upsert_book(conn, store, {"asin": item["asin"], "title": item.get("title")})
        return "list '%s' on %s: %d books" % (info.get("name"), store, len(capture.get("items", [])))

    raise CaptureError("unknown capture type %r" % kind)


def import_paths(conn, paths):
    """Import capture files (globs allowed). Already-imported files are skipped."""
    results = []
    files = []
    for p in paths:
        p = os.path.expanduser(p)
        if os.path.isdir(p):
            files.extend(sorted(glob.glob(os.path.join(p, "*.json"))))
        else:
            files.extend(sorted(glob.glob(p)) if any(c in p for c in "*?[") else [p])
    for path in files:
        with open(path, "rb") as fh:
            raw = fh.read()
        digest = hashlib.sha256(raw).hexdigest()
        if conn.execute("SELECT 1 FROM imports WHERE sha256 = ?", (digest,)).fetchone():
            results.append((path, "already imported"))
            continue
        try:
            summary = import_capture(conn, json.loads(raw.decode("utf-8")))
        except (CaptureError, KeyError, json.JSONDecodeError) as exc:
            results.append((path, "skipped: %s" % exc))
            continue
        conn.execute("INSERT INTO imports (sha256, path, imported_at) VALUES (?,?,?)",
                     (digest, path, date.today().isoformat()))
        conn.commit()
        results.append((path, summary))
    return results
