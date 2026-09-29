"""Check a finished whodunit PDF the way a reader would solve it (needs pymupdf).

python -m whodunit.check_pdf BOOK.pdf

It reads the register back from the PDF (italic text = fairy-tale characters), the chapter list from
The Palace page and the rules from the clue cards, then solves the rules with its own code, also under
common slips (Y as a vowel, counting one name too many or too few, including Hansel's and Gretel's own
pages, counting only names that start with King or Queen). Finally it checks that the solution's
"page, line, name" really points at the killer. It shares no code with the generator on purpose.
"""
import bisect
import re
import sys

import pymupdf

doc = pymupdf.open(sys.argv[1] if len(sys.argv) > 1 else "")
INDOOR_WORDS = ("Ballroom", "Staircase", "Kitchens", "Library", "Gallery", "Throne", "Banqueting", "Cellar",
                "Tower", "Mirror Hall")
pages, italic, chapter_of, chapters, clue_rules = {}, set(), {}, [], []
current_ch = None
for pg in doc:
    t = pg.get_text()
    if t.strip().startswith("The Palace"):
        for m in re.finditer(r"(\d+)\.\s+(The [^\n]+)\n(\d+)–(\d+)", t):
            chapters.append((m.group(2).strip(), int(m.group(3)), int(m.group(4))))
    clue_rules += re.findall(r"Rule:\s*\n?(.+?)(?:\n(?:Example|CLUE|CHECKPOINT)|\Z)", t, re.S) if "The Clues" in t else []
    lines = [l for l in t.splitlines() if l.strip()]
    if not lines or not lines[-1].strip().isdigit() or "Rule:" in t:
        continue
    no = int(lines[-1])
    names = []
    all_lines = sorted((ln for blk in pg.get_text("dict")["blocks"] for ln in blk.get("lines", [])),
                       key=lambda ln: (round(ln["bbox"][1]), ln["bbox"][0]))
    first_names_line = next(k for k, ln in enumerate(all_lines)
                            if any("Italic" not in s["font"] and s["size"] < 12 and s["text"].strip()
                                   and "CHAPTER" not in s["text"] for s in ln["spans"]))
    for line in all_lines[first_names_line:]:
            spans = line["spans"]
            for s in spans:
                txt = s["text"].strip()
                if not txt or txt == str(no):
                    continue
                if "Italic" in s["font"]:
                    names.append(txt); italic.add(txt)
                else:
                    names += txt.split()
    pages[no] = names
nums = sorted(pages)
flat = [(no, n) for no in nums for n in pages[no]]
def chap(no):
    return next(c for c in chapters if c[1] <= no <= c[2])
V = set("AEIOU")
def solve(y_vowel=False, window=10, inclusive=False, royal_first=False):
    vow = V | {"Y"} if y_vowel else V
    L = lambda n: re.sub("[^A-Za-z]", "", n).upper()
    wolf = {no for no, n in flat if n == "Big Bad Wolf"}
    hg = sorted(no for no, n in flat if n in ("Hansel", "Gretel"))
    cast_pos = [k for k, (no, n) in enumerate(flat) if n in italic]
    royal = lambda n: (n.split()[0] in ("King", "Queen", "Prince", "Princess")) if royal_first else \
        any(w in ("King", "Queen", "Prince", "Princess") for w in n.split())
    bears_ch = {chap(flat[k][0])[0] for k in range(len(flat) - 2)
                if [flat[k + j][1] for j in range(3)] == ["Papa Bear", "Mama Bear", "Baby Bear"]}
    tests = {
        "room inside the palace": lambda k, no, n: any(w in chap(no)[0] for w in INDOOR_WORDS),
        "Papa Bear": lambda k, no, n: chap(no)[0] in bears_ch,
        "between Hansel": lambda k, no, n: (hg[0] <= no <= hg[1]) if inclusive else (hg[0] < no < hg[1]),
        "Big Bad Wolf": lambda k, no, n: any(abs(no - w) <= 1 for w in wolf),
        "royal guest": lambda k, no, n: any(royal(x) for x in pages[no]),
        "fairy-tale character": lambda k, no, n: any(abs(j - k) <= window and j != k for j in
                                                     cast_pos[max(0, bisect.bisect_left(cast_pos, k - window) - 1):
                                                              bisect.bisect_right(cast_pos, k + window) + 1]),
        "odd number of consonants": lambda k, no, n: sum(ch not in vow for ch in L(n)) % 2 == 1,
        "even number of vowels": lambda k, no, n: sum(ch in vow for ch in L(n)) % 2 == 0,
        "double letter": lambda k, no, n: bool(re.search(r"(.)\1", n.lower().replace(" ", "|"))),
        "end in a consonant": lambda k, no, n: L(n)[-1] not in vow,
        "letter from A to M": lambda k, no, n: L(n)[0] <= "M",
        "first letter of the name printed first": lambda k, no, n: L(pages[no][0])[0] in L(n),
    }
    alive = list(range(len(flat)))
    counts = []
    for rule in clue_rules:
        rule = " ".join(rule.split())
        key = next(k for k in tests if k in rule)
        alive = [k for k in alive if tests[key](k, *flat[k])]
        counts.append(len(alive))
    return [flat[k] for k in alive], counts
print("register pages", len(pages), "names", len(flat), "characters", len(italic), "chapters", len(chapters),
      "clues", len(clue_rules))
alive, counts = solve()
print("printed rules:", counts, alive)
assert len(alive) == 2, "expected exactly two suspects"
for kw in (dict(y_vowel=True), dict(window=11), dict(window=9), dict(inclusive=True), dict(royal_first=True)):
    slipped = solve(**kw)[0]
    print("  slip", kw, "->", slipped)
    assert slipped == alive, "a slip changes the answer"

# --- the solution points at the killer
sol = next(pg for pg in doc if "The Solution" in pg.get_text())
t = " ".join(sol.get_text().split())
m = re.search(r"(\w+) \(the killer\): page (\d+), line (\d+) from the (top|bottom), name (\d+) on the line", t)
name, no, ln, end, at = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4), int(m.group(5))
pg = next(p for p in doc if p.get_text().strip().splitlines()[-1:] == [str(no)] and "Rule:" not in p.get_text())
spans = [sp for b in pg.get_text("dict")["blocks"] for l in b.get("lines", []) for sp in l["spans"]]
first_y = min(sp["bbox"][1] for sp in spans if "Italic" not in sp["font"] and sp["size"] < 12 and sp["text"].strip()
              and "CHAPTER" not in sp["text"] and sp["text"].strip() != str(no))
by_y = {}
for sp in spans:
    tx = sp["text"].strip()
    if not tx or tx == str(no) or sp["bbox"][1] < first_y - 2:
        continue
    by_y.setdefault(round(sp["bbox"][3]), []).append(sp)
rows = []
for y in sorted(by_y):
    row = []
    for sp in sorted(by_y[y], key=lambda sp: sp["bbox"][0]):
        row += [sp["text"].strip()] if "Italic" in sp["font"] else sp["text"].split()
    rows.append(row)
row = rows[ln - 1] if end == "top" else rows[len(rows) - ln]
print("solution says %s: page %d line %d from the %s, name %d -> %r" % (name, no, ln, end, at, row[at - 1]))
assert row[at - 1] == name
print("OK: one answer under every reading, and the solution points at the killer.")
