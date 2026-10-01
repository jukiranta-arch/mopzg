"""Solve a rendered case from the PDF alone, with clue logic written separately
from village/case.py, under the same misreadings. Needs pymupdf.

    python -m village.check_pdf CASE.pdf

Prints the survivors under each reading and whether the check line printed in
the PDF fits exactly one of the names left after all clues but one.
"""

import re
import sys

import pymupdf

LEDGER_SIZE = 12


def read(path):
    doc = pymupdf.open(path)
    pages, chapters, numbers, check = [], [], [], None
    for page in doc:
        spans = [s for b in page.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"]]
        text = " ".join(s["text"] for s in spans)
        m = re.search(r"name has (\d+) letters, and its letters add up to (\d+)", text)
        if m:
            check = (int(m.group(1)), int(m.group(2)))
        if not text.startswith("THE GATE LEDGER"):
            continue
        names = [s for s in spans if abs(s["size"] - LEDGER_SIZE) < 0.01]
        ordered = sorted(names, key=lambda s: (round(s["bbox"][1]), s["bbox"][0]))
        pages.append([w for s in ordered for w in s["text"].split()])
        title = [s["text"] for s in spans if abs(s["size"] - 17) < 0.01]
        if title:
            chapters.append((title[0], len(pages) - 1))
        numbers.append(int([s["text"] for s in spans if abs(s["size"] - 9) < 0.01][-1]))
    return pages, chapters, numbers, check


def solve(pages, chapters, reading):
    flat = [(p, n) for p, names in enumerate(pages) for n in names]
    names = [n for _, n in flat]
    page = [p for p, _ in flat]
    chapter = {}
    for k, (_, start) in enumerate(chapters):
        end = chapters[k + 1][1] if k + 1 < len(chapters) else len(pages)
        for p in range(start, end):
            chapter[p] = k

    def starts(group):
        return [i for i in range(len(names)) if names[i:i + len(group)] == list(group)]

    def vowel(ch):
        return ch in "AEIOU" or (ch == "Y" and reading == "y_vowel")

    beatle_chapters = {chapter[page[i]] for i in starts(["John", "Paul", "George", "Ringo"])}
    pb = page[starts(["Charlotte", "Emily", "Anne"])[0]]
    pm = page[starts(["Meg", "Jo", "Beth", "Amy"])[0]]
    lo, hi = sorted((pb, pm))
    outlaw = {page[i] for i in starts(["Bonnie", "Clyde"])}
    if reading != "outlaw_page_only":
        outlaw = {q for p in outlaw for q in (p - 1, p, p + 1)}
    window = 10 + {"wide": 1, "narrow": -1}.get(reading, 0)
    musk = [i for i, n in enumerate(names) if n in ("Athos", "Porthos", "Aramis")]

    tests = {
        "beatles": lambda i: chapter[page[i]] in beatle_chapters,
        "sisters": lambda i: (lo <= page[i] <= hi) if reading == "inclusive" else (lo < page[i] < hi),
        "outlaws": lambda i: page[i] in outlaw,
        "musketeers": lambda i: any(0 < abs(i - j) <= window for j in musk),
        "ends_vowel": lambda i: vowel(names[i][-1].upper()),
        "even_vowels": lambda i: sum(vowel(ch) for ch in names[i].upper()) % 2 == 0,
        "no_jam": lambda i: not set(names[i].upper()) & set("JAM"),
        "first_a_to_m": lambda i: names[i][0].upper() <= "M",
    }
    return names, page, tests


def main(path):
    pages, chapters, numbers, check = read(path)
    print("%d ledger pages, %d names, chapters %s, check %s" % (
        len(pages), sum(map(len, pages)), [c for c, _ in chapters], check))
    finals, near = set(), set()
    for reading in [None, "y_vowel", "wide", "narrow", "inclusive", "outlaw_page_only"]:
        names, page, tests = solve(pages, chapters, reading)
        alive = [i for i in range(len(names)) if all(t(i) for t in tests.values())]
        print("%-17s survivors: %s" % (reading or "as printed",
                                       ["%s (p.%d)" % (names[i], numbers[page[i]]) for i in alive]))
        finals |= {(page[i], i) for i in alive}
        for skip in tests:
            near |= {i for i in range(len(names)) if all(t(i) for k, t in tests.items() if k != skip)}
    if len(finals) != 1:
        print("FAIL: readings disagree or leave more than one name")
        return 1
    (_, killer), = finals
    sig = lambda n: (len(n), sum(ord(c) - 64 for c in n.upper()))
    names = solve(pages, chapters, None)[0]
    clash = [names[i] for i in near if i != killer and sig(names[i]) == check]
    print("killer:", names[killer], sig(names[killer]), "| check line fits killer:", sig(names[killer]) == check,
          "| near-survivors with the same check:", clash)
    return 0 if sig(names[killer]) == check and not clash else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
