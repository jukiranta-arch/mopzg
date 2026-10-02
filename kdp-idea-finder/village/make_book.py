"""Build, render and check the whole book, and write a QA report.

    python -m village.make_book OUT.pdf [REPORT.md]

1. generate: every case is solved by the generator under every misreading;
2. render the print interior;
3. check: village.check_book re-solves every case from the PDF text alone;
4. write the report: names left after each clue, the answers, print checks.
"""

import contextlib
import io
import sys
import time

from .book import READINGS, generate_valid_book
from .check_book import main as check_pdf
from whodunit.render import LayoutError

from .render_book import render_book


def report(book, info, check_out, seconds):
    lines = ["# QA report: %s" % "Murder in Juniper Falls", "",
             "Generated in %d s (seed %d). Interior: %d pages, 6 x 9 in." % (seconds, book.seed, info["pages"]), "",
             "## Each case", "",
             "| Case | Names | Pages | Clues | Names left after each clue | Answer | Check line |",
             "|---|---|---|---|---|---|---|"]
    for c in list(book.cases) + [book.finale]:
        s = c.stats
        name = c.plan.shop if c.plan else "The Town Meeting"
        lines.append("| %s | %s | %d | %d | %s | %s | %d letters, sum %d |" % (
            name, format(s["total"], ","), s["pages"], len(c.clues), " → ".join(format(n, ",") for n in
                                                                                   s["after_each"]),
            s["killer_name"], c.check[0], c.check[1]))
    lines += ["", "Every case leaves exactly one name under each of %d readings: the rules as printed, plus the "
              "misreadings a solver might make (Y as a vowel; counts of names or pages one too wide or too narrow; "
              "counting the two named pages as \u201cbetween\u201d; forgetting the page before and after; "
              "\u201cboth\u201d taken as \u201ceither\u201d; the wrong facing page; the page after instead of "
              "the page before; \u201cbut not both\u201d ignored; \u201cexactly twice\u201d taken as \u201cat "
              "least twice\u201d)." % len(READINGS), "",
              "Mastermind: %s (the killers' first letters: %s)." % (
                  book.mastermind, ", ".join(c.ledger.flat[c.killer][0] for c in book.cases)), "",
              "## Independent check of the PDF", "", "```", check_out.strip(), "```", ""]
    return "\n".join(lines)


def main(argv):
    out = argv[0]
    t = time.time()
    seed = 1
    while True:                   # a page that overflows when typeset means trying the next seed
        book = generate_valid_book(range(seed, seed + 50))
        try:
            info = render_book(book, out)
            break
        except LayoutError as e:
            print("seed %d: %s; trying the next seed" % (book.seed, e), file=sys.stderr)
            seed = book.seed + 1
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        status = check_pdf(out)
    text = report(book, info, buf.getvalue(), time.time() - t)
    if len(argv) > 1:
        with open(argv[1], "w", encoding="utf-8") as fh:
            fh.write(text)
    print(text)
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
