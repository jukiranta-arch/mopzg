"""Check a rendered book from the PDF alone (needs pymupdf).

    python -m village.check_book BOOK.pdf

It never imports the generator. It reads each case's clues as printed, turns
each sentence into a test with its own code, reads the names from the ledger
pages, solves every case under the same misreadings the generator uses, and
checks that:

- every reading leaves exactly the same one name;
- the check line printed after the ledger fits that name, and no name that
  survives all clues but one also fits it;
- the solutions printed at the back name the same people;
- the PDF is 6 x 9 inches with an even page count and every font embedded.
"""

import re
import sys

import pymupdf

DOT = "·"
NAME_SIZE = 10.5
VOWELS = "AEIOU"
READINGS = [None, "y_vowel", "wide", "narrow", "inclusive", "page_only", "either"]


def letters(n):
    return re.sub("[^A-Z]", "", n.upper())


def split_names(text):
    """'A, B, C and D' -> [A, B, C, D]."""
    text = text.replace(" and ", ", ")
    return [p.strip() for p in text.split(",") if p.strip()]


# ---------------------------------------------------------------- reading the PDF

def spans_of(page):
    return [s for b in page.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"]]


def lines_of(page):
    """Text lines in reading order, each as (text, size, bold)."""
    out = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            text = "".join(s["text"] for s in l["spans"]).strip()
            if text:
                s = l["spans"][0]
                out.append((text, round(s["size"], 1), "Bold" in s["font"], l["bbox"][1]))
    out.sort(key=lambda t: t[3])
    return out


def read_book(path):
    doc = pymupdf.open(path)
    sections, current = [], None
    solutions_text = ""
    for page in doc:
        spans = spans_of(page)
        text = " ".join(s["text"] for s in spans)
        m = re.match(r"\s*CASE (\w+)\s+The (\w+)", text)
        if (m and len(text) < 200) or (text.strip().startswith("THE FINALE") and len(text) < 200):
            current = dict(title=text.strip(), clue_lines=[], pages=[], chapters=[], numbers=[], check=None)
            sections.append(current)
            continue
        if current is None:
            continue
        headings = {s["text"].strip() for s in spans if abs(s["size"] - 16) < 0.01 and "Bold" in s["font"]}
        if headings & {"The Solutions", "The Mastermind"}:
            solutions_text += " " + text
            continue
        if re.search(r"CLUE \d+", text):
            current["clue_lines"] += lines_of(page)
            continue
        body = [s for s in spans if abs(s["size"] - NAME_SIZE) < 0.01 and "Bold" not in s["font"]]
        if sum(s["text"].count(DOT) for s in body) > 50:
            body.sort(key=lambda s: (round(s["bbox"][1]), s["bbox"][0]))
            joined = " ".join(s["text"] for s in body)
            current["pages"].append([" ".join(e.split()) for e in joined.split(DOT) if e.strip()])
            title = [s["text"] for s in spans if abs(s["size"] - 16) < 0.01]
            if title:
                current["chapters"].append((title[0], len(current["pages"]) - 1))
            current["numbers"].append(int([s["text"] for s in spans if abs(s["size"] - 9) < 0.01][-1]))
            continue
        m = re.search(r"name has (\d+) letters, and they add up to (\d+)", text)
        if m:
            current["check"] = (int(m.group(1)), int(m.group(2)))
    meta = dict(pages=doc.page_count, size=(round(doc[0].rect.width), round(doc[0].rect.height)),
                unembedded=sorted({f[3] for p in doc for f in p.get_fonts() if f[1] not in ("ttf", "cff", "type1c",
                                                                                         "opentype")}))
    return sections, solutions_text, meta


def parse_clues(lines):
    """[(clue sentence, explanation)] from the clue pages' lines."""
    clues, cur = [], None
    for text, size, bold, _ in lines:
        if re.fullmatch(r"CLUE \d+", text):
            cur = dict(text="", explain="")
            clues.append(cur)
        elif cur is None:
            continue
        elif bold and size == 10.5 and not cur["explain"]:
            cur["text"] = (cur["text"] + " " + text).strip()
        elif not text.startswith("Example:") and size == 10.0 and "Example" not in cur.get("stop", ""):
            cur["explain"] = (cur["explain"] + " " + text).strip()
        elif text.startswith("Example:"):
            cur["stop"] = "Example"
    return [(c["text"], c["explain"]) for c in clues]


# ---------------------------------------------------------------- turning sentences into tests

def build_tests(clues, pages, chapters, reading, answers):
    names = [n for p in pages for n in p]
    page = [k for k, p in enumerate(pages) for _ in p]
    chapter = {}
    for k, (_, start) in enumerate(chapters):
        end = chapters[k + 1][1] if k + 1 < len(chapters) else len(pages)
        for p in range(start, end):
            chapter[p] = k
    pages_of = lambda who: {page[i] for i, n in enumerate(names) if n == who}
    vow = VOWELS + ("Y" if reading == "y_vowel" else "")
    tests = []
    for text, explain in clues:
        t = None
        m = re.fullmatch(r"The (?:killer|mastermind) is within one page of an? (.+)\.", text)
        if m:
            ps = pages_of(m.group(1))
            if reading != "page_only":
                ps = {q for p in ps for q in (p - 1, p, p + 1)}
            t = lambda i, ps=ps: page[i] in ps
        m = m or None
        if not t and (m := re.fullmatch(r"The killer is not in a chapter that contains all \w+ (.+)\.", text)):
            members = split_names(re.search(r"are [^:]+: (.+?), exactly as written", explain).group(1))
            seen = {}
            for i, n in enumerate(names):
                if n in members:
                    seen.setdefault(chapter[page[i]], set()).add(n)
            full = {ch for ch, s in seen.items() if len(s) == len(members)}
            t = lambda i, full=full: chapter[page[i]] not in full
        if not t and (m := re.fullmatch(r"The killer sits within (\d+) names of an? .+\.", text)):
            members = split_names(re.match(r".+? are (.+?)\. Count", explain).group(1))
            w = int(m.group(1)) + {"wide": 1, "narrow": -1}.get(reading, 0)
            spots = [i for i, n in enumerate(names) if n in members]
            t = lambda i, spots=spots, w=w: any(0 < abs(i - j) <= w for j in spots)
        if not t and (m := re.fullmatch(r"The (?:killer|mastermind) appears between (.+)'s page and (.+)'s page\.",
                                        text)):
            (pa,), (pb,) = pages_of(m.group(1)), pages_of(m.group(2))
            lo, hi = sorted((pa, pb))
            t = (lambda i, lo=lo, hi=hi: lo <= page[i] <= hi) if reading == "inclusive" else \
                (lambda i, lo=lo, hi=hi: lo < page[i] < hi)
        if not t and (m := re.fullmatch(r"The killer's page contains both an? (.+) and an? (.+)\.", text)):
            a, b = pages_of(m.group(1)), pages_of(m.group(2))
            ps = (a | b) if reading == "either" else (a & b)
            t = lambda i, ps=ps: page[i] in ps
        if not t and (m := re.fullmatch(r"The mastermind is not on a page with an? (.+)\.", text)):
            ps = pages_of(m.group(1))
            t = lambda i, ps=ps: page[i] not in ps
        if not t and (m := re.fullmatch(r"The killer's name contains the last letter of the (\w+) killer's name\.",
                                        text)):
            last = letters(answers[m.group(1)])[-1]
            t = lambda i, last=last: last in letters(names[i])
        if not t and text.startswith("The mastermind's first name is spelled by the first letters"):
            first = "".join(answers[k][0] for k in ("bookstore", "bakery", "diner", "inn", "library"))
            first = first[0] + first[1:].lower()
            t = lambda i, first=first: len(names[i].split()) == 2 and names[i].split()[0] == first
        if not t:
            fixed = {
                "The killer's name has an odd number of consonants.":
                    lambda n: sum(c not in vow for c in letters(n)) % 2 == 1,
                "The killer's name has an even number of consonants.":
                    lambda n: sum(c not in vow for c in letters(n)) % 2 == 0,
                "The killer's name ends in a consonant.": lambda n: letters(n)[-1] not in vow,
                "The killer's name ends in a vowel.": lambda n: letters(n)[-1] in vow,
                "The killer's name contains a double letter.":
                    lambda n: any(re.search(r"(.)\1", w.lower()) for w in n.split()),
                "The killer's name has no double letter.":
                    lambda n: not any(re.search(r"(.)\1", w.lower()) for w in n.split()),
                "The killer's name begins with a letter from the first half of the alphabet, A to M.":
                    lambda n: letters(n)[0] <= "M",
                "The killer's name begins with a letter from the second half of the alphabet, N to Z.":
                    lambda n: letters(n)[0] >= "N",
                "The killer's name has an even number of vowels.":
                    lambda n: sum(c in vow for c in letters(n)) % 2 == 0,
                "The killer's name has an odd number of vowels.":
                    lambda n: sum(c in vow for c in letters(n)) % 2 == 1,
                "The killer signed with a first name and a surname.": lambda n: len(n.split()) == 2,
            }
            if text not in fixed:
                raise ValueError("clue not understood: %r" % text)
            fn = fixed[text]
            t = lambda i, fn=fn: fn(names[i])
        tests.append(t)
    return names, page, tests


def sig(n):
    l = letters(n)
    return len(l), sum(ord(c) - 64 for c in l)


def main(path):
    sections, solutions, meta = read_book(path)
    problems, answers = [], {}
    print("%d PDF pages, %s pt; unembedded fonts: %s" % (meta["pages"], meta["size"], meta["unembedded"] or "none"))
    if meta["size"] != (432, 648):
        problems.append("page size is not 6 x 9 inches")
    if meta["pages"] % 2:
        problems.append("odd page count")
    if meta["unembedded"]:
        problems.append("fonts not embedded: %s" % meta["unembedded"])
    for sec in sections:
        key = re.search(r"The (\w+)", sec["title"]).group(1).lower()
        key = "finale" if key == "town" or "FINALE" in sec["title"] else key
        clues = parse_clues(sec["clue_lines"])
        finals, near = set(), set()
        for reading in READINGS:
            names, page, tests = build_tests(clues, sec["pages"], sec["chapters"], reading, answers)
            alive = tuple(i for i in range(len(names)) if all(t(i) for t in tests))
            finals.add(alive)
            for k in range(len(tests)):
                near |= {i for i in range(len(names)) if all(t(i) for j, t in enumerate(tests) if j != k)}
        names = build_tests(clues, sec["pages"], sec["chapters"], None, answers)[0]
        if len(finals) != 1 or len(next(iter(finals))) != 1:
            problems.append("%s: readings disagree or leave %s" % (key, [len(f) for f in finals]))
            print("%-9s %d clues, %d names: FAIL %s" % (key, len(clues), len(names), finals))
            continue
        (who,), = finals
        clash = [names[i] for i in near if i != who and sig(names[i]) == sec["check"]]
        in_solutions = names[who] in solutions
        answers[key] = names[who]
        print("%-9s %2d clues, %5d names on %2d pages: %-20s check %s fits: %s; near-misses that fit: %s; "
              "in solutions: %s" % (key, len(clues), len(names), len(sec["pages"]), names[who], sec["check"],
                                    sig(names[who]) == sec["check"], clash or "none", in_solutions))
        if sig(names[who]) != sec["check"] or clash or not in_solutions:
            problems.append("%s: check line or solution mismatch" % key)
    if len(answers) != 6:
        problems.append("expected 5 cases and a finale, found %d sections" % len(answers))
    print("PROBLEMS: %s" % (problems or "none"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
