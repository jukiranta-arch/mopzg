"""python -m village OUT.pdf: the test case (Case One), checked and rendered."""
import sys

from .case import generate_valid
from .render import render


def main(argv):
    out = argv[0]
    case = generate_valid()
    info = render(case, out)
    s = case.stats
    print("seed %d: %s names on %d pages; suspects %s and %s; killer %s on page %d; check %s; %d PDF pages -> %s" % (
        s["seed"], format(s["total"], ","), s["pages"], s["killer_name"], s["innocent_name"], s["killer_name"],
        s["killer_page"], case.check, info["pages"], out))
    print("each clue alone keeps:", s["alone"], "| left after the hunt clues:", s["after_hunt"])


if __name__ == "__main__":
    main(sys.argv[1:])
