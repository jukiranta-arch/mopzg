"""python -m whodunit sample OUT.pdf  |  python -m whodunit book OUT.pdf"""
import sys

from .generate import BOOK_BALANCE, BOOK_CLUES, SAMPLE_CLUES, generate_any
from .render import render

PRESETS = {
    # A 30-page case that plays like the book: the same balance rules, fewer clues.
    "sample": dict(n_pages=30, per_page=(270, 300), n_chapters=4, n_indoor=2, clue_keys=SAMPLE_CLUES,
                   balance=dict(BOOK_BALANCE, page_level_keep=(0.02, 0.2))),
    "book": dict(n_pages=140, per_page=(270, 300), n_chapters=10, n_indoor=6, clue_keys=BOOK_CLUES,
                 balance=BOOK_BALANCE),
}


def main(argv):
    kind, out = argv[0], argv[1]
    reg, clues, sol = generate_any(range(1, 200), **PRESETS[kind])
    pages = render(reg, clues, sol, out, edition_note="SAMPLE CASE" if kind == "sample" else "")
    print("%s: %s names, %d clues, %d PDF pages -> %s" % (kind, format(sol["total_names"], ","), len(clues), pages, out))
    print("in play after each clue (pages, names):", [(cp["pages"], cp["names"]) for cp in sol["checkpoints"]])
    print("suspects:", sol["suspects"], "killer:", sol["killer"])


if __name__ == "__main__":
    main(sys.argv[1:])
