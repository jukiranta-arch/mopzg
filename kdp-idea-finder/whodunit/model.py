"""The register (every guest's name in reading order, split into pages and
chapters), the clues, and a solver that applies them.

Guests are single first names, as in the best-selling books of this kind.
Fairy-tale characters appear whole ("Snow White") and are printed in italics.

Letter rules, stated once in the book's rules:
- every printed letter A-Z counts; spaces, hyphens and apostrophes do not;
- the vowels are A, E, I, O and U; every other letter, Y included, is a consonant.

Solvers slip, so every puzzle is also solved under READINGS, the plausible
misreadings of the rules, and is only accepted when all of them leave the
same two suspects.
"""

import bisect
import re
from dataclasses import dataclass, field

VOWELS = set("AEIOU")
BEARS = ("Papa Bear", "Mama Bear", "Baby Bear")
ROYAL_WORDS = ("King", "Queen", "Prince", "Princess")

READINGS = [
    {},                              # the rules as printed
    {"y_vowel": True},               # treats Y as a vowel
    {"window": 1},                   # counts "at most 10 names away" one too generously
    {"window": -1},                  # ...or one too strictly
    {"between_inclusive": True},     # includes Hansel's and Gretel's own pages
    {"royal_first_word": True},      # counts only names that start with King, Queen, Prince or Princess
]


def letters(text):
    return re.sub(r"[^A-Za-z]", "", text).upper()


def words(text):
    return [w for w in re.split(r"\s+", text.strip()) if w]


@dataclass
class Register:
    pages: list                      # list of pages; each page is a list of name strings
    chapters: list                   # list of (place name, first page index)
    first_page_no: int = 1           # printed number of the register's first page
    indoor: set = field(default_factory=set)       # chapter indices set inside the palace
    cast: set = field(default_factory=set)         # every fairy-tale name (printed in italics)

    # Derived lookups, rebuilt by index().
    flat: list = field(default_factory=list)
    page_of: list = field(default_factory=list)
    chapter_of_page: list = field(default_factory=list)
    cache: dict = field(default_factory=dict)
    page_start: list = field(default_factory=list)   # flat index of each page's first name
    reading: dict = field(default_factory=dict)      # one of READINGS; {} is the rules as printed

    def set_reading(self, reading):
        if reading != self.reading:
            self.reading, self.cache = dict(reading), {}

    def index(self):
        self.flat, self.page_of, self.cache, self.page_start = [], [], {}, []
        for p, names in enumerate(self.pages):
            self.page_start.append(len(self.flat))
            for n in names:
                self.flat.append(n)
                self.page_of.append(p)
        self.chapter_of_page = []
        starts = [c[1] for c in self.chapters]
        ch = -1
        for p in range(len(self.pages)):
            while ch + 1 < len(starts) and starts[ch + 1] <= p:
                ch += 1
            self.chapter_of_page.append(ch)
        return self

    def page_no(self, p):
        return self.first_page_no + p

    def first_index_on_page(self, p):
        return self.page_start[p]


# ---------------------------------------------------------------- clues

@dataclass
class Clue:
    key: str
    text: str                        # the rule, as printed on the clue card
    explain: str                     # how to apply it (the first-level hint)
    kind: str                        # "word" (about the name) or "place" (about where it sits)
    test: object                     # test(reg, i) -> bool
    param: dict = field(default_factory=dict)


def is_vowel(reg, ch):
    return ch in VOWELS or (ch == "Y" and bool(reg.reading.get("y_vowel")))


def is_royal(reg, text):
    ws = words(text)
    if reg.reading.get("royal_first_word"):
        return ws[0] in ROYAL_WORDS
    return any(w in ROYAL_WORDS for w in ws)


def _odd_consonants(reg, i):
    return sum(1 for c in letters(reg.flat[i]) if not is_vowel(reg, c)) % 2 == 1


def _even_vowels(reg, i):
    return sum(1 for c in letters(reg.flat[i]) if is_vowel(reg, c)) % 2 == 0


def _ends_consonant(reg, i):
    return not is_vowel(reg, letters(reg.flat[i])[-1])


def _double_letter(reg, i):
    return any(len(w) > 1 and re.search(r"([a-z])\1", w.lower()) for w in words(reg.flat[i]))


def _first_half(reg, i):
    return letters(reg.flat[i])[0] <= "M"


def _last_two_rising(reg, i):
    l = letters(reg.flat[i])
    return len(l) > 1 and l[-2] < l[-1]


def _key_letter(reg, i):
    opening = letters(reg.pages[reg.page_of[i]][0])
    return opening[0] in letters(reg.flat[i])


def _odd_page_number(reg, i):
    return reg.page_no(reg.page_of[i]) % 2 == 1


def _chapter_indoors(reg, i):
    return reg.chapter_of_page[reg.page_of[i]] in reg.indoor


def near_page_of_test(name):
    def test(reg, i):
        key = ("pages_of", name)
        if key not in reg.cache:
            reg.cache[key] = {reg.page_of[j] for j, n in enumerate(reg.flat) if n == name}
        p = reg.page_of[i]
        return any(abs(p - q) <= 1 for q in reg.cache[key])
    return test


def between_pages_test(a, b):
    def test(reg, i):
        key = ("between", a, b)
        if key not in reg.cache:
            pa, pb = reg.page_of[reg.flat.index(a)], reg.page_of[reg.flat.index(b)]
            reg.cache[key] = (min(pa, pb), max(pa, pb))
        lo, hi = reg.cache[key]
        if reg.reading.get("between_inclusive"):
            return lo <= reg.page_of[i] <= hi
        return lo < reg.page_of[i] < hi
    return test


def _royal_on_page(reg, i):
    p = reg.page_of[i]
    key = ("royal", p)
    if key not in reg.cache:
        reg.cache[key] = any(is_royal(reg, n) for n in reg.pages[p])
    return reg.cache[key]


def near_cast_test(n):
    def test(reg, i):
        key = ("cast_positions",)
        if key not in reg.cache:
            reg.cache[key] = [j for j, name in enumerate(reg.flat) if name in reg.cast]
        w = n + reg.reading.get("window", 0)
        pos = reg.cache[key]
        k = bisect.bisect_left(pos, i - w)
        while k < len(pos) and pos[k] <= i + w:
            if pos[k] != i:
                return True
            k += 1
        return False
    return test


def _bears_together(reg, i):
    """The chapter holds Papa Bear, Mama Bear and Baby Bear one straight after another."""
    ch = reg.chapter_of_page[reg.page_of[i]]
    key = ("bears",)
    if key not in reg.cache:
        reg.cache[key] = {reg.chapter_of_page[reg.page_of[j]] for j in range(len(reg.flat) - 2)
                          if tuple(reg.flat[j:j + 3]) == BEARS}
    return ch in reg.cache[key]


def catalogue(cast_window=10):
    """Every clue type the generator can use, keyed by name."""
    c = [
        Clue("chapter_indoors",
             "Keep only guests in a chapter named after a room inside the palace. Cross out every chapter set "
             "out in the grounds.",
             "Rooms are inside: the Ballroom, the Kitchens, the Library and so on. Gardens, gates, yards, bridges, "
             "mazes and orchards are outside. The chapters are listed on The Palace page.",
             "place", _chapter_indoors),
        Clue("three_bears",
             "Keep only guests in a chapter where Papa Bear, Mama Bear and Baby Bear stand together, one straight "
             "after another.",
             "Look for the three bears side by side in reading order (they may run on to the next line). "
             "Cross out every chapter where they don’t stand together.",
             "place", _bears_together),
        Clue("between_hansel_gretel",
             "Keep only guests on the pages between Hansel’s page and Gretel’s.",
             "Hansel and Gretel each appear exactly once. Their own two pages don’t count.",
             "place", between_pages_test("Hansel", "Gretel")),
        Clue("near_wolf",
             "Keep only guests on a page with the Big Bad Wolf on it, or on the page just before or after one.",
             "The Wolf turns up more than once. Mark every Wolf page first.",
             "place", near_page_of_test("Big Bad Wolf")),
        Clue("royal_on_page",
             "Keep only guests whose page has a royal guest on it.",
             "A royal guest is any name with the word King, Queen, Prince or Princess in it, such as the "
             "Snow Queen or Old King Cole.",
             "place", _royal_on_page),
        Clue("odd_page",
             "Keep only guests on an odd-numbered page.",
             "Use the page number printed at the foot of each register page.",
             "place", _odd_page_number),
        Clue("near_character",
             "Keep only guests at most %d names away from a fairy-tale character." % cast_window,
             "Fairy-tale characters are printed in italics. Count in reading order: the very next name is 1 away. "
             "The count carries on across lines and pages. Highlight the %d names either side of each character."
             % cast_window,
             "place", near_cast_test(cast_window), {"window": cast_window}),
        Clue("odd_consonants",
             "Keep only names with an odd number of consonants.",
             "Count every letter that is not A, E, I, O or U. Y is a consonant.", "word", _odd_consonants),
        Clue("even_vowels",
             "Keep only names with an even number of vowels.",
             "Count every A, E, I, O and U. Y is not a vowel.", "word", _even_vowels),
        Clue("ends_consonant",
             "Keep only names that end in a consonant.",
             "Look only at the last letter. Y is a consonant.", "word", _ends_consonant),
        Clue("double_letter",
             "Keep only names with a double letter.",
             "The same letter twice in a row, like the “ll” in Bella or the “nn” in Anna.", "word", _double_letter),
        Clue("first_half",
             "Keep only names that begin with a letter from A to M.",
             "Look only at the first letter.", "word", _first_half),
        Clue("last_two_rising",
             "Keep only names whose last two letters are in alphabetical order.",
             "“Lucy” ends C, Y: in order. “Ann” ends N, N: a double letter is not in order.", "word",
             _last_two_rising),
        Clue("key_letter",
             "Keep only names that contain the first letter of the name printed first on their page.",
             "The first name on a page is the one at the top left. Note its first letter, then check each "
             "name on that page for it.", "place", _key_letter),
    ]
    return {x.key: x for x in c}


def solve(reg, clues, reading=None):
    """Indices that satisfy every clue, and how many remain after each clue in turn,
    under one of READINGS (default: the rules as printed)."""
    reg.set_reading(reading or {})
    alive = list(range(len(reg.flat)))
    counts = []
    for cl in clues:
        alive = [i for i in alive if cl.test(reg, i)]
        counts.append(len(alive))
    return alive, counts


def solve_all_readings(reg, clues):
    """Survivors under each reading, as {reading index: alive}. Leaves the register on the printed rules."""
    out = {k: solve(reg, clues, r)[0] for k, r in enumerate(READINGS)}
    reg.set_reading({})
    return out
