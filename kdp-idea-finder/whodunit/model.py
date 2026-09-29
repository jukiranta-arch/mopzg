"""The register (every guest's name in reading order, split into pages and
chapters), the clues, and a solver that applies them.

Letter rules used by every clue, stated once in the book's rules:
- only the letters A-Z count; spaces, hyphens and apostrophes do not;
- a title (Mr, Queen, Little...) is part of the name;
- the vowels are A, E, I, O and U; every other letter, Y included, is a consonant.
"""

import re
from dataclasses import dataclass, field

VOWELS = set("AEIOU")


def letters(text):
    return re.sub(r"[^A-Za-z]", "", text).upper()


def words(text):
    return [w for w in re.split(r"\s+", text.strip()) if w]


@dataclass
class Register:
    pages: list                      # list of pages; each page is a list of name strings
    chapters: list                   # list of (quote, first page index)
    first_page_no: int = 1           # printed number of the register's first page

    # Derived lookups, rebuilt by index().
    flat: list = field(default_factory=list)
    page_of: list = field(default_factory=list)
    chapter_of_page: list = field(default_factory=list)
    cache: dict = field(default_factory=dict)
    page_start: list = field(default_factory=list)   # flat index of each page's first name

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

    def facing(self, p):
        """Index of the page facing page p in an open book, or None.
        Even printed numbers are left-hand pages, odd numbers right-hand."""
        no = self.page_no(p)
        q = p + 1 if no % 2 == 0 else p - 1
        return q if 0 <= q < len(self.pages) else None

    def first_index_on_page(self, p):
        return self.page_start[p]


# ---------------------------------------------------------------- clues

@dataclass
class Clue:
    key: str
    text: str                        # the clue as printed in the box
    explain: str                     # how to read it (printed in italics)
    kind: str                        # "word" (about the name) or "place" (about where it sits)
    test: object                     # test(reg, i) -> bool
    param: dict = field(default_factory=dict)


def _odd_consonants(reg, i):
    return sum(1 for c in letters(reg.flat[i]) if c not in VOWELS) % 2 == 1


def _even_vowels(reg, i):
    return sum(1 for c in letters(reg.flat[i]) if c in VOWELS) % 2 == 0


def _ends_consonant(reg, i):
    return letters(reg.flat[i])[-1] not in VOWELS


def _double_letter(reg, i):
    return any(len(w) > 1 and re.search(r"([a-z])\1", w.lower()) for w in words(reg.flat[i]))


def _first_half(reg, i):
    return letters(reg.flat[i])[0] <= "M"


def _last_two_rising(reg, i):
    l = letters(reg.flat[i])
    return len(l) > 1 and l[-2] < l[-1]


def _alliterative(text):
    ws = words(text)
    return len(ws) > 1 and len({w[0].upper() for w in ws}) == 1


def starts_with_title(text, title):
    ws = words(text)
    return bool(ws) and ws[0] == title


def near_title_test(title, n):
    def test(reg, i):
        lo, hi = max(0, i - n), min(len(reg.flat), i + n + 1)
        return any(starts_with_title(reg.flat[j], title) for j in range(lo, hi) if j != i)
    return test


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
        return lo < reg.page_of[i] < hi
    return test


def _even_page_count(reg, i):
    return len(reg.pages[reg.page_of[i]]) % 2 == 0


def page_has_both_test(t1, t2):
    def test(reg, i):
        key = ("both", t1, t2, reg.page_of[i])
        if key not in reg.cache:
            names = reg.pages[reg.page_of[i]]
            reg.cache[key] = (any(starts_with_title(n, t1) for n in names)
                              and any(starts_with_title(n, t2) for n in names))
        return reg.cache[key]
    return test


def chapter_has_all_test(required):
    def test(reg, i):
        ch = reg.chapter_of_page[reg.page_of[i]]
        key = ("chapter_all", tuple(required), ch)
        if key not in reg.cache:
            present = {n for p, c in enumerate(reg.chapter_of_page) if c == ch for n in reg.pages[p]}
            reg.cache[key] = all(r in present for r in required)
        return reg.cache[key]
    return test


def _key_letter(reg, i):
    p = reg.page_of[i]
    first = words(reg.pages[p][0])
    key_word = first[1] if len(first) > 1 and first[0] in TITLE_WORDS else first[0]
    return key_word[0].upper() in letters(reg.flat[i])


def _facing_alliterative(reg, i):
    q = reg.facing(reg.page_of[i])
    if q is None:
        return False
    key = ("alliterative_page", q)
    if key not in reg.cache:
        reg.cache[key] = any(_alliterative(n) for n in reg.pages[q])
    return reg.cache[key]


TITLE_WORDS = {"Mr", "Mrs", "Miss", "Dr", "Sir", "Lady", "Dame", "Lord", "Captain", "Old", "Little",
               "King", "Queen", "Prince", "Princess", "Mother", "Father"}

BEARS = ("Papa Bear", "Mama Bear", "Baby Bear")


def catalogue(queen_window=12):
    """Every clue type the generator can use, keyed by name."""
    c = [
        Clue("odd_consonants", "Each suspect’s name has an odd number of consonants.",
             "Count every consonant in the whole name, title included. Y is a consonant.", "word", _odd_consonants),
        Clue("even_vowels", "Each suspect’s name has an even number of vowels.",
             "Count every A, E, I, O and U in the whole name. None at all counts as even.", "word", _even_vowels),
        Clue("ends_consonant", "Each suspect’s name ends in a consonant.",
             "Look only at the very last letter of the whole name.", "word", _ends_consonant),
        Clue("double_letter", "Each suspect’s name contains a double letter.",
             "The same letter twice in a row inside one word, like the “ll” in Bella. "
             "Letters split by a space don’t count.", "word", _double_letter),
        Clue("first_half", "Each suspect’s name begins with a letter from A to M.",
             "The first letter of the name as printed, title included.", "word", _first_half),
        Clue("last_two_rising", "The last two letters of each suspect’s name are in alphabetical order.",
             "“Ann” ends N, N: a double letter is not in order. “Lucy” ends C, Y: in order.",
             "word", _last_two_rising),
        Clue("near_queen", "Each suspect sits within %d names of a Queen." % queen_window,
             "A Queen is any name that begins with the title Queen. Count names in reading order; "
             "the count carries on across page and chapter breaks.", "place",
             near_title_test("Queen", queen_window), {"window": queen_window}),
        Clue("near_wolf", "Both suspects are within one page of the Big Bad Wolf.",
             "The Wolf turns up more than once. A suspect’s page must be a Wolf page, "
             "or the page just before or just after one.", "place", near_page_of_test("Big Bad Wolf")),
        Clue("between_hansel_gretel", "Both suspects are on pages between Hansel’s page and Gretel’s.",
             "Hansel and Gretel each appear once. Their own two pages don’t count.", "place",
             between_pages_test("Hansel", "Gretel")),
        Clue("even_page", "Each suspect’s page holds an even number of names.",
             "Every name on the page counts, whatever its length.", "place", _even_page_count),
        Clue("king_and_queen", "Each suspect’s page has both a King and a Queen on it.",
             "Any name beginning with the title King, and any beginning with Queen.", "place",
             page_has_both_test("King", "Queen")),
        Clue("three_bears", "Each suspect’s chapter contains Papa Bear, Mama Bear and Baby Bear.",
             "All three must appear somewhere in the same chapter, spelled exactly like that.", "place",
             chapter_has_all_test(BEARS)),
        Clue("key_letter", "Each suspect’s name contains the first letter of the first name on its page.",
             "Take the first name printed at the top of the page (skip a title such as Mr or Queen) "
             "and note its first letter.", "place", _key_letter),
        Clue("facing_alliterative", "The page facing each suspect’s page carries an alliterative name.",
             "An alliterative name has every word starting with the same letter, title included, "
             "like Peter Piper or Mrs Moss. Facing pages are the two you see side by side.", "place",
             _facing_alliterative),
    ]
    return {x.key: x for x in c}


def solve(reg, clues):
    """Indices that satisfy every clue, and how many remain after each clue in turn."""
    alive = list(range(len(reg.flat)))
    counts = []
    for cl in clues:
        alive = [i for i in alive if cl.test(reg, i)]
        counts.append(len(alive))
    return alive, counts
