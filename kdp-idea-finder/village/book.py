"""The full book: five linked cases in Juniper Falls and a mastermind finale
(spec: briefs/2026-10-01_spec-linked-cases.md).

Each case is one shop's ledger, laid out like Who Killed Mr Darcy?: entries
separated by dots, famous names hidden among ordinary customers, clues that
are facts about the killer, one name left, and a check line after the ledger
that confirms the answer without giving it away.

The cases are linked:
- from Case Two on, one clue uses the previous case's killer;
- the first letters of the five killers spell the mastermind's first name,
  whom the finale finds in the town register.

Every case is solved under READINGS, the plausible misreadings of the rules,
and is only accepted when each of them leaves the same one name.
"""

import random
import re
from dataclasses import dataclass, field

from whodunit.names import FIRST, LAST

VOWELS = set("AEIOU")
WINDOW = 10

READINGS = [
    {},                          # the rules as printed
    {"y_vowel": True},           # treats Y as a vowel
    {"window": 1},               # "within 10 names" counted one too generously
    {"window": -1},              # ...or one too strictly
    {"between_inclusive": True}, # counts the two landmarks' own pages as "between"
    {"near_page_only": True},    # forgets the page before and after
    {"pair_either": True},       # takes "both an A and a B" as either one
]


def letters(name):
    return re.sub(r"[^A-Za-z]", "", name).upper()


def signature(name):
    """What the check line prints: number of letters, and their sum with A = 1 ... Z = 26."""
    l = letters(name)
    return len(l), sum(ord(c) - 64 for c in l)


def article(name):
    return "an" if name[0] in "AEIOU" else "a"


def join_and(names):
    names = list(names)
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def join_or(names):
    names = list(names)
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]


# ---------------------------------------------------------------- themes

@dataclass
class Theme:
    key: str
    number: str                 # "One"
    shop: str                   # "The Bookstore"
    place: str                  # "Pell's Books"
    noun: str                   # what a name in the ledger is: "customer"
    chapters: list              # five places inside the shop
    group: tuple                # all of them in a chapter
    group_label: str            # "March sisters"
    group_note: str             # who they are
    throughout: str             # appears 3-4 times
    once: tuple                 # two names, once each
    pair: tuple                 # both on the killer's page
    scattered: tuple            # one at a time, everywhere
    scattered_one: str          # "a Musketeer"
    scattered_label: str        # "The Musketeers"
    eggs: list                  # famous names with no clue

    def landmark_names(self):
        return {*self.group, self.throughout, *self.once, *self.pair, *self.scattered, *self.eggs}

    def reserved_words(self):
        """First names and surnames that never appear in ordinary entries in this case."""
        return {w for n in self.landmark_names() for w in n.split()}


THEMES = [
    Theme("bookstore", "One", "The Bookstore", "Pell's Books", "customer",
          ["Mystery & Crime", "Romance", "Cookbooks", "The Children's Corner", "The Reading Café"],
          ("Meg", "Jo", "Beth", "Amy"), "March sisters", "the four sisters of Little Women",
          "Tom Sawyer", ("Romeo", "Juliet"), ("Anne Shirley", "Gilbert Blythe"),
          ("Athos", "Porthos", "Aramis"), "a Musketeer", "The Musketeers",
          ["Huckleberry Finn", "Ichabod Crane", "Rip Van Winkle", "Hester Prynne", "Jay Gatsby", "Captain Ahab",
           "Oliver Twist", "Ebenezer Scrooge", "Jane Eyre", "Phileas Fogg", "Dorian Gray", "Captain Nemo"]),
    Theme("bakery", "Two", "The Bakery", "Rosie's Bakery", "taster",
          ["The Bread Shelves", "The Pie Table", "The Cake Counter", "The Cookie Jar", "The Coffee Bar"],
          ("Queen of Hearts", "King of Hearts", "Knave of Hearts"), "Hearts",
          "the Queen, the King and the Knave of Hearts, from the old rhyme about the stolen tarts",
          "Simple Simon", ("Humpty Dumpty", "Mother Goose"), ("Jack", "Jill"),
          ("Little Bo Peep", "Little Boy Blue", "Little Miss Muffet"), "a Little", "The Littles",
          ["Peter Piper", "Old King Cole", "Mother Hubbard", "Jack Sprat", "Wee Willie Winkie", "Georgie Porgie",
           "Polly Flinders", "Lucy Locket", "Doctor Foster", "Mary Mary"]),
    Theme("diner", "Three", "The Diner", "Lou's Diner", "diner",
          ["The Counter", "The Booths", "The Window Tables", "The Back Room", "The Takeout Line"],
          ("George Washington", "Thomas Jefferson", "Theodore Roosevelt", "Abraham Lincoln"), "Mount Rushmore presidents",
          "the four presidents carved into Mount Rushmore",
          "Benjamin Franklin", ("John Adams", "John Quincy Adams"), ("Meriwether Lewis", "William Clark"),
          ("Orville Wright", "Wilbur Wright"), "a Wright brother", "The Wright brothers",
          ["Betsy Ross", "Paul Revere", "Davy Crockett", "Annie Oakley", "Johnny Appleseed", "Amelia Earhart",
           "Daniel Boone", "Calamity Jane", "Buffalo Bill", "Pecos Bill"]),
    Theme("inn", "Four", "The Inn", "the Juniper Inn", "guest",
          ["The Ballroom", "The Bar", "The Grand Staircase", "The Garden Room", "The Library Lounge"],
          ("Jane", "Elizabeth", "Mary", "Kitty", "Lydia"), "Bennet sisters", "the five sisters of Pride and Prejudice",
          "Cupid", ("Antony", "Cleopatra"), ("Napoleon", "Josephine"),
          ("Zeus", "Hera", "Apollo", "Athena"), "a Greek god", "The Greek gods",
          ["Lancelot", "Guinevere", "Tristan", "Isolde", "Orpheus", "Eurydice", "Scarlett", "Rhett", "Heathcliff",
           "Catherine Earnshaw"]),
    Theme("library", "Five", "The Library", "the Juniper Falls Public Library", "reader",
          ["The Reading Room", "The Stacks", "The Reference Desk", "The Children's Library", "The Local Archive"],
          ("Charlotte", "Emily", "Anne"), "Brontë sisters", "the three sisters who wrote Jane Eyre, Wuthering "
          "Heights and Agnes Grey", "Mark Twain", ("Charles Dickens", "Jane Austen"), ("Robert Frost", "Walt Whitman"),
          ("Jacob Grimm", "Wilhelm Grimm"), "a Brother Grimm", "The Brothers Grimm",
          ["Herman Melville", "Oscar Wilde", "Victor Hugo", "Leo Tolstoy", "Virginia Woolf", "Edgar Allan Poe",
           "Louisa May Alcott", "Emily Dickinson", "Jules Verne", "Bram Stoker"]),
]

# The finale reuses each case's "throughout" landmark, so the register calls back to the five cases.
MASTERMINDS = ["Edith", "Mabel", "Clara", "Hazel", "Agnes", "Ralph", "Grace", "Cyril", "Basil", "Ethel"]


# ---------------------------------------------------------------- the ledger

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

    def at(self, i):
        """(page index, position on that page) of a flat index."""
        p = self.page_of[i]
        return p, i - sum(len(x) for x in self.pages[:p])


# ---------------------------------------------------------------- clues

@dataclass
class Clue:
    key: str
    kind: str          # "hunt", "letter" or "chain"
    text: str          # the clue, as printed
    explain: str       # how it works, as printed under it
    test: object       # test(ledger, reading) -> list of bools, one per entry


def _vowel(c, reading):
    return c in VOWELS or (c == "Y" and bool(reading.get("y_vowel")))


def word_clue(key, text, explain, fn, kind="letter"):
    return Clue(key, kind, text, explain, lambda led, reading: [fn(n, reading) for n in led.flat])


LETTER_CLUES = [
    word_clue("odd_consonants", "The killer's name has an odd number of consonants.",
              "Count every letter in the whole name that isn't a vowel. Y is always a consonant.",
              lambda n, r: sum(not _vowel(c, r) for c in letters(n)) % 2 == 1),
    word_clue("even_consonants", "The killer's name has an even number of consonants.",
              "Count every letter in the whole name that isn't a vowel. Y is always a consonant.",
              lambda n, r: sum(not _vowel(c, r) for c in letters(n)) % 2 == 0),
    word_clue("ends_consonant", "The killer's name ends in a consonant.",
              "Look only at the very last letter of the whole name. Y is a consonant.",
              lambda n, r: not _vowel(letters(n)[-1], r)),
    word_clue("ends_vowel", "The killer's name ends in a vowel.",
              "Look only at the very last letter of the whole name. The vowels are A, E, I, O and U; Y is not one.",
              lambda n, r: _vowel(letters(n)[-1], r)),
    word_clue("double_letter", "The killer's name contains a double letter.",
              "Two of the same letter sitting together in the name, not split by a space. It only needs to appear "
              "once, anywhere in the name.",
              lambda n, r: any(re.search(r"([a-z])\1", w.lower()) for w in n.split())),
    word_clue("no_double_letter", "The killer's name has no double letter.",
              "No two of the same letter sit together anywhere in the name. Letters split by a space don't count "
              "as a double.",
              lambda n, r: not any(re.search(r"([a-z])\1", w.lower()) for w in n.split())),
    word_clue("a_to_m", "The killer's name begins with a letter from the first half of the alphabet, A to M.",
              "Look only at the very first letter of the name.", lambda n, r: letters(n)[0] <= "M"),
    word_clue("n_to_z", "The killer's name begins with a letter from the second half of the alphabet, N to Z.",
              "Look only at the very first letter of the name.", lambda n, r: letters(n)[0] >= "N"),
    word_clue("even_vowels", "The killer's name has an even number of vowels.",
              "Count every A, E, I, O and U in the whole name. Y is not a vowel.",
              lambda n, r: sum(_vowel(c, r) for c in letters(n)) % 2 == 0),
    word_clue("odd_vowels", "The killer's name has an odd number of vowels.",
              "Count every A, E, I, O and U in the whole name. Y is not a vowel.",
              lambda n, r: sum(_vowel(c, r) for c in letters(n)) % 2 == 1),
    word_clue("full_name", "The killer signed with a first name and a surname.",
              "The entry has two words, like Ada Finch, not a single name like Rosa.",
              lambda n, r: len(n.split()) == 2),
]
LETTER_BY_KEY = {c.key: c for c in LETTER_CLUES}
OPPOSITES = [{"odd_consonants", "even_consonants"}, {"ends_consonant", "ends_vowel"},
             {"double_letter", "no_double_letter"}, {"a_to_m", "n_to_z"}, {"even_vowels", "odd_vowels"}]


def hunt_clues(t):
    """The five hunt clues of a theme."""
    def near_page(led, reading):
        pages = led.pages_with(t.throughout)
        if not reading.get("near_page_only"):
            pages = {q for p in pages for q in (p - 1, p, p + 1)}
        return [p in pages for p in led.page_of]

    def not_group_chapter(led, reading):
        found = {}
        for i, n in enumerate(led.flat):
            if n in t.group:
                found.setdefault(led.chapter_of_page[led.page_of[i]], set()).add(n)
        full = {ch for ch, names in found.items() if len(names) == len(t.group)}
        return [led.chapter_of_page[p] not in full for p in led.page_of]

    def near_scattered(led, reading):
        w = WINDOW + reading.get("window", 0)
        out = [False] * len(led.flat)
        for j, name in enumerate(led.flat):
            if name in t.scattered:
                for k in range(max(0, j - w), min(len(out), j + w + 1)):
                    if k != j:
                        out[k] = True
        return out

    def between(led, reading):
        (pa,), (pb,) = led.pages_with(t.once[0]), led.pages_with(t.once[1])
        lo, hi = min(pa, pb), max(pa, pb)
        if reading.get("between_inclusive"):
            return [lo <= p <= hi for p in led.page_of]
        return [lo < p < hi for p in led.page_of]

    def pair_page(led, reading):
        a, b = led.pages_with(t.pair[0]), led.pages_with(t.pair[1])
        pages = (a | b) if reading.get("pair_either") else (a & b)
        return [p in pages for p in led.page_of]

    n_group = ["", "one", "two", "three", "four", "five", "six"][len(t.group)]
    return [
        Clue("near_page", "hunt", "The killer is within one page of %s %s." % (article(t.throughout), t.throughout),
             "“Within one page” means the page before, the same page, or the page after. %s turns up "
             "more than once; being within one page of any appearance qualifies." % t.throughout, near_page),
        Clue("group", "hunt", "The killer is not in a chapter that contains all %s %s." % (n_group, t.group_label),
             "The %s are %s: %s, exactly as written and on their own. All %s must appear somewhere in the "
             "chapter, in any order. More than one chapter may contain all of them." % (
                 t.group_label, t.group_note, join_and(t.group), n_group), not_group_chapter),
        Clue("scattered", "hunt", "The killer sits within %d names of %s." % (WINDOW, t.scattered_one),
             "%s are %s. Count names in normal reading order: the very next name is 1 away. If one is near the "
             "top or bottom of a page, the count carries on onto the previous or next page." % (
                 t.scattered_label, join_and(t.scattered)), near_scattered),
        Clue("between", "hunt", "The killer appears between %s's page and %s's page." % t.once,
             "%s and %s each appear only once in the ledger. Their own two pages don't count: the killer's page "
             "falls somewhere in between." % t.once, between),
        Clue("pair", "hunt", "The killer's page contains both %s %s and %s %s." % (
            article(t.pair[0]), t.pair[0], article(t.pair[1]), t.pair[1]),
             "Both names must be on the page, anywhere on it. They don't need to sit together.", pair_page),
    ]


def chain_clue(prev_theme, prev_name):
    last = letters(prev_name)[-1]
    return word_clue("chain", "The killer's name contains the last letter of the %s killer's name." % (
        prev_theme.shop[4:].lower()),
        "Take the name you found in Case %s (%s) and look at its very last letter. This killer's name contains "
        "that letter somewhere." % (prev_theme.number, prev_theme.shop.lower()),
        lambda n, r: last in letters(n), kind="chain")


def solve(led, clues, reading=None, skip=None):
    reading = reading or {}
    alive = [True] * len(led.flat)
    for c in clues:
        if c.key != skip:
            alive = [a and b for a, b in zip(alive, c.test(led, reading))]
    return [i for i, a in enumerate(alive) if a]


def survivors_all_readings(led, clues, skip=None):
    out = set()
    for r in READINGS:
        out |= set(solve(led, clues, r, skip))
    return out


def verdicts(clue, name):
    one = Ledger([[name]], [("", 0)]).index()
    return {clue.test(one, r)[0] for r in READINGS}


# ---------------------------------------------------------------- generation

@dataclass
class Case:
    theme: Theme
    ledger: Ledger
    clues: list
    killer: int
    check: tuple
    stats: dict


class GenerationError(ValueError):
    pass


def _pools(theme):
    bad = theme.reserved_words()
    firsts = [n for n in FIRST if n not in bad and n.isalpha()]
    lasts = [n for n in LAST if n not in bad and n.isalpha()]
    return firsts, lasts


def generate_case(theme, rng, initial, chain=None, n_pages=20, per_page=(205, 215), pages_per_chapter=4,
                  scattered=70, heading_cost=30):
    """One case whose killer's first name begins with `initial`; `chain` is the previous case's clue."""
    firsts, lasts = _pools(theme)

    def entry(full_share=0.45):
        f = rng.choice(firsts)
        return f + " " + rng.choice(lasts) if rng.random() < full_share else f

    n_ch = n_pages // pages_per_chapter
    chapters = [(theme.chapters[k], k * pages_per_chapter) for k in range(n_ch)]
    ch_of = [p // pages_per_chapter for p in range(n_pages)]
    pages = [[entry() for _ in range(rng.randint(*per_page) - (heading_cost if p % pages_per_chapter == 0 else 0))]
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

    # The two "once" names: about half the pages strictly between them.
    gap = rng.randint(9, 11)
    lo = rng.randint(0, n_pages - gap - 2)
    pa, pb = (lo, lo + gap + 1) if rng.random() < 0.5 else (lo + gap + 1, lo)
    put(theme.once[0], pa)
    put(theme.once[1], pb)
    kp = rng.choice(range(min(pa, pb) + 2, max(pa, pb) - 1))
    # The group: all of them in two chapters other than the killer's; some of them in each other chapter.
    full = set(rng.sample([c for c in range(n_ch) if c != ch_of[kp]], 2))
    for ch in range(n_ch):
        chosen = theme.group if ch in full else rng.sample(theme.group, rng.randint(1, len(theme.group) - 1))
        for g in chosen:
            put(g, rng.choice([p for p in range(n_pages) if ch_of[p] == ch]))
    # "Throughout": on the killer's page and two or three others.
    for p in {kp} | set(rng.sample([p for p in range(n_pages) if abs(p - kp) > 2], rng.randint(2, 3))):
        put(theme.throughout, p)
    # The pair: both on the killer's page and on about half the others; one alone on a few more.
    both = {kp} | set(rng.sample(range(n_pages), n_pages // 2 - 1))
    for p in both:
        put(theme.pair[0], p)
        put(theme.pair[1], p)
    for p in rng.sample([p for p in range(n_pages) if p not in both], 3):
        put(rng.choice(theme.pair), p)
    for egg in theme.eggs:
        put(egg, rng.randrange(n_pages))

    # The killer: a full name with the right initial; then the letter clues it passes under every reading.
    hunts = hunt_clues(theme)
    for _ in range(500):
        first = rng.choice([f for f in firsts if f[0] == initial])
        name = first + " " + rng.choice(lasts)
        if chain and verdicts(chain, name) != {True}:
            continue
        fits = [c for c in LETTER_CLUES if c.key != "full_name" and verdicts(c, name) == {True}]
        rng.shuffle(fits)
        picked = []
        for c in fits:
            if not any(c.key in o and picked_key in o for o in OPPOSITES for picked_key in [p.key for p in picked]):
                picked.append(c)
            if len(picked) == 4:
                break
        if len(picked) == 4:
            break
    else:
        raise GenerationError("no killer name fits (%s, %s)" % (theme.key, initial))
    clues = hunts[:1] + picked[:1] + hunts[1:2] + hunts[2:3] + picked[1:2] + hunts[3:4] + picked[2:3] + hunts[4:5] \
        + picked[3:4] + ([chain] if chain else [])
    k = put(name, kp)
    put(rng.choice(theme.scattered), kp, near=k)
    for _ in range(scattered):
        put(rng.choice(theme.scattered), rng.randrange(n_pages))

    led = Ledger(pages, chapters).index()
    killer = sum(len(x) for x in pages[:kp]) + k
    sig = signature(name)
    landmarks = theme.landmark_names()

    # Repair: every other survivor gets a name that fails a letter clue under every reading;
    # nobody who survives all clues but one may match the check line.
    word = [c for c in clues if c.kind != "hunt"]
    failing = sorted({e for e in {entry() for _ in range(3000)} if any(verdicts(c, e) == {False} for c in word)})
    for _ in range(20):
        bad = survivors_all_readings(led, clues) - {killer}
        for c in clues:
            bad |= {i for i in survivors_all_readings(led, clues, skip=c.key)
                    if i != killer and signature(led.flat[i]) == sig}
        if not bad:
            break
        hunt_alive = set(solve(led, hunts))
        for i in bad:
            p, at = led.at(i)
            if led.flat[i] in theme.eggs:
                # An unclued famous name: swap it with an ordinary entry on a page the hunt clues rule out.
                q = rng.choice([q for q in range(n_pages) if not any(led.page_of[j] == q for j in hunt_alive)])
                at2 = rng.choice([a for a in range(1, len(pages[q]) - 1) if pages[q][a] not in landmarks])
                pages[p][at], pages[q][at2] = pages[q][at2], pages[p][at]
                if pages[p][at] in landmarks or pages[p][at] == name:
                    raise GenerationError("could not move a famous name (%s)" % theme.key)
                continue
            if led.flat[i] in landmarks and (led.flat[i] not in theme.scattered or abs(i - killer) > WINDOW + 2):
                # A clued famous name: move it on its own page, far from every scattered name, so the
                # "within 10 names" clue rules it out. Page and chapter clues are unaffected.
                scat = [j for j, n in enumerate(led.flat) if n in theme.scattered and j != i] + [killer]
                start = sum(len(x) for x in pages[:p])
                spots = [a for a in range(len(pages[p])) if pages[p][a] not in landmarks and start + a != killer
                         and all(abs(start + a - j) > WINDOW + 2 for j in scat)]
                if not spots:
                    raise GenerationError("no room to move %s (%s)" % (led.flat[i], theme.key))
                a = rng.choice(spots)
                pages[p][at], pages[p][a] = pages[p][a], pages[p][at]
                continue
            if led.flat[i] in landmarks:
                raise GenerationError("a landmark would need renaming (%s)" % theme.key)
            pages[p][at] = rng.choice([n for n in failing if signature(n) != sig])
        led.index()
    else:
        raise GenerationError("repair did not settle (%s)" % theme.key)
    case = Case(theme, led, clues, killer, sig, {})
    case.stats = stats(case)
    return case


def stats(case):
    led, clues = case.ledger, case.clues
    total = len(led.flat)
    alive, after = list(range(total)), []
    for c in clues:
        ok = c.test(led, {})
        alive = [i for i in alive if ok[i]]
        after.append(len(alive))
    return dict(total=total, pages=len(led.pages), killer_name=led.flat[case.killer],
                alone={c.key: round(sum(c.test(led, {})) / total, 2) for c in clues},
                after_each=after, after_hunt=len(solve(led, [c for c in clues if c.kind == "hunt"])),
                finals={k: solve(led, clues, r) for k, r in enumerate(READINGS)})


def validate(case):
    """The spec's rules for a case; returns a list of problems (empty when fine)."""
    led, s, problems = case.ledger, case.stats, []
    for r, alive in s["finals"].items():
        if alive != [case.killer]:
            problems.append("%s: reading %d leaves %d names" % (case.theme.key, r, len(alive)))
    for c in case.clues:
        if c.kind == "hunt" and not 0.25 <= s["alone"][c.key] <= 0.75:
            problems.append("%s: hunt clue %s alone keeps %.0f%%" % (case.theme.key, c.key, 100 * s["alone"][c.key]))
        near = survivors_all_readings(led, case.clues, skip=c.key) - {case.killer}
        if any(signature(led.flat[i]) == case.check for i in near):
            problems.append("%s: check line fits a near-survivor (skipping %s)" % (case.theme.key, c.key))
    if not 40 <= s["after_hunt"] <= 300:
        problems.append("%s: %d names left for the letter clues" % (case.theme.key, s["after_hunt"]))
    if led.flat[case.killer] in case.theme.landmark_names():
        problems.append("%s: the killer is a landmark" % case.theme.key)
    return problems


# ---------------------------------------------------------------- the finale

FINALE_CHAPTERS = ["Main Street", "Maple Avenue", "Church Lane", "River Road"]


def finale_clues(themes, mastermind):
    """The mastermind's first name, then one callback to each case's "throughout" landmark."""
    t1, t2, t3, t4, t5 = themes

    def name_is(led, reading):
        return [n.split()[0] == mastermind and len(n.split()) == 2 for n in led.flat]

    def near(landmark, key):
        def test(led, reading):
            pages = led.pages_with(landmark)
            if not reading.get("near_page_only"):
                pages = {q for p in pages for q in (p - 1, p, p + 1)}
            return [p in pages for p in led.page_of]
        return Clue(key, "hunt", "The mastermind is within one page of %s %s." % (article(landmark), landmark),
                    "The page before, the same page, or the page after any %s." % landmark, test)

    def not_on_page(landmark, key):
        def test(led, reading):
            pages = led.pages_with(landmark)
            return [p not in pages for p in led.page_of]
        return Clue(key, "hunt", "The mastermind is not on a page with %s %s." % (article(landmark), landmark),
                    "Cross out every page where %s appears." % landmark, test)

    def between(a, b, key):
        def test(led, reading):
            (pa,), (pb,) = led.pages_with(a), led.pages_with(b)
            lo, hi = min(pa, pb), max(pa, pb)
            if reading.get("between_inclusive"):
                return [lo <= p <= hi for p in led.page_of]
            return [lo < p < hi for p in led.page_of]
        return Clue(key, "hunt", "The mastermind appears between %s's page and %s's page." % (a, b),
                    "%s and %s each appear only once in the register. Their own two pages don't count." % (a, b),
                    test)

    return [
        Clue("mastermind_name", "name",
             "The mastermind's first name is spelled by the first letters of the five killers, in case order.",
             "Write down the first letter of each killer's name, from Case One to Case Five. They spell a first "
             "name. Only full names (first name and surname) with exactly that first name qualify.", name_is),
        near(t1.throughout, "f_near1"),
        not_on_page(t2.throughout, "f_not2"),
        between(t3.throughout, t5.throughout, "f_between35"),
        near(t4.throughout, "f_near4"),
    ]


def generate_finale(themes, rng, mastermind, n_pages=8, per_page=(205, 215), pages_per_chapter=2, heading_cost=30):
    """The town register. Ten people share the mastermind's first name; the callback clues leave one.

    Layout (page indices, mirrored at random): Benjamin Franklin on 0 and Mark Twain on 7, so "between" is 1-6;
    Tom Sawyer and Cupid on the mastermind's page 3 (Tom also on 7, Cupid also on 6); Simple Simon on 1, 2 and 5.
    The mastermind's namesakes stand on pages 0, 1, 2 and 5, where every reading rules them out, and each callback
    clue rules out at least one of them.
    """
    t1, t2, t3, t4, t5 = themes
    bad = {w for t in themes for w in t.throughout.split()} | {mastermind}
    firsts = [n for n in FIRST if n not in bad and n.isalpha()]
    lasts = [n for n in LAST if n not in bad and n.isalpha()]

    def entry():
        f = rng.choice(firsts)
        return f + " " + rng.choice(lasts) if rng.random() < 0.45 else f

    flip = rng.random() < 0.5
    P = (lambda p: n_pages - 1 - p) if flip else (lambda p: p)
    chapters = [(FINALE_CHAPTERS[k], k * pages_per_chapter) for k in range(n_pages // pages_per_chapter)]
    clues = finale_clues(themes, mastermind)
    for _ in range(50):
        pages = [[entry() for _ in range(rng.randint(*per_page) - (heading_cost if p % pages_per_chapter == 0
                                                                     else 0))] for p in range(n_pages)]
        taken = [set() for _ in range(n_pages)]

        def put(name, page):
            free = [k for k in range(1, len(pages[page]) - 1) if not ({k - 1, k, k + 1} & taken[page])]
            k = rng.choice(free)
            pages[page][k] = name
            taken[page].add(k)
            return k

        put(t3.throughout, P(0))
        put(t5.throughout, P(7))
        for p in (3, 7):
            put(t1.throughout, P(p))
        for p in (3, 6):
            put(t4.throughout, P(p))
        for p in (1, 2, 5):
            put(t2.throughout, P(p))
        surnames = rng.sample(lasts, 10)
        mp = P(3)
        k = put(mastermind + " " + surnames[0], mp)
        decoy_pages = [0, 1, 2, 5] + [rng.choice([0, 1, 2, 5]) for _ in range(5)]
        for s_name, p in zip(surnames[1:], decoy_pages):
            put(mastermind + " " + s_name, P(p))
        led = Ledger(pages, chapters).index()
        who = sum(len(x) for x in pages[:mp]) + k
        finals = {r: solve(led, clues, READINGS[r]) for r in range(len(READINGS))}
        namesakes = solve(led, clues[:1])
        each = all(len(set(namesakes) - set(solve(led, [clues[0], c]))) >= 1 for c in clues[1:])
        if all(v == [who] for v in finals.values()) and len(namesakes) == 10 and each:
            case = Case(None, led, clues, who, signature(led.flat[who]), {})
            case.stats = stats(case)
            return case
    raise GenerationError("no finale register found")


# ---------------------------------------------------------------- the book

@dataclass
class Book:
    cases: list
    finale: Case
    mastermind: str
    seed: int


def generate_book(seed=1):
    rng = random.Random(seed)
    for mastermind in rng.sample(MASTERMINDS, len(MASTERMINDS)):
        try:
            cases, chain = [], None
            for theme, initial in zip(THEMES, mastermind.upper()):
                for _ in range(6):
                    try:
                        case = generate_case(theme, rng, initial, chain)
                    except GenerationError:
                        continue
                    if not validate(case):
                        break
                else:
                    raise GenerationError("no valid %s case for %s" % (theme.key, initial))
                cases.append(case)
                chain = chain_clue(theme, case.ledger.flat[case.killer])
            finale = generate_finale(THEMES, rng, mastermind)
            return Book(cases, finale, mastermind, seed)
        except GenerationError:
            continue
    raise GenerationError("no book for seed %d" % seed)


def generate_valid_book(seeds=range(1, 50)):
    for s in seeds:
        try:
            return generate_book(s)
        except GenerationError:
            continue
    raise GenerationError("no valid book in the seeds tried")
