# KDP Idea Finder

Finds Amazon KDP book ideas that have **proven demand** but **weak or no direct competition**.

The method: find a niche where books are already selling (proven demand). Then add a *layer*, meaning a buyer, life situation, format or angle, until nothing in that niche serves the new concept. Only keep layers that are proven to sell elsewhere, either on books in other niches or in what buyers type into Amazon search. The result is an original book with demand behind it.

```
 Best Sellers / Movers & Shakers ──► seeds ──► capture a search ──► niche score
                                                      │
                          other niches' sellers ──►  ideas (base + layer) ──► capture the layered search ──► verified
                          Amazon autocomplete   ──►        ▲                                                  │
                                                           └───────────── kdp next tells you what to do ◄─────┘
```

## Setup (once, about 2 minutes)

You need Python 3.9 or newer and no other packages.

```bash
cd kdp-idea-finder
pip install -e .            # gives you the `kdp` command (or run: python -m kdpfinder ...)
kdp setup                   # creates ~/kdp-data and install_bookmarklet.html
```

Open `~/kdp-data/install_bookmarklet.html` and drag **KDP Capture** to your bookmarks bar.

## The loop (10–20 minutes a day)

1. **`kdp next`** tells you what to do, most valuable first.
2. Do what it says in your normal browser. Open the Amazon page (a Books search, Best Sellers, Movers & Shakers or New Releases) and click **KDP Capture**. On a search page it reads result pages 1–3 and opens up to 60 organic books one at a time, slowly on purpose (about 4 minutes). Then it downloads `kdp_capture_*.json`. Niche scores use the top 16. All pages feed `kdp seeds` and the layer evidence behind `kdp ideas`, so broad searches like `gift for women` work as market scans.
3. **`kdp import`** loads everything in `~/Downloads/kdp_capture_*.json`. Files it has already imported are skipped.
4. **`kdp ideas`** ranks layered concepts. **`kdp report`** writes a markdown shortlist to `~/kdp-data/reports/`.

Capture the same searches again on different days. A score's confidence goes from low (1 day of BSR data) to medium (2) to high (3 or more), because one BSR reading can be a spike.

## Autopilot

Click **KDP Capture** on any other Amazon page, such as the front page, to open the Autopilot panel:

1. **Find what people search.** It asks Amazon autocomplete what follows each starting phrase (`gift for`, `gift for a`, …, `gift for z`, and so on for each phrase). Suggestions listed higher are searched more, so each appearance scores `1 / (1 + position)`. It saves a `kdp_capture_suggestions_*.json` file.
2. **Capture ticked searches.** It captures the top searches one by one (3 result pages and the top 16 books each), pausing a few seconds between pages. It saves a `kdp_capture_batch_*.json` file every 5 searches and stops on a captcha.

It rests 15–30 seconds between searches. If a captcha stops it, the panel remembers the searches left and shows a countdown (60 minutes; `window.KDP_COOLDOWN_MIN` changes it). Then **Continue where it left off** picks up from the interrupted search. **Capture the phrases in the box directly** skips discovery and captures the lines typed into the box.

Books on pages 2–3 aren't opened. Amazon's "N+ bought in past month" label, where shown, is used as their sales estimate (a lower bound).

## Commands

| command | what it does |
|---|---|
| `kdp next` | the to-do list: which searches to capture, what to re-check, which ideas are ready |
| `kdp import [files]` | import captures (default `~/Downloads/kdp_capture_*.json`) |
| `kdp niches` | every captured niche with its score |
| `kdp analyze "grief journal"` | full breakdown of one niche, book by book |
| `kdp analyze "grief journal" --layer "for men"` | quick estimate for a layered concept from the base search |
| `kdp ideas [--top 15] [--unproven]` | layered ideas on proven demand, best first |
| `kdp seeds` | base niches that keep showing up in the lists you captured |
| `kdp expand "grief journal"` | Amazon autocomplete for a seed: what buyers type after it (about 30 slow requests) |
| `kdp expand "grief journal" --paste file.txt` | same, from suggestions you copied by hand |
| `kdp mark "grief journal" B0XXXXXXXX direct` | override direct / non_direct / unrelated for a book |
| `kdp layers` | the layer library |
| `kdp report` | markdown shortlist |

Global options are `--store amazon.co.uk` (or `KDP_STORE`) and `--data DIR` (or `KDP_DATA`).

## How a niche is scored (0–100)

**Field:** the first 16 organic results of the niche's search. Sponsored results are ignored.

**Selling:** a book sells when its estimated sales are at least 1 copy a day. On amazon.com that's roughly BSR 100k or better. Estimates come from a BSR-to-sales curve in `config.py`.

**Direct competitor:** the title covers the concept's keyword *and* every layer the concept adds. It has the same buyer, problem and format. Everything else in the field is non-direct: it proves demand, but it's not the same book.

| part | max | what earns points |
|---|---|---|
| demand | 35 | median daily sales of the top 5 books (0.3/day scores 0, 20/day scores full), and at least 3 sellers |
| gap | 35 | no direct competitor scores full. Direct books that sell well and have many reviews take points away |
| beatability | 15 | sellers with under 100 reviews, indie-published sellers, and sellers under 6 months old (newcomers can rank) |
| durability | 15 | minus 7 for a copycat wave (many books under 60 days old), minus 5 for a trademark word (score capped at 30), minus 3 for a health topic |

A score of 70 or more is **good**, 50–69 is **average**, and below 50 is **skip**.

**Idea score:** base demand × layer evidence × (1 − how well the base field already serves the layer). A new *buyer* or *situation* counts in full. A *format* tweak on a crowded base is a thin layer and is discounted. Once you capture the layered search itself, the idea shows as **verified** and uses that search's real score.

## Tuning and calibrating

Every number is an estimate until you check it against real sales. Put overrides in `~/kdp-data/config.json`. Keys you don't set keep their defaults:

```json
{
  "bsr_anchors": [[1000, 60], [10000, 10], [100000, 1.0], [1000000, 0.05]],
  "store_multiplier": {"amazon.co.uk": 0.3},
  "selling_daily": 0.5
}
```

Once a month, compare the predictions with your KDP royalty report and adjust `bsr_anchors`. The KDP royalty rules (the 60%/50% price threshold and print costs) are in `config.py`. **Check them against KDP's current pricing page.** They change.

Add your own layers in `~/kdp-data/layers.json`. `kdp expand` lists the autocomplete phrases that no existing layer matches, which makes it a good source of new layers:

```json
{"buyer": {"for widows": "widows?|widowed"},
 "format": {"pocket size": ["pocket|travel size", "pocket {}"]}}
```

## Honest limits

- **Sales are estimates.** BSR is a snapshot ranking, not a sales count. Treat sales as a range until your own royalty reports calibrate them.
- **Direct vs non-direct is matched on titles.** Titles with synonyms or unusual wording can be misclassified. Check the book list in `kdp analyze` and fix mistakes with `kdp mark`.
- **Amazon changes its page markup.** If a capture comes back with no BSRs, save that Amazon page (Ctrl+S). Its structure can then be added to `tests/test_bookmarklet_browser.py` and the parser fixed.
- **Human pace, your own browser.** The bookmarklet reads pages you could open yourself, with a 2.5–5 second gap between pages, and stops if Amazon shows a captcha. It never touches your KDP account. Don't run it in loops.
- **Trademarks, health claims, KDP content rules:** the tool flags common trademark and health words. Clearing a title is still your job.

## Tests

```bash
python -m unittest discover -s tests
```

The browser test runs the real bookmarklet in headless Chromium against mock Amazon pages. It needs Node with Playwright and is skipped otherwise.
