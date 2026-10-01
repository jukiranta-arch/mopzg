"""python -m village OUT.pdf: the test case (Case One), checked and rendered."""
import os
import sys
import tempfile

from .case import generate_valid
from .render import render


def main(argv):
    out = argv[0]
    case = generate_valid()
    with tempfile.TemporaryDirectory() as tmp:     # first pass finds where the ledger starts
        first = render(case, os.path.join(tmp, "dry.pdf"))["first_ledger_page"]
    info = render(case, out, ledger_start=first)
    assert info["first_ledger_page"] == first
    s = case.stats
    print("seed %d: %s names on %d pages, killer %s on page %d, check %s, %d PDF pages -> %s" % (
        s["seed"], format(s["total"], ","), s["pages"], s["killer_name"], case.ledger.page_no(
            case.ledger.page_of[case.killer]), case.check, info["pages"], out))
    print("each clue alone keeps:", s["alone"], "| left after the hunt clues:", s["after_hunt"])


if __name__ == "__main__":
    main(sys.argv[1:])
