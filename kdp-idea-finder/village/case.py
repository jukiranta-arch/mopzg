"""One case of the linked-case book (spec: briefs/2026-10-01_spec-linked-cases.md).

A case is a gate ledger: first names in reading order, split into pages and
chapters (places at the event). Famous groups stand among the ordinary names
as landmarks to hunt for; they are printed like every other name.

Clues come in two kinds:
- hunt clues, about where a guest stands (a chapter, a page range, a page,
  a distance in names from a landmark);
- letter clues, about the name itself, meant for the few hundred names left.

After the last clue comes the check line: the killer's name length and letter
sum (A = 1 ... Z = 26). The generator makes sure it confirms only the killer:
no other guest who survives all the clues, or all but one of them, under any
of READINGS, has the same length and sum.
"""

import random
from dataclasses import dataclass, field

from whodunit.model import letters
from whodunit.names import FIRST

VOWELS = set("AEIOU")

BEATLES = ("John", "Paul", "George", "Ringo")
BRONTES = ("Charlotte", "Emily", "Anne")
MARCH = ("Meg", "Jo", "Beth", "Amy")
OUTLAWS = ("Bonnie", "Clyde")
MUSKETEERS = ("Athos", "Porthos", "Aramis")
EGGS = (("Orville", "Wilbur"), ("Caspar", "Melchior", "Balthazar"), ("Romeo", "Juliet"))

# Names that appear only as part of a landmark, so a lone one can never be mistaken for it.
RESERVED = {"Ringo", "Charlotte", "Meg", "Jo", "Bonnie", "Clyde", *MUSKETEERS,
            "Orville", "Wilbur", "Caspar", "Melchior", "Balthazar", "Romeo", "Juliet"}
FILLER = [n for n in FIRST if n not in RESERVED and n.isalpha()]

# Plausible misreadings; every case must give the same answer under each of them.
READINGS = [
    {},                          # the rules as printed
    {"y_vowel": True},           # treats Y as a vowel
    {"window": 1},               # "within 10 names" counted one too generously
    {"window": -1},              # ...or one too strictly
    {"between_inclusive": True}, # counts the two sisters' own pages as "between"
    {"outlaw_page_only": True},  # forgets "or the page just before or after"
]


def signature(name):
    """What the check line prints: number of letters, and their sum with A = 1 ... Z = 26."""
    l = letters(name)
    return len(l), sum(ord(c) - 64 for c in l)


@dataclass
class Ledger:
    pages: list                       # each page is a list of names
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

    def runs(self, group):
        """Flat indices where the group starts, standing together in reading order."""
        n = len(group)
        return [i for i in range(len(self.flat) - n + 1) if tuple(self.flat[i:i + n]) == tuple(group)]


# ---------------------------------------------------------------- clues

@dataclass
class Clue:
    key: str
    kind: str          # "hunt" or "letter"
    rule: str          # the plain rule, as printed
    witness: str       # the story line before it
    example: str       # how to apply it
    test: object       # test(ledger, i, reading) -> bool, for every flat index at once via prepare()


def _is_vowel(c, reading):
    return c in VOWELS or (c == "Y" and bool(reading.get("y_vowel")))


def word_test(fn):
    def test(led, reading):
        return [fn(n, reading) for n in led.flat]
    return test


def ends_vowel(name, reading):
    return _is_vowel(letters(name)[-1], reading)


def even_vowels(name, reading):
    return sum(_is_vowel(c, reading) for c in letters(name)) % 2 == 0


def no_jam(name, reading):
    return not set(letters(name)) & set("JAM")


def first_a_to_m(name, reading):
    return letters(name)[0] <= "M"


def beatles_chapter(led, reading):
    chs = {led.chapter_of_page[led.page_of[i]] for i in led.runs(BEATLES)}
    return [led.chapter_of_page[p] in chs for p in led.page_of]


def between_sisters(led, reading):
    pb = led.page_of[led.runs(BRONTES)[0]]
    pm = led.page_of[led.runs(MARCH)[0]]
    lo, hi = min(pb, pm), max(pb, pm)
    if reading.get("between_inclusive"):
        return [lo <= p <= hi for p in led.page_of]
    return [lo < p < hi for p in led.page_of]


def outlaws_near(led, reading):
    pages = {led.page_of[i] for i in led.runs(OUTLAWS)}
    if not reading.get("outlaw_page_only"):
        pages |= {p + d for p in pages for d in (-1, 1)}
    return [p in pages for p in led.page_of]


def musketeer_within(n):
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


WINDOW = 10

CLUES = [
    Clue("beatles", "hunt",
         "Keep only guests in a chapter where John, Paul, George and Ringo stand together, in that order.",
         "The skiffle band played Beatles songs all afternoon, and four of the audience sang along to every one. "
         "They never left the side of whoever did it.",
         "The four names stand one straight after another, in reading order. The group may run on to the next "
         "line or page. Cross out every chapter where they don't stand together.",
         beatles_chapter),
    Clue("sisters", "hunt",
         "Keep only guests on the pages between the Brontë sisters' page and the March sisters' page.",
         "Mrs Pettigrew of the book stall saw the killer between two lots of sisters: Charlotte, Emily and Anne "
         "came for the poetry, and Meg, Jo, Beth and Amy for the novels.",
         "Charlotte, Emily and Anne stand together once in the ledger; Meg, Jo, Beth and Amy stand together once. "
         "Find both pages. Only the pages between them count, not the two sisters' pages themselves.",
         between_sisters),
    Clue("outlaws", "hunt",
         "Keep only guests on a page where Bonnie and Clyde stand side by side, or on the page just before or "
         "just after one.",
         "Two guests in matching hats kept slipping past the gate without paying. The constable never caught them, "
         "but the killer was never far from where they had just been.",
         "Bonnie and Clyde turn up more than once, always as a pair. Mark every page they share, then the page "
         "either side of each one.",
         outlaws_near),
    Clue("musketeers", "hunt",
         "Keep only guests at most %d names away from a Musketeer: Athos, Porthos or Aramis." % WINDOW,
         "The fencing club gave displays all day. Their three swordsmen took the names of the Musketeers, and "
         "the killer was standing close to one of them when the bell rang.",
         "The Musketeers are scattered through the ledger, one at a time. Count in reading order: the very next "
         "name is 1 away, and the count carries on across lines and pages. Crossed-out names still count. "
         "Highlight the %d names either side of each Musketeer." % WINDOW,
         musketeer_within(WINDOW)),
    Clue("ends_vowel", "letter",
         "Keep only names that end in a vowel.",
         "The vicar heard the killer's name called across the tea tent. It ended softly, he said: on an open "
         "sound, not a hard one.",
         "Look only at the last letter. The vowels are A, E, I, O and U. Y is not a vowel.",
         word_test(ends_vowel)),
    Clue("even_vowels", "letter",
         "Keep only names with an even number of vowels.",
         "The raffle stub in the victim's hand had the killer's name half-torn away. The vowels that survived "
         "came in pairs.",
         "Count every A, E, I, O and U. Y is not a vowel. A name with no vowels has an even number (none).",
         word_test(even_vowels)),
    Clue("no_jam", "letter",
         "Keep only names with none of the letters J, A or M.",
         "The jam judge, who notices everything, swore the killer's name tag had none of the letters of her "
         "favourite word on it.",
         "Cross out every name that has a J, an A or an M anywhere in it.",
         word_test(no_jam)),
    Clue("first_a_to_m", "letter",
         "Keep only names that begin with a letter from A to M.",
         "The gate ledger was kept in two books, A to M and N to Z. The killer signed the first.",
         "Look only at the first letter.",
         word_test(first_a_to_m)),
]
HUNT_KEYS = [c.key for c in CLUES if c.kind == "hunt"]


def solve(led, clues=CLUES, reading=None, skip=None):
    """Flat indices passing every clue (except `skip`) under one reading."""
    reading = reading or {}
    alive = [True] * len(led.flat)
    for c in clues:
        if c.key == skip:
            continue
        ok = c.test(led, reading)
        alive = [a and b for a, b in zip(alive, ok)]
    return [i for i, a in enumerate(alive) if a]


def survivors_all_readings(led, clues=CLUES, skip=None):
    out = set()
    for r in READINGS:
        out |= set(solve(led, clues, r, skip))
    return out


# ---------------------------------------------------------------- generation

PLACES = ["The Tea Tent", "The Tombola", "The Cake Stall", "The Dog Show Ring", "The Bowling Green"]


def _letter_verdicts(name):
    """For each letter clue, the set of verdicts across all readings."""
    return {c.key: {c.test(Ledger([[name]], [("", 0)]).index(), r)[0] for r in READINGS}
            for c in CLUES if c.kind == "letter"}


def _passes_letters_everywhere(name):
    return all(v == {True} for v in _letter_verdicts(name).values())


def _fails_letters_everywhere(name):
    return any(v == {False} for v in _letter_verdicts(name).values())


@dataclass
class Case:
    ledger: Ledger
    killer: int
    check: tuple
    stats: dict


def generate(seed=1, n_pages=20, per_page=(225, 240), pages_per_chapter=4, musketeers=70):
    rng = random.Random(seed)
    n_ch = n_pages // pages_per_chapter
    places = PLACES[:n_ch]
    chapters = [(places[k], k * pages_per_chapter) for k in range(n_ch)]
    pages = [[rng.choice(FILLER) for _ in range(rng.randint(*per_page))] for _ in range(n_pages)]
    ch_of = [p // pages_per_chapter for p in range(n_pages)]
    taken = [set() for _ in range(n_pages)]     # positions on a page already used by landmarks

    def put(group, page, at=None):
        names = pages[page]
        span = len(group)
        free = [k for k in range(2, len(names) - span - 2)
                if not any(k + d in taken[page] for d in range(-2, span + 2))]
        k = at if at is not None else rng.choice(free)
        names[k:k + span] = list(group)
        taken[page] |= set(range(k, k + span))
        return k

    # Sisters: about half the pages strictly between them.
    gap = rng.randint(9, 11)
    lo = rng.randint(1, n_pages - gap - 2)
    pb, pm = (lo, lo + gap + 1) if rng.random() < 0.5 else (lo + gap + 1, lo)
    put(BRONTES, pb)
    put(MARCH, pm)
    # The killer's page: strictly between the sisters, at least two pages from either.
    kp = rng.choice(range(min(pb, pm) + 2, max(pb, pm) - 1))
    # Beatles: once in the killer's chapter and once in one other, so the chapter clue keeps 2 of 5.
    beatle_chs = [ch_of[kp], rng.choice([c for c in range(n_ch) if c != ch_of[kp]])]
    for ch in beatle_chs:
        put(BEATLES, rng.choice([p for p in range(n_pages) if ch_of[p] == ch]))
    # Outlaws on the killer's page and 3-4 more, spread so their pages and neighbours cover about 60%.
    others = [p for p in range(n_pages) if abs(p - kp) >= 2]
    outlaw_pages = {kp}
    while len(outlaw_pages) < rng.randint(4, 5):
        q = rng.choice(others)
        if all(abs(q - x) >= 2 for x in outlaw_pages):
            outlaw_pages.add(q)
    for p in sorted(outlaw_pages):
        put(OUTLAWS, p)
    # Easter eggs: fun to find, no clue uses them.
    for g in EGGS:
        put(g, rng.randrange(n_pages))
    # Musketeers: single names scattered everywhere.
    for _ in range(musketeers):
        put((rng.choice(MUSKETEERS),), rng.randrange(n_pages))

    led = Ledger(pages, chapters).index()

    # The killer: a page that every hunt clue keeps under every reading (so on an outlaw page,
    # strictly between the sisters, in a Beatles chapter), within WINDOW - 1 names of a Musketeer.
    hunt = [c for c in CLUES if c.kind == "hunt"]
    safe = set(range(len(led.flat)))
    for r in READINGS:
        safe &= set(solve(led, hunt, r))
    choices = [i for i in safe if led.flat[i] not in RESERVED and not any(
        led.flat[j] in RESERVED for j in range(max(0, i - 1), min(len(led.flat), i + 2)))]
    if not choices:
        raise ValueError("no place for the killer (seed %d)" % seed)
    killer = rng.choice(sorted(choices))
    pool = [n for n in FILLER if _passes_letters_everywhere(n)]
    p, k = led.page_of[killer], killer - sum(len(x) for x in pages[:led.page_of[killer]])
    pages[p][k] = rng.choice(pool)
    led.index()
    sig = signature(led.flat[killer])

    # Repair: every other survivor gets a name that fails a letter clue under every reading;
    # every near-survivor (all clues but one) must not match the check line.
    failing = [n for n in FILLER if _fails_letters_everywhere(n)]
    for _ in range(20):
        changed = False
        bad = survivors_all_readings(led) - {killer}
        for c in CLUES:
            bad |= {i for i in survivors_all_readings(led, skip=c.key)
                    if i != killer and signature(led.flat[i]) == sig}
        for i in sorted(bad):
            if led.flat[i] in RESERVED:
                raise ValueError("a landmark would need renaming (seed %d)" % seed)
            new = rng.choice([n for n in failing if signature(n) != sig])
            p = led.page_of[i]
            pages[p][i - sum(len(x) for x in pages[:p])] = new
            changed = True
        led.index()
        if not changed:
            break
    else:
        raise ValueError("repair did not settle (seed %d)" % seed)

    stats = _stats(led, killer)
    return Case(led, killer, sig, stats)


def _stats(led, killer):
    total = len(led.flat)
    alone = {c.key: round(sum(c.test(led, {})) / total, 2) for c in CLUES}
    hunt = [c for c in CLUES if c.kind == "hunt"]
    after_hunt = len(solve(led, hunt))
    finals = {k: sorted(solve(led, CLUES, r)) for k, r in enumerate(READINGS)}
    return dict(total=total, pages=len(led.pages), alone=alone, after_hunt=after_hunt, finals=finals,
                killer=killer, killer_name=led.flat[killer], killer_page=led.page_no(led.page_of[killer]))


def validate(case, keep=(0.3, 0.7)):
    """The rules the spec sets for a case; returns a list of problems (empty when fine)."""
    led, s, problems = case.ledger, case.stats, []
    for r, alive in s["finals"].items():
        if alive != [case.killer]:
            problems.append("reading %d leaves %s" % (r, alive))
    for key in HUNT_KEYS:
        if not keep[0] <= s["alone"][key] <= keep[1] and key != "musketeers":
            problems.append("hunt clue %s alone keeps %.0f%%" % (key, 100 * s["alone"][key]))
    if not 0.25 <= s["alone"]["musketeers"] <= 0.6:
        problems.append("musketeer clue alone keeps %.0f%%" % (100 * s["alone"]["musketeers"]))
    if not 60 <= s["after_hunt"] <= 400:
        problems.append("%d names left for the letter clues" % s["after_hunt"])
    for c in CLUES:
        near = survivors_all_readings(led, skip=c.key) - {case.killer}
        if any(signature(led.flat[i]) == case.check for i in near):
            problems.append("check line also fits a near-survivor (skipping %s)" % c.key)
    if len(led.runs(BRONTES)) != 1 or len(led.runs(MARCH)) != 1:
        problems.append("sisters not unique")
    return problems


def generate_valid(seeds=range(1, 200), **kw):
    for s in seeds:
        try:
            case = generate(s, **kw)
        except ValueError:
            continue
        if not validate(case):
            case.stats["seed"] = s
            return case
    raise RuntimeError("no valid case in the seeds tried")
