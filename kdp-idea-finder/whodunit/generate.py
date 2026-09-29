"""Build a register and a clue set with exactly two surviving suspects.

Method: fill pages with random names, place the landmark characters, pick
two suspects where every "place" clue holds, give them names that pass every
"word" clue, then keep renaming any other survivor until only the two are
left. Every change is re-checked by the solver, so the finished puzzle is
verified, not assumed.
"""

import random

from .model import BEARS, Register, catalogue, letters, solve, starts_with_title, words
from .names import (CHARACTERS, CHAPTER_QUOTES, FEMALE, FEMALE_TITLES, FIRST, LAST, MALE, MALE_TITLES,
                    TITLES)

ORDINARY_TITLES = [t for t in TITLES if t not in ("Old", "Little")]
UNIQUE_ANCHORS = {"Hansel", "Gretel", "Big Bad Wolf", *BEARS, *CHARACTERS}
_MALE_FIRST, _FEMALE_FIRST = sorted(set(FIRST) - FEMALE), sorted(set(FIRST) - MALE)


class GenerationError(RuntimeError):
    pass


def first_for(rng, title):
    """A first name that suits the title: no "Queen Bruno" or "Mr Barbara"."""
    if title in MALE_TITLES:
        return rng.choice(_MALE_FIRST)
    if title in FEMALE_TITLES:
        return rng.choice(_FEMALE_FIRST)
    return rng.choice(FIRST)


def random_name(rng):
    r = rng.random()
    f, l = rng.choice(FIRST), rng.choice(LAST)
    if r < 0.38:
        return f
    if r < 0.80:
        return f + " " + l
    t = rng.choice(ORDINARY_TITLES)
    if r < 0.93:
        return t + " " + l
    return t + " " + first_for(rng, t) + " " + l


def _word_passes(text, word_clues):
    reg = Register([[text]], [("", 0)]).index()
    return all(c.test(reg, 0) for c in word_clues)


def build_register(rng, n_pages, per_page, n_chapters, first_page_no=1, density=None):
    d = {"queen": 1 / 30, "king": 1 / 400, "character": 1 / 45, "wolf_every": 5}
    d.update(density or {})
    pages = [[random_name(rng) for _ in range(rng.randint(*per_page))] for _ in range(n_pages)]

    starts = sorted(rng.sample(range(1, n_pages), n_chapters - 1)) if n_chapters > 1 else []
    starts = [0] + starts
    quotes = rng.sample(CHAPTER_QUOTES, n_chapters) if n_chapters <= len(CHAPTER_QUOTES) else CHAPTER_QUOTES
    chapters = list(zip(quotes, starts))
    for p in starts:                       # a chapter heading takes about a tenth of the page
        del pages[p][int(len(pages[p]) * 0.88):]

    taken = set()

    def put(p, name):
        """Place a landmark name, never first on a page and never over another landmark."""
        while True:
            slot = rng.randrange(1, len(pages[p]))
            if (p, slot) not in taken:
                break
        taken.add((p, slot))
        pages[p][slot] = name

    total = sum(len(x) for x in pages)
    for _ in range(int(total * d["queen"])):
        put(rng.randrange(n_pages), "Queen " + first_for(rng, "Queen"))
    for _ in range(int(total * d["king"])):
        put(rng.randrange(n_pages), "King " + first_for(rng, "King"))
    for _ in range(int(total * d["character"])):
        put(rng.randrange(n_pages), rng.choice(CHARACTERS))
    for p in range(rng.randrange(d["wolf_every"]), n_pages, d["wolf_every"]):
        put(p, "Big Bad Wolf")
    # Hansel and Gretel: once each, a fair way apart.
    a = rng.randrange(0, max(1, n_pages // 3))
    b = rng.randrange(min(n_pages - 1, a + max(3, n_pages // 3)), n_pages)
    put(a, "Hansel")
    put(b, "Gretel")
    # The three bears in about half of the chapters.
    for ci, (_, start) in enumerate(chapters):
        end = chapters[ci + 1][1] if ci + 1 < len(chapters) else n_pages
        if rng.random() < 0.5:
            for bear in BEARS:
                put(rng.randrange(start, end), bear)
    return Register(pages, chapters, first_page_no).index()


# Page clues early: late in the order, the survivors sit only on the suspects' pages
# and a page clue would have nothing left to eliminate.
SAMPLE_CLUES = ["near_wolf", "odd_consonants", "even_page", "between_hansel_gretel", "ends_consonant",
                "king_and_queen", "double_letter", "first_half", "key_letter"]
BOOK_CLUES = ["odd_consonants", "near_wolf", "even_page", "ends_consonant", "three_bears", "double_letter",
              "between_hansel_gretel", "near_queen", "first_half", "king_and_queen", "even_vowels",
              "last_two_rising", "key_letter"]
FIXABLE_PAGE_CLUES = {"king_and_queen", "even_page"}


def _fix_pages(reg, rng, keys, page_nos):
    """Make the fixable page-level clues true on the given pages, editing only ordinary names."""
    for p in page_nos:
        names = reg.pages[p]
        if "king_and_queen" in keys:
            for title in ("King", "Queen"):
                if not any(starts_with_title(n, title) for n in names):
                    free = [k for k in range(1, len(names))
                            if names[k] not in UNIQUE_ANCHORS and words(names[k])[0] not in ("King", "Queen")]
                    names[rng.choice(free)] = title + " " + first_for(rng, title)
        if "even_page" in keys and len(names) % 2:
            names.append(random_name(rng))
    reg.index()


def generate(seed=1, n_pages=12, per_page=(150, 175), n_chapters=3,
             clue_keys=None, queen_window=12, first_page_no=1, max_rounds=300, min_cut=0.03,
             density=None):
    """Return (register, clues, solution). Raises GenerationError if this seed can't be made to work."""
    rng = random.Random(seed)
    cat = catalogue(queen_window)
    clue_keys = clue_keys or SAMPLE_CLUES
    clues = [cat[k] for k in clue_keys]
    word_clues = [c for c in clues if c.kind == "word"]

    reg = build_register(rng, n_pages, per_page, n_chapters, first_page_no, density)

    # 1. Pick two suspect pages in different chapters where the structural clues
    #    (Wolf, Hansel and Gretel, bears) already hold, then make the page-level
    #    facts true on them: a King and a Queen present, an even name count.
    place_clues = [c for c in clues if c.kind == "place"]
    structural = [c for c in place_clues if c.key not in FIXABLE_PAGE_CLUES | {"key_letter", "near_queen"}]
    pages = [p for p in range(len(reg.pages)) if all(c.test(reg, reg.page_start[p] + 1) for c in structural)]
    rng.shuffle(pages)
    page_pair = next(((p, q) for p in pages for q in pages
                      if reg.chapter_of_page[p] != reg.chapter_of_page[q]), None)
    if not page_pair:
        raise GenerationError("no two pages in different chapters satisfy the structural clues")
    _fix_pages(reg, rng, {c.key for c in clues}, page_pair)

    # Places on those pages where every place clue holds, not a landmark, not first on its page.
    def places(p):
        out = [i for i in range(reg.page_start[p] + 1, reg.page_start[p] + len(reg.pages[p]))
               if reg.flat[i] not in UNIQUE_ANCHORS and words(reg.flat[i])[0] not in ("Queen", "King")
               and all(c.test(reg, i) for c in place_clues if c.key != "key_letter")]
        return rng.choice(out) if out else None
    pair = tuple(places(p) for p in page_pair)
    if None in pair:
        raise GenerationError("no place on a suspect page satisfies the place clues")

    # 2. Name the suspects so they pass every clue, with different lengths for the final deduction.
    for n, idx in enumerate(pair):
        for _ in range(20000):
            name = random_name(rng)
            if not _word_passes(name, word_clues):
                continue
            if n == 1 and len(letters(name)) == len(letters(reg.flat[pair[0]])):
                continue
            p = reg.page_of[idx]
            reg.pages[p][idx - reg.page_start[p]] = name
            reg.index()
            if all(c.test(reg, idx) for c in clues):
                break
        else:
            raise GenerationError("could not name a suspect")
    suspect_names = [reg.flat[i] for i in pair]

    # 3. Rename every other survivor until only the suspects remain.
    for _ in range(max_rounds):
        reg.index()
        alive, counts = solve(reg, clues)
        extra = [i for i in alive if i not in pair]
        if not all(i in alive for i in pair) or [reg.flat[i] for i in pair] != suspect_names:
            raise GenerationError("a repair broke a suspect")
        if not extra:
            break
        for i in extra:
            text = reg.flat[i]
            if text in UNIQUE_ANCHORS:
                raise GenerationError("a landmark character survived: %s" % text)
            head = words(text)[0]
            for _ in range(2000):
                new = (head + " " + first_for(rng, head)) if head in ("Queen", "King") else random_name(rng)
                if not _word_passes(new, word_clues):
                    break
            p = reg.page_of[i]
            reg.pages[p][i - reg.page_start[p]] = new
    else:
        raise GenerationError("did not converge")

    reg.index()
    alive, counts = solve(reg, clues)
    assert sorted(alive) == sorted(pair), (alive, pair)
    # Every clue must do real work: remove at least min_cut of what is left before it.
    before = len(reg.flat)
    for c, after in zip(clues, counts):
        if after > before * (1 - min_cut):
            raise GenerationError("clue '%s' barely eliminates anyone (%d -> %d)" % (c.key, before, after))
        before = after
    a, b = pair
    killer = a if len(letters(reg.flat[a])) > len(letters(reg.flat[b])) else b
    solution = {
        "suspects": [{"name": reg.flat[i], "page": reg.page_no(reg.page_of[i]),
                      "chapter": reg.chapter_of_page[reg.page_of[i]] + 1} for i in pair],
        "killer": reg.flat[killer],
        "counts": counts,
        "total_names": len(reg.flat),
        "seed": seed,
    }
    return reg, clues, solution


def generate_any(seeds, **kw):
    """Try seeds in turn until one works."""
    last = None
    for s in seeds:
        try:
            return generate(seed=s, **kw)
        except GenerationError as e:
            last = e
    raise GenerationError("no seed worked: %s" % last)
