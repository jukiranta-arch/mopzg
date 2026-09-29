"""SQLite storage. Snapshots are never overwritten: trajectories are the point."""

import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    asin TEXT NOT NULL,
    store TEXT NOT NULL,
    title TEXT,
    author TEXT,
    format TEXT,
    pages INTEGER,
    pub_date TEXT,
    publisher TEXT,
    indie INTEGER,
    PRIMARY KEY (asin, store)
);
-- taken_at is a date (YYYY-MM-DD): one snapshot per book per day, latest capture wins.
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY,
    asin TEXT NOT NULL,
    store TEXT NOT NULL,
    taken_at TEXT NOT NULL,
    bsr INTEGER,
    bsr_category TEXT,
    category_ranks TEXT,
    price REAL,
    price_currency TEXT,
    bought_month INTEGER,
    reviews INTEGER,
    rating REAL,
    source TEXT,
    UNIQUE (asin, store, taken_at)
);
CREATE TABLE IF NOT EXISTS searches (
    id INTEGER PRIMARY KEY,
    keyword TEXT NOT NULL,
    store TEXT NOT NULL,
    taken_at TEXT NOT NULL,
    url TEXT,
    UNIQUE (keyword, store, taken_at)
);
CREATE TABLE IF NOT EXISTS search_results (
    search_id INTEGER NOT NULL REFERENCES searches(id),
    position INTEGER NOT NULL,
    asin TEXT NOT NULL,
    sponsored INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (search_id, position)
);
CREATE TABLE IF NOT EXISTS lists (
    id INTEGER PRIMARY KEY,
    kind TEXT,
    name TEXT,
    store TEXT NOT NULL,
    taken_at TEXT NOT NULL,
    url TEXT,
    UNIQUE (url, taken_at)
);
CREATE TABLE IF NOT EXISTS list_items (
    list_id INTEGER NOT NULL REFERENCES lists(id),
    rank INTEGER NOT NULL,
    asin TEXT NOT NULL,
    title TEXT,
    reviews INTEGER,
    PRIMARY KEY (list_id, rank)
);
CREATE TABLE IF NOT EXISTS suggestions (
    seed TEXT NOT NULL,
    store TEXT NOT NULL,
    suggestion TEXT NOT NULL,
    taken_at TEXT NOT NULL,
    PRIMARY KEY (seed, store, suggestion)
);
CREATE TABLE IF NOT EXISTS marks (
    keyword TEXT NOT NULL,
    store TEXT NOT NULL,
    asin TEXT NOT NULL,
    relation TEXT NOT NULL CHECK (relation IN ('direct', 'non_direct', 'unrelated')),
    PRIMARY KEY (keyword, store, asin)
);
CREATE TABLE IF NOT EXISTS reviews (
    asin TEXT NOT NULL,
    store TEXT NOT NULL,
    review_key TEXT NOT NULL,         -- Amazon's review id, or a hash of title and text
    stars REAL,
    title TEXT,
    body TEXT,
    review_date TEXT,
    verified INTEGER,
    helpful TEXT,
    source TEXT,                      -- product page, critical, positive
    taken_at TEXT,
    PRIMARY KEY (asin, store, review_key)
);
CREATE TABLE IF NOT EXISTS imports (
    sha256 TEXT PRIMARY KEY,
    path TEXT,
    imported_at TEXT
);
"""


def connect(data_dir):
    os.makedirs(data_dir, exist_ok=True)
    conn = sqlite3.connect(os.path.join(data_dir, "kdp.sqlite"))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(snapshots)")}
    for col, kind in (("price_currency", "TEXT"), ("bought_month", "INTEGER")):
        if col not in cols:                     # databases made by older versions
            conn.execute("ALTER TABLE snapshots ADD COLUMN %s %s" % (col, kind))
    return conn


def niches(conn, store=None):
    """Every (keyword, store) with at least one captured search."""
    sql = "SELECT keyword, store, COUNT(*) AS captures, MAX(taken_at) AS last FROM searches"
    args = ()
    if store:
        sql += " WHERE store = ?"
        args = (store,)
    sql += " GROUP BY keyword, store ORDER BY keyword"
    return conn.execute(sql, args).fetchall()


def latest_search(conn, keyword, store):
    return conn.execute(
        "SELECT * FROM searches WHERE keyword = ? AND store = ? ORDER BY taken_at DESC LIMIT 1",
        (keyword, store)).fetchone()


def search_asins(conn, search_id, limit):
    rows = conn.execute(
        "SELECT asin FROM search_results WHERE search_id = ? AND sponsored = 0 "
        "ORDER BY position LIMIT ?", (search_id, limit)).fetchall()
    return [r["asin"] for r in rows]


def book(conn, asin, store):
    return conn.execute("SELECT * FROM books WHERE asin = ? AND store = ?",
                        (asin, store)).fetchone()


def snapshots(conn, asin, store):
    return conn.execute(
        "SELECT * FROM snapshots WHERE asin = ? AND store = ? ORDER BY taken_at",
        (asin, store)).fetchall()


def marks(conn, keyword, store):
    rows = conn.execute("SELECT asin, relation FROM marks WHERE keyword = ? AND store = ?",
                        (keyword, store)).fetchall()
    return {r["asin"]: r["relation"] for r in rows}


def reviews(conn, store=None, asins=None, max_stars=5):
    """Captured reviews, lowest stars first. store=None reads every Amazon site: the same
    book usually has the same ASIN everywhere, and every site's reviews are useful."""
    sql = ("SELECT r.*, b.title AS book_title FROM reviews r LEFT JOIN books b ON b.asin = r.asin AND b.store = r.store "
           "WHERE (r.stars IS NULL OR r.stars <= ?)")
    args = [max_stars]
    if store:
        sql += " AND r.store = ?"
        args.append(store)
    if asins:
        sql += " AND r.asin IN (%s)" % ",".join("?" * len(asins))
        args += list(asins)
    return conn.execute(sql + " ORDER BY r.asin, r.stars, r.store, r.review_key", args).fetchall()


def suggestions(conn, store):
    return conn.execute("SELECT seed, suggestion FROM suggestions WHERE store = ?",
                        (store,)).fetchall()
