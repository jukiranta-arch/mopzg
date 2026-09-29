"""python -m whodunit sample OUT.pdf  |  python -m whodunit book OUT.pdf"""
import sys

from .generate import BOOK_CLUES, SAMPLE_CLUES, generate_any
from .render import render

PRESETS = {
    "sample": dict(n_pages=10, per_page=(200, 225), n_chapters=3,
                   clue_keys=SAMPLE_CLUES),
    "book": dict(n_pages=150, per_page=(200, 225), n_chapters=10, clue_keys=BOOK_CLUES),
}


def main(argv):
    kind, out = argv[0], argv[1]
    reg, clues, sol = generate_any(range(1, 200), **PRESETS[kind])
    pages = render(reg, clues, sol, out, edition_note="SAMPLE CASE" if kind == "sample" else "")
    print("%s: %s names, %d clues, %d PDF pages -> %s" % (kind, format(sol["total_names"], ","), len(clues), pages, out))
    print("counts:", sol["counts"])
    print("suspects:", sol["suspects"], "killer:", sol["killer"])


if __name__ == "__main__":
    main(sys.argv[1:])
