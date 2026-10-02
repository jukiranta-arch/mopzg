"""Check a rendered book from the PDF alone (needs pymupdf).

    python -m village.check_book BOOK.pdf

It never imports the generator. It reads each case's clues as printed (the sentence after "Rule:" and the
explanation under it), turns each sentence into a test with its own code, reads the names from the list pages,
solves every case under the same misreadings the generator uses, and checks that:

- every reading leaves exactly the same one name;
- the check line printed after the list fits that name, and no name that survives all clues but one fits it;
- the solutions printed at the back name the same people;
- the PDF is 6 x 9 inches with an even page count and every font embedded.
"""

import re
import sys

import pymupdf

DOT = "·"
NAME_SIZE = 10.5
READINGS = [None, "y_vowel", "wide", "narrow", "inclusive", "page_only", "either", "pages_up", "pages_down",
            "facing_flip", "before_after_flip", "xor_inclusive", "at_least"]
ORDER = ["bookstore", "bakery", "diner", "inn", "library"]


def L(n):
    return re.sub("[^A-Z]", "", n.upper())


def first(n):
    return n.split()[0]


def surname(n):
    p = n.split()
    return p[-1] if len(p) > 1 else ""


def split_names(text):
    return [p.strip() for p in text.replace(" and ", ", ").replace(" or ", ", ").split(",") if p.strip()]


# ---------------------------------------------------------------- reading the PDF

def spans_of(page):
    return [s for b in page.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"]]


def lines_of(page):
    out = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            text = "".join(s["text"] for s in l["spans"]).strip()
            if text:
                s = l["spans"][0]
                out.append((text, round(s["size"], 1), "Bold" in s["font"], "Italic" in s["font"], l["bbox"][1]))
    out.sort(key=lambda t: t[4])
    return out


def read_book(path):
    doc = pymupdf.open(path)
    sections, current, solutions = [], None, ""
    for page in doc:
        spans = spans_of(page)
        text = " ".join(s["text"] for s in spans)
        if len(text) < 200 and (re.match(r"\s*CASE \w+\s+The \w+", text) or text.strip().startswith("THE FINALE")):
            current = dict(title=text.strip(), lines=[], pages=[], chapters=[], numbers=[], check=None)
            sections.append(current)
            continue
        if current is None:
            continue
        heads = {s["text"].strip() for s in spans if abs(s["size"] - 16) < 0.01 and "Bold" in s["font"]}
        if heads & {"The Solutions", "The Mastermind"}:
            solutions += " " + text
            continue
        if re.search(r"CLUE \d+", text):
            current["lines"] += lines_of(page)
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
    fonts = sorted({f[3] for p in doc for f in p.get_fonts() if f[1] not in ("ttf", "cff", "type1c", "opentype")})
    meta = dict(pages=doc.page_count, size=(round(doc[0].rect.width), round(doc[0].rect.height)), unembedded=fonts)
    return sections, solutions, meta


def parse_clues(lines):
    """[(rule, how)] from the clue pages: the bold sentence after "Rule:", and the plain lines under it."""
    clues, cur = [], None
    for text, size, bold, italic, _ in lines:
        if re.match(r"CLUE \d+", text):
            cur = dict(rule="", how="", state="title")
            clues.append(cur)
        elif cur is None:
            continue
        elif bold and text.startswith("Rule:"):
            cur["rule"], cur["state"] = text[5:].strip(), "rule"
        elif bold and cur["state"] == "rule":
            cur["rule"] += " " + text
        elif not bold and not italic and cur["state"] in ("rule", "how"):
            cur["how"] = (cur["how"] + " " + text).strip()
            cur["state"] = "how"
        elif italic and cur["state"] == "how":
            cur["state"] = "example"
    return [(c["rule"], c["how"]) for c in clues]


# ---------------------------------------------------------------- sentences to tests

def build_tests(clues, pages, chapters, numbers, reading, answers):
    names = [n for p in pages for n in p]
    page = [k for k, p in enumerate(pages) for _ in p]
    chapter, bounds = {}, []
    for k, (_, start) in enumerate(chapters):
        end = chapters[k + 1][1] if k + 1 < len(chapters) else len(pages)
        bounds.append((start, end - 1))
        for p in range(start, end):
            chapter[p] = k
    pages_of = lambda who: {page[i] for i, n in enumerate(names) if n == who}
    vow = set("AEIOU") | ({"Y"} if reading == "y_vowel" else set())
    win = {"wide": 1, "narrow": -1}.get(reading, 0)
    pw = {"pages_up": 1, "pages_down": -1}.get(reading, 0)
    part = {"name": lambda n: n, "first name": first, "surname": surname}
    tests = []

    def per_name(fn):
        return lambda i: fn(names[i])

    for rule, how in clues:
        r = rule.replace("mastermind", "killer")
        t = None
        m = re.fullmatch(r"The killer is within one page of an? (.+)\.", r)
        if m:
            ps = pages_of(m.group(1))
            if reading != "page_only":
                ps = {q for p in ps for q in (p - 1, p, p + 1)}
            t = lambda i, ps=ps: page[i] in ps
        elif m := re.fullmatch(r"The killer is within (\d+) pages of (.+)\.", r):
            (q,) = pages_of(m.group(2))
            w = int(m.group(1)) + pw
            t = lambda i, q=q, w=w: abs(page[i] - q) <= w
        elif m := re.fullmatch(r"The killer is more than (\d+) pages away from (.+)\.", r):
            (q,) = pages_of(m.group(2))
            w = int(m.group(1)) + pw
            t = lambda i, q=q, w=w: abs(page[i] - q) > w
        elif m := re.fullmatch(r"The killer is between (.+)'s page and (.+)'s page\.", r):
            (pa,), (pb,) = pages_of(m.group(1)), pages_of(m.group(2))
            lo, hi = sorted((pa, pb))
            t = (lambda i, lo=lo, hi=hi: lo <= page[i] <= hi) if reading == "inclusive" else \
                (lambda i, lo=lo, hi=hi: lo < page[i] < hi)
        elif re.fullmatch(r"The killer is not in a chapter that contains all \w+ .+\.", r):
            members = split_names(re.search(r"are [^:]+: (.+?), exactly as written", how).group(1))
            seen = {}
            for i, n in enumerate(names):
                if n in members:
                    seen.setdefault(chapter[page[i]], set()).add(n)
            full = {ch for ch, s in seen.items() if len(s) == len(members)}
            t = lambda i, full=full: chapter[page[i]] not in full
        elif m := re.fullmatch(r"The killer is in a chapter where (.+) appears exactly twice\.", r):
            counts = {}
            for p in [page[i] for i, n in enumerate(names) if n == m.group(1)]:
                counts[chapter[p]] = counts.get(chapter[p], 0) + 1
            ok = {ch for ch, c in counts.items() if (c >= 2 if reading == "at_least" else c == 2)}
            t = lambda i, ok=ok: chapter[page[i]] in ok
        elif m := re.fullmatch(r"The killer is in a chapter where (.+) appears\.", r):
            chs = {chapter[p] for p in pages_of(m.group(1))}
            t = lambda i, chs=chs: chapter[page[i]] in chs
        elif re.fullmatch(r"The killer is not in a chapter that opens and closes with .+\.", r):
            pairs = re.findall(r"([A-Z][\w ]+?) and ([A-Z][\w ]+?)(?:,| and |\.)",
                               how.split("The pairs are", 1)[1])
            duos = set(pairs)
            bad = {k for k, (s, e) in enumerate(bounds) if (pages[s][0], pages[e][-1]) in duos}
            t = lambda i, bad=bad: chapter[page[i]] not in bad
        elif m := re.fullmatch(r"The killer's page contains both an? (.+) and an? (.+)\.", r):
            a, b = pages_of(m.group(1)), pages_of(m.group(2))
            ps = (a | b) if reading == "either" else (a & b)
            t = lambda i, ps=ps: page[i] in ps
        elif m := re.fullmatch(r"The killer's page contains an? (.+) or an? (.+), but not both\.", r):
            a, b = pages_of(m.group(1)), pages_of(m.group(2))
            ps = (a | b) if reading == "xor_inclusive" else (a ^ b)
            t = lambda i, ps=ps: page[i] in ps
        elif m := re.fullmatch(r"The killer is within (\d+) names of .+\.", r):
            members = split_names(re.match(r".+? are (.+?)\. Count", how).group(1))
            w = int(m.group(1)) + win
            spots = [i for i, n in enumerate(names) if n in members]
            t = lambda i, spots=spots, w=w: any(0 < abs(i - j) <= w for j in spots)
        elif re.fullmatch(r"The page facing the killer's page contains an? (.+)\.", r):
            who = re.fullmatch(r"The page facing the killer's page contains an? (.+)\.", r).group(1)
            ps = pages_of(who)

            def facing(p):
                odd = numbers[p] % 2 == 1
                if reading == "facing_flip":
                    odd = not odd
                return p - 1 if odd else p + 1
            t = lambda i, ps=ps: facing(page[i]) in ps
        elif re.fullmatch(r"The page just before the killer's page contains .+\.", r):
            members = split_names(re.search(r"means (.+?)\.$", how).group(1))
            ps = set().union(*[pages_of(x) for x in members])
            d = -1 if reading == "before_after_flip" else 1
            t = lambda i, ps=ps, d=d: page[i] - d in ps
        elif m := re.fullmatch(r"The killer's page contains none of (.+)\.", r):
            members = split_names(re.search(r"means (.+?)\. Cross", how).group(1))
            ps = set().union(*[pages_of(x) for x in members])
            t = lambda i, ps=ps: page[i] not in ps
        elif r == "The killer is not on the first or last page of a chapter.":
            t = lambda i: bounds[chapter[page[i]]][0] < page[i] < bounds[chapter[page[i]]][1]
        elif r == "The killer is on an even-numbered page.":
            t = lambda i: numbers[page[i]] % 2 == 0
        elif m := re.fullmatch(r"The killer is not on a page with an? (.+)\.", r):
            ps = pages_of(m.group(1))
            t = lambda i, ps=ps: page[i] not in ps
        elif r == "The killer's name contains the first letter of the first name on the killer's page.":
            t = lambda i: L(pages[page[i]][0])[0] in L(names[i])
        elif r == "The killer's first name shares no letter with the first name at the top of the killer's page.":
            t = lambda i: not set(L(first(pages[page[i]][0]))) & set(L(first(names[i])))
        elif r == "The name just before the killer comes earlier in the alphabet than the name just after the killer.":
            t = lambda i: 0 < i < len(names) - 1 and L(names[i - 1]) < L(names[i + 1])
        elif r == "The killer's name begins with the same letter as the last name on the killer's page.":
            t = lambda i: L(names[i])[0] == L(pages[page[i]][-1])[0]
        elif m := re.fullmatch(r"The killer's name contains the last letter of the (\w+) killer's name\.", r):
            ch = L(answers[m.group(1)])[-1]
            t = per_name(lambda n, ch=ch: ch in L(n))
        elif m := re.fullmatch(r"The killer's name contains the first letter of the (\w+) killer's surname\.", r):
            ch = L(surname(answers[m.group(1)]))[0]
            t = per_name(lambda n, ch=ch: ch in L(n))
        elif m := re.fullmatch(r"The killer's first name has as many letters as the (\w+) killer's first name\.", r):
            k = len(L(first(answers[m.group(1)])))
            t = per_name(lambda n, k=k: len(L(first(n))) == k)
        elif m := re.fullmatch(r"The killer's surname shares no letter with the (\w+) killer's first name\.", r):
            used = set(L(first(answers[m.group(1)])))
            t = per_name(lambda n, used=used: bool(surname(n)) and not set(L(surname(n))) & used)
        elif r.startswith("The killer's first name is spelled by the first letters of the five killers"):
            want = "".join(answers[k][0] for k in ORDER)
            want = want[0] + want[1:].lower()
            t = per_name(lambda n, want=want: len(n.split()) == 2 and first(n) == want)
        elif m := re.fullmatch(r"The killer's (name|first name|surname) has an (odd|even) number of (consonants|vowels)\.",
                               r):
            sc, parity, what = m.groups()
            f = part[sc]

            def fn(n, f=f, parity=parity, what=what):
                x = L(f(n))
                if not x:
                    return False
                k = sum((c in vow) == (what == "vowels") for c in x)
                return k % 2 == (1 if parity == "odd" else 0)
            t = per_name(fn)
        elif m := re.fullmatch(r"The killer's (name|first name|surname) ends in a (consonant|vowel)\.", r):
            f, want = part[m.group(1)], m.group(2)
            t = per_name(lambda n, f=f, want=want: bool(L(f(n))) and (L(f(n))[-1] in vow) == (want == "vowel"))
        elif m := re.fullmatch(r"The killer's (name|first name|surname) contains a double letter\.", r):
            f = part[m.group(1)]
            t = per_name(lambda n, f=f: any(re.search(r"(.)\1", w.lower()) for w in f(n).split()))
        elif m := re.fullmatch(r"The killer's (name|first name|surname) has no double letter\.", r):
            f = part[m.group(1)]
            t = per_name(lambda n, f=f: bool(f(n)) and not any(re.search(r"(.)\1", w.lower()) for w in f(n).split()))
        elif r == "The last two letters of the killer's name are in alphabetical order.":
            t = per_name(lambda n: len(L(n)) > 1 and L(n)[-2] < L(n)[-1])
        elif m := re.fullmatch(r"The killer's name contains no (.+)\.", r):
            bad = set(split_names(m.group(1)))
            t = per_name(lambda n, bad=bad: not set(L(n)) & bad)
        elif m := re.fullmatch(r"The killer's name contains an? ([A-Z])\.", r):
            ch = m.group(1)
            t = per_name(lambda n, ch=ch: ch in L(n))
        elif r == "The killer's surname is longer than the killer's first name.":
            t = per_name(lambda n: bool(surname(n)) and len(L(surname(n))) > len(L(first(n))))
        elif m := re.fullmatch(r"The killer's first name has at least (\d+) letters\.", r):
            k = int(m.group(1))
            t = per_name(lambda n, k=k: len(L(first(n))) >= k)
        elif m := re.fullmatch(r"The killer's name has at most (\d+) letters\.", r):
            k = int(m.group(1))
            t = per_name(lambda n, k=k: len(L(n)) <= k)
        elif r == "The first letter of the killer's first name appears again in the killer's surname.":
            t = per_name(lambda n: bool(surname(n)) and L(n)[0] in L(surname(n)))
        elif m := re.fullmatch(r"Some letter appears at least twice in the killer's (name|first name|surname)\.", r):
            f = part[m.group(1)]
            t = per_name(lambda n, f=f: bool(f(n)) and len(set(L(f(n)))) < len(L(f(n))))
        elif r == "No letter appears twice in the killer's name.":
            t = per_name(lambda n: len(set(L(n))) == len(L(n)))
        elif m := re.fullmatch(r"The killer's name has at least (\d+) vowels\.", r):
            k = int(m.group(1))
            t = per_name(lambda n, k=k: sum(c in vow for c in L(n)) >= k)
        elif r == "The killer's surname begins with a consonant.":
            t = per_name(lambda n: bool(surname(n)) and L(surname(n))[0] not in vow)
        elif r.startswith("Two letters that sit side by side in the killer's name are also neighbours"):
            t = per_name(lambda n: any(abs(ord(a) - ord(b)) == 1 for w in n.split() for a, b in zip(L(w), L(w)[1:])))
        elif r == "The killer's name has an even number of letters.":
            t = per_name(lambda n: len(L(n)) % 2 == 0)
        if t is None:
            raise ValueError("clue not understood: %r" % rule)
        tests.append(t)
    return names, page, tests


def sig(n):
    return len(L(n)), sum(ord(c) - 64 for c in L(n))


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
        key = "finale" if "FINALE" in sec["title"] else re.search(r"The (\w+)", sec["title"]).group(1).lower()
        clues = parse_clues(sec["lines"])
        finals, near = set(), set()
        for reading in READINGS:
            names, page, tests = build_tests(clues, sec["pages"], sec["chapters"], sec["numbers"], reading, answers)
            alive = tuple(i for i in range(len(names)) if all(t(i) for t in tests))
            finals.add(alive)
            for k in range(len(tests)):
                near |= {i for i in range(len(names)) if all(t(i) for j, t in enumerate(tests) if j != k)}
        names = build_tests(clues, sec["pages"], sec["chapters"], sec["numbers"], None, answers)[0]
        if len(finals) != 1 or len(next(iter(finals))) != 1:
            problems.append("%s: readings disagree or leave %s names" % (key, sorted(len(f) for f in finals)))
            print("%-9s %d clues: FAIL" % (key, len(clues)))
            continue
        (who,), = finals
        clash = [names[i] for i in near if i != who and sig(names[i]) == sec["check"]]
        answers[key] = names[who]
        ok = sig(names[who]) == sec["check"] and not clash and names[who] in solutions
        print("%-9s %2d clues, %5d names on %2d pages, %4.0f%% different: %-22s check fits: %s; near-misses that "
              "fit: %s; in solutions: %s" % (key, len(clues), len(names), len(sec["pages"]),
                                             100 * len(set(names)) / len(names), names[who],
                                             sig(names[who]) == sec["check"], clash or "none", names[who] in solutions))
        if not ok:
            problems.append("%s: check line or solution mismatch" % key)
    if len(answers) != 6:
        problems.append("expected 5 cases and a finale, solved %d" % len(answers))
    print("PROBLEMS: %s" % (problems or "none"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
