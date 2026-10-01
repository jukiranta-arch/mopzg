"""One case of the linked-case book, laid out like Who Killed Mr Darcy?
(briefs/2026-09-29_winners-samples.md):

- the ledger is a list of entries separated by dots: first names, full names,
  and famous names hidden among them, unmarked;
- the clues are facts about the two suspects ("Each suspect's name...",
  "Both suspects are within one page of a Robin Hood"), mixing letter clues
  with hunt clues;
- two suspects remain; a final deduction at the back of the book names the
  killer, then a check line confirms it before the solution page.

Every case is solved under READINGS, the plausible misreadings of the rules,
and is only accepted when each of them leaves the same two suspects.
"""

import random
import re
from dataclasses import dataclass, field

from whodunit.names import FIRST, LAST

VOWELS = set("AEIOU")

BEATLES = ("John", "Paul", "George", "Ringo")
MUSKETEERS = ("Athos", "Porthos", "Aramis")
ROBIN = "Robin Hood"
ROMEO, JULIET = "Romeo", "Juliet"
BONNIE, CLYDE = "Bonnie", "Clyde"
# Famous names with no clue of their own, for readers to spot.
EGGS = ["Florence Nightingale", "Charles Dickens", "Jane Austen", "Isaac Newton", "Ada Lovelace",
        "Oliver Twist", "Long John Silver", "Captain Nemo", "Ebenezer Scrooge", "Lady Macbeth"]

# First names and surnames that never appear in ordinary entries, so a landmark can't be confused
# with an ordinary visitor ("Robin Finch" is not Robin Hood; "John Baker" is not a Beatle).
RESERVED_FIRST = {*BEATLES, *MUSKETEERS, "Robin", ROMEO, JULIET, BONNIE, CLYDE}
RESERVED_LAST = {"Hood", "Robin"}
FIRSTS = [n for n in FIRST if n not in RESERVED_FIRST and n.isalpha()]
LASTS = [n for n in LAST if n not in RESERVED_LAST and n.isalpha()]
LANDMARKS = {*BEATLES, *MUSKETEERS, ROBIN, ROMEO, JULIET, BONNIE, CLYDE, *EGGS}

READINGS = [
    {},                          # the rules as printed
    {"y_vowel": True},           # treats Y as a vowel
    {"window": 1},               # "within 10 names" counted one too generously
    {"window": -1},              # ...or one too strictly
    {"between_inclusive": True}, # counts Romeo's and Juliet's own pages as "between"
    {"robin_page_only": True},   # forgets the page before and after a Robin Hood
    {"bonnie_or_clyde": True},   # takes "a Bonnie and a Clyde" as either one
]


def letters(name):
    return re.sub(r"[^A-Za-z]", "", name).upper()


def signature(name):
    """What the check line prints: number of letters, and their sum with A = 1 ... Z = 26."""
    l = letters(name)
    return len(l), sum(ord(c) - 64 for c in l)


@dataclass
class Ledger:
    pages: list                       # each page is a list of entries
    chapters: list                    # (place, first page index)
    first_page_no: int = 1
    flat: list = field(default_factory=list)
    page_of: list = field(default_factory=list)
    chapter_of_page: list = field(default_factory=list)

    def index(self):
        self.flat, self.page_of = [], []
        for p, names in enumerate(self.pages):
            self.flat += names
            self.page_of += [p] * len(names)
        starts = [s for _, s in self.chapters]
        self.chapter_of_page = [max(k for k, s in enumerate(starts) if s <= p) for p in range(len(self.pages))]
        return self

    def page_no(self, p):
        return self.first_page_no + p

    def pages_with(self, name):
        return {self.page_of[i] for i, n in enumerate(self.flat) if n == name}


# ---------------------------------------------------------------- clues

@dataclass
class Clue:
    key: str
    kind: str          # "hunt" or "letter"
    text: str          # the clue, as printed
    explain: str       # how it works, as printed under it
    test: object       # test(ledger, reading) -> list of bools, one per entry


def _vowel(c, reading):
    return c in VOWELS or (c == "Y" and bool(reading.get("y_vowel")))


def word_test(fn):
    return lambda led, reading: [fn(n, reading) for n in led.flat]


def odd_consonants(name, reading):
    return sum(not _vowel(c, reading) for c in letters(name)) % 2 == 1


def ends_consonant(name, reading):
    return not _vowel(letters(name)[-1], reading)


def double_letter(name, reading):
    return any(re.search(r"([a-z])\1", w.lower()) for w in name.split())


def a_to_m(name, reading):
    return letters(name)[0] <= "M"


def near_robin(led, reading):
    pages = led.pages_with(ROBIN)
    if not reading.get("robin_page_only"):
        pages = {q for p in pages for q in (p - 1, p, p + 1)}
    return [p in pages for p in led.page_of]


def not_beatles_chapter(led, reading):
    found = {}
    for i, n in enumerate(led.flat):
        if n in BEATLES:
            found.setdefault(led.chapter_of_page[led.page_of[i]], set()).add(n)
    full = {ch for ch, names in found.items() if len(names) == 4}
    return [led.chapter_of_page[p] not in full for p in led.page_of]


def near_musketeer(n):
    def test(led, reading):
        w = n + reading.get("window", 0)
        out = [False] * len(led.flat)
        for j, name in enumerate(led.flat):
            if name in MUSKETEERS:
                for k in range(max(0, j - w), min(len(out), j + w + 1)):
                    if k != j:
                        out[k] = True
        return out
    return test


def between_romeo_juliet(led, reading):
    (pr,), (pj,) = led.pages_with(ROMEO), led.pages_with(JULIET)
    lo, hi = min(pr, pj), max(pr, pj)
    if reading.get("between_inclusive"):
        return [lo <= p <= hi for p in led.page_of]
    return [lo < p < hi for p in led.page_of]


def bonnie_and_clyde(led, reading):
    b, c = led.pages_with(BONNIE), led.pages_with(CLYDE)
    pages = (b | c) if reading.get("bonnie_or_clyde") else (b & c)
    return [p in pages for p in led.page_of]


WINDOW = 10

CLUES = [
    Clue("odd_consonants", "letter",
         "Each suspect's name has an odd number of consonants.",
         "Count every letter in the whole name that isn't a vowel. Y is always a consonant; the vowels are A, E, "
         "I, O and U.",
         word_test(odd_consonants)),
    Clue("robin", "hunt",
         "Both suspects are within one page of a Robin Hood.",
         "“Within one page” means the page before, the same page, or the page after. Robin Hood "
         "turns up more than once; being within one page of any of his appearances qualifies.",
         near_robin),
    Clue("ends_consonant", "letter",
         "Each suspect's name ends in a consonant.",
         "Look only at the very last letter of the whole name. Y is a consonant.",
         word_test(ends_consonant)),
    Clue("beatles", "hunt",
         "Neither suspect is in a chapter that contains all four Beatles.",
         "Only the first names John, Paul, George and Ringo qualify, exactly as written and on their own "
         "(John Baker is not a Beatle). All four must appear somewhere in the chapter, in any order. More "
         "than one chapter may contain all four.",
         not_beatles_chapter),
    Clue("musketeers", "hunt",
         "Each suspect sits within %d names of a Musketeer." % WINDOW,
         "The Musketeers are Athos, Porthos and Aramis. Count names in normal reading order: the very next "
         "name is 1 away. If a Musketeer is near the top or bottom of a page, the count carries on onto the "
         "previous or next page.",
         near_musketeer(WINDOW)),
    Clue("romeo_juliet", "hunt",
         "Both suspects appear between Romeo's page and Juliet's page.",
         "Romeo and Juliet each appear only once in the ledger. Their own two pages don't count: each "
         "suspect's page falls somewhere in between.",
         between_romeo_juliet),
    Clue("double_letter", "letter",
         "Each suspect's name contains a double letter.",
         "Two of the same letter sitting together in the name, not split by a space. It only needs to appear "
         "once, anywhere in the name.",
         word_test(double_letter)),
    Clue("bonnie_clyde", "hunt",
         "Each suspect's page contains both a Bonnie and a Clyde.",
         "Both names must be on the page, anywhere on it. They don't need to sit together.",
         bonnie_and_clyde),
    Clue("a_to_m", "letter",
         "Each suspect's name begins with a letter from the first half of the alphabet, A to M.",
         "Look only at the very first letter of the name.",
         word_test(a_to_m)),
]
FINAL = ("The killer's name is the longer of the two.",
         "Count the letters in each suspect's whole name. Spaces don't count.")


def solve(led, clues=CLUES, reading=None, skip=None):
    """Indices that pass every clue (except `skip`) under one reading."""
    reading = reading or {}
    alive = [True] * len(led.flat)
    for c in clues:
        if c.key != skip:
            alive = [a and b for a, b in zip(alive, c.test(led, reading))]
    return [i for i, a in enumerate(alive) if a]


def survivors_all_readings(led, clues=CLUES, skip=None):
    out = set()
    for r in READINGS:
        out |= set(solve(led, clues, r, skip))
    return out


# ---------------------------------------------------------------- generation

PLACES = ["The Church Gate", "The Tea Tent", "The Tombola", "The Cake Stall", "The Dog Show Ring",
          "The Bowling Green"]


def _verdicts(name):
    one = Ledger([[name]], [("", 0)]).index()
    return {c.key: {c.test(one, r)[0] for r in READINGS} for c in CLUES if c.kind == "letter"}


def passes_letters(name):
    return all(v == {True} for v in _verdicts(name).values())


def fails_letters(name):
    return any(v == {False} for v in _verdicts(name).values())


def random_entry(rng, full_share=0.45):
    first = rng.choice(FIRSTS)
    return first + " " + rng.choice(LASTS) if rng.random() < full_share else first


@dataclass
class Case:
    ledger: Ledger
    killer: int
    innocent: int
    check: tuple
    stats: dict


def generate(seed=1, n_pages=20, per_page=(222, 232), pages_per_chapter=4, musketeers=70, heading_cost=30):
    rng = random.Random(seed)
    n_ch = n_pages // pages_per_chapter
    chapters = [(PLACES[k], k * pages_per_chapter) for k in range(n_ch)]
    ch_of = [p // pages_per_chapter for p in range(n_pages)]
    pages = [[random_entry(rng) for _ in range(rng.randint(*per_page) - (heading_cost if p % pages_per_chapter == 0 else 0))]
             for p in range(n_pages)]
    taken = [set() for _ in range(n_pages)]

    def put(name, page, near=None):
        names = pages[page]
        free = [k for k in range(1, len(names) - 1) if not ({k - 1, k, k + 1} & taken[page])]
        if near is not None:
            free = [k for k in free if 0 < abs(k - near) <= WINDOW - 2] or free
        k = rng.choice(free)
        names[k] = name
        taken[page].add(k)
        return k

    # Romeo and Juliet: about half the pages strictly between them.
    gap = rng.randint(9, 11)
    lo = rng.randint(0, n_pages - gap - 2)
    pr, pj = (lo, lo + gap + 1) if rng.random() < 0.5 else (lo + gap + 1, lo)
    put(ROMEO, pr)
    put(JULIET, pj)
    inside = list(range(min(pr, pj) + 2, max(pr, pj) - 1))
    # The two suspects: different pages, different chapters, strictly between the lovers.
    for _ in range(100):
        s1, s2 = rng.sample(inside, 2)
        if ch_of[s1] != ch_of[s2] and abs(s1 - s2) >= 3:
            break
    else:
        raise ValueError("no suspect pages (seed %d)" % seed)
    # Beatles: all four in two chapters without a suspect; one to three of them in each other chapter.
    free_chs = [c for c in range(n_ch) if c not in (ch_of[s1], ch_of[s2])]
    full = set(rng.sample(free_chs, 2))
    for ch in range(n_ch):
        chosen = BEATLES if ch in full else rng.sample(BEATLES, rng.randint(1, 3))
        for b in chosen:
            put(b, rng.choice([p for p in range(n_pages) if ch_of[p] == ch]))
    # Robin Hood: on both suspects' pages and one or two others.
    robin_pages = {s1, s2} | set(rng.sample([p for p in range(n_pages) if abs(p - s1) > 2 and abs(p - s2) > 2],
                                            rng.randint(1, 2)))
    for p in robin_pages:
        put(ROBIN, p)
    # Bonnie and Clyde: both on the suspects' pages and on about half the others; one alone on a few more.
    both = {s1, s2} | set(rng.sample(range(n_pages), n_pages // 2 - 2))
    for p in both:
        put(BONNIE, p)
        put(CLYDE, p)
    for p in rng.sample([p for p in range(n_pages) if p not in both], 3):
        put(rng.choice((BONNIE, CLYDE)), p)
    for egg in EGGS:
        put(egg, rng.randrange(n_pages))
    # Suspects, each with a Musketeer close by; then Musketeers everywhere.
    pool = [e for e in {random_entry(rng, 0.8) for _ in range(4000)} if passes_letters(e)]
    pool.sort()
    for _ in range(200):
        a, b = rng.sample(pool, 2)
        if len(letters(a)) - len(letters(b)) >= 2 and not set(a.split()) & set(b.split()):
            killer_name, innocent_name = a, b
            break
    else:
        raise ValueError("no suspect names (seed %d)" % seed)
    order = [(s1, killer_name), (s2, innocent_name)] if rng.random() < 0.5 else [(s1, innocent_name),
                                                                                (s2, killer_name)]
    spots = {}
    for p, name in order:
        k = put(name, p)
        put(rng.choice(MUSKETEERS), p, near=k)
        spots[name] = (p, k)
    for _ in range(musketeers):
        put(rng.choice(MUSKETEERS), rng.randrange(n_pages))

    led = Ledger(pages, chapters).index()
    flat_at = lambda p, k: sum(len(x) for x in pages[:p]) + k
    killer, innocent = flat_at(*spots[killer_name]), flat_at(*spots[innocent_name])
    sig = signature(killer_name)

    # Repair: everyone else who survives gets a name that fails a letter clue under every reading;
    # nobody close to surviving may match the check line.
    failing = sorted({e for e in {random_entry(rng) for _ in range(3000)} if fails_letters(e)})
    for _ in range(20):
        bad = survivors_all_readings(led) - {killer, innocent}
        for c in CLUES:
            bad |= {i for i in survivors_all_readings(led, skip=c.key)
                    if i != killer and signature(led.flat[i]) == sig}
        if not bad:
            break
        for i in bad:
            if led.flat[i] in LANDMARKS:
                raise ValueError("a landmark would need renaming (seed %d)" % seed)
            p = led.page_of[i]
            pages[p][i - sum(len(x) for x in pages[:p])] = rng.choice([n for n in failing if signature(n) != sig])
        led.index()
    else:
        raise ValueError("repair did not settle (seed %d)" % seed)
    return Case(led, killer, innocent, sig, _stats(led, killer, innocent))


def _stats(led, killer, innocent):
    total = len(led.flat)
    return dict(
        total=total, pages=len(led.pages),
        alone={c.key: round(sum(c.test(led, {})) / total, 2) for c in CLUES},
        after_hunt=len(solve(led, [c for c in CLUES if c.kind == "hunt"])),
        finals={k: sorted(solve(led, CLUES, r)) for k, r in enumerate(READINGS)},
        killer=killer, killer_name=led.flat[killer], innocent_name=led.flat[innocent],
        killer_page=led.page_no(led.page_of[killer]))


def validate(case):
    """The spec's rules for a case; returns a list of problems (empty when fine)."""
    led, s, problems = case.ledger, case.stats, []
    pair = sorted([case.killer, case.innocent])
    for r, alive in s["finals"].items():
        if alive != pair:
            problems.append("reading %d leaves %d names" % (r, len(alive)))
    for c in CLUES:
        if c.kind == "hunt" and not 0.25 <= s["alone"][c.key] <= 0.75:
            problems.append("hunt clue %s alone keeps %.0f%%" % (c.key, 100 * s["alone"][c.key]))
        near = survivors_all_readings(led, skip=c.key) - {case.killer}
        if any(signature(led.flat[i]) == case.check for i in near):
            problems.append("check line also fits a near-survivor (skipping %s)" % c.key)
    if not 40 <= s["after_hunt"] <= 300:
        problems.append("%d names left for the letter clues" % s["after_hunt"])
    if len(letters(led.flat[case.killer])) - len(letters(led.flat[case.innocent])) < 2:
        problems.append("final deduction too close")
    return problems


def generate_valid(seeds=range(1, 300), **kw):
    for s in seeds:
        try:
            case = generate(s, **kw)
        except ValueError:
            continue
        if not validate(case):
            case.stats["seed"] = s
            return case
    raise RuntimeError("no valid case in the seeds tried")
