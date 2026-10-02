"""Solve a rendered case from the PDF alone, with clue logic written separately
from village/case.py, under the same misreadings. Needs pymupdf.

    python -m village.check_pdf CASE.pdf

Prints the survivors under each reading, and whether the check line printed in
the PDF fits the killer and no near-survivor.
"""

import re
import sys

import pymupdf

DOT = "·"
LEDGER_SIZE = 10.5


def read(path):
    doc = pymupdf.open(path)
    pages, chapters, numbers, check = [], [], [], None
    for page in doc:
        spans = [s for b in page.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"]]
        text = " ".join(s["text"] for s in spans)
        m = re.search(r"name has (\d+) letters, and they add up to (\d+)", text)
        if m:
            check = (int(m.group(1)), int(m.group(2)))
        body = [s for s in spans if abs(s["size"] - LEDGER_SIZE) < 0.01]
        if sum(s["text"].count(DOT) for s in body) < 50:
            continue
        body.sort(key=lambda s: (round(s["bbox"][1]), s["bbox"][0]))
        joined = " ".join(s["text"] for s in body)
        pages.append([" ".join(e.split()) for e in joined.split(DOT) if e.strip()])
        title = [s["text"] for s in spans if abs(s["size"] - 16) < 0.01]
        if title:
            chapters.append((title[0], len(pages) - 1))
        numbers.append(int([s["text"] for s in spans if abs(s["size"] - 9) < 0.01][-1]))
    return pages, chapters, numbers, check


def tests_for(pages, chapters, reading):
    names = [n for p in pages for n in p]
    page = [k for k, p in enumerate(pages) for _ in p]
    chapter = {}
    for k, (_, start) in enumerate(chapters):
        end = chapters[k + 1][1] if k + 1 < len(chapters) else len(pages)
        for p in range(start, end):
            chapter[p] = k
    pages_of = lambda who: {page[i] for i, n in enumerate(names) if n == who}
    vowels = "AEIOUY" if reading == "y_vowel" else "AEIOU"
    letters = lambda n: re.sub("[^A-Z]", "", n.upper())

    tom = pages_of("Tom Sawyer")
    if reading != "tom_page_only":
        tom = {q for p in tom for q in (p - 1, p, p + 1)}
    seen = {}
    for i, n in enumerate(names):
        if n in ("Meg", "Jo", "Beth", "Amy"):
            seen.setdefault(chapter[page[i]], set()).add(n)
    march = {ch for ch, s in seen.items() if len(s) == 4}
    window = 10 + {"wide": 1, "narrow": -1}.get(reading, 0)
    musk = [i for i, n in enumerate(names) if n in ("Athos", "Porthos", "Aramis")]
    (pr,), (pj,) = pages_of("Romeo"), pages_of("Juliet")
    lo, hi = sorted((pr, pj))
    a, g = pages_of("Anne Shirley"), pages_of("Gilbert Blythe")
    ag = (a | g) if reading == "either" else (a & g)

    tests = {
        "odd_consonants": lambda i: sum(c not in vowels for c in letters(names[i])) % 2 == 1,
        "tom": lambda i: page[i] in tom,
        "ends_consonant": lambda i: letters(names[i])[-1] not in vowels,
        "march": lambda i: chapter[page[i]] not in march,
        "musketeers": lambda i: any(0 < abs(i - j) <= window for j in musk),
        "romeo_juliet": lambda i: (lo <= page[i] <= hi) if reading == "inclusive" else (lo < page[i] < hi),
        "double_letter": lambda i: any(re.search(r"(.)\1", w.lower()) for w in names[i].split()),
        "anne_gilbert": lambda i: page[i] in ag,
        "a_to_m": lambda i: letters(names[i])[0] <= "M",
    }
    return names, page, tests


def main(path):
    pages, chapters, numbers, check = read(path)
    print("%d ledger pages, %d names, chapters %s, check %s" % (
        len(pages), sum(map(len, pages)), [c for c, _ in chapters], check))
    finals, near = set(), set()
    for reading in [None, "y_vowel", "wide", "narrow", "inclusive", "tom_page_only", "either"]:
        names, page, tests = tests_for(pages, chapters, reading)
        alive = [i for i in range(len(names)) if all(t(i) for t in tests.values())]
        print("%-16s %s" % (reading or "as printed", ["%s (p.%d)" % (names[i], numbers[page[i]]) for i in alive]))
        finals.add(tuple(alive))
        for skip in tests:
            near |= {i for i in range(len(names)) if all(t(i) for k, t in tests.items() if k != skip)}
    if len(finals) != 1 or len(next(iter(finals))) != 1:
        print("FAIL: the readings disagree, or don't leave exactly one name")
        return 1
    names = tests_for(pages, chapters, None)[0]
    (killer,), = finals
    sig = lambda n: (len(re.sub("[^A-Z]", "", n.upper())), sum(ord(c) - 64 for c in re.sub("[^A-Z]", "", n.upper())))
    clash = [names[i] for i in near if i != killer and sig(names[i]) == check]
    print("killer: %s %s | check fits killer: %s | other near-survivors that fit: %s" % (
        names[killer], sig(names[killer]), sig(names[killer]) == check, clash))
    return 0 if sig(names[killer]) == check and not clash else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
