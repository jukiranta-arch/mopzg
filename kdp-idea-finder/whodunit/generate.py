"""Build a register and a clue set with exactly two surviving suspects.

Method: fill pages with random names, place the landmark characters, pick
two suspects where every "place" clue holds, give them names that pass every
"word" clue, then keep renaming any other survivor until only the two are
left. Every change is re-checked by the solver, so the finished puzzle is
verified, not assumed.
"""

import random

from .model import (BEARS, PERSON_TITLES, READINGS, Register, catalogue, letters, solve, solve_all_readings,
                    starts_with_title, words)
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


def _word_passes(text, word_clues, reading=None):
    reg = Register([[text]], [("", 0)]).index()
    reg.set_reading(reading or {})
    return all(c.test(reg, 0) for c in word_clues)


def _word_fails_everywhere(text, word_clues):
    """True if the name fails some word clue under every reading, so no slip can keep it alive."""
    return not any(_word_passes(text, word_clues, r) for r in READINGS)


def _key_initial(text):
    ws = words(text)
    return (ws[1] if len(ws) > 1 and ws[0] in PERSON_TITLES else ws[0])[0].upper()


def _holds_everywhere(reg, i, clues):
    ok = True
    for r in READINGS:
        reg.set_reading(r)
        if not all(c.test(reg, i) for c in clues):
            ok = False
            break
    reg.set_reading({})
    return ok


def _plan_suspect_pages(rng, n_pages, chapter_of, first_page_no):
    """Two odd-numbered pages in different chapters, a sensible distance apart, with room
    for Hansel before the first and Gretel after the second."""
    near, far = max(1, n_pages // 12), max(2, n_pages // 3)
    odd = [p for p in range(1, n_pages - 1) if (first_page_no + p) % 2 == 1]
    pairs = [(p, q) for p in odd for q in odd
             if near <= q - p <= far and chapter_of[p] != chapter_of[q]]
    return rng.choice(pairs) if pairs else None


def build_register(rng, n_pages, per_page, n_chapters, first_page_no=1, density=None, between_span=None,
                   bears_share=0.5):
    """Random guests plus landmarks. The two suspect pages are planned first and the
    landmarks placed around them (Wolf nearby, Hansel before, Gretel after, bears in both
    chapters), so the place clues can hold for the suspects while cutting everyone else."""
    d = {"queen": 1 / 30, "king": 1 / 400, "character": 1 / 45, "wolf_every": 5}
    d.update(density or {})
    pages = [[random_name(rng) for _ in range(rng.randint(*per_page))] for _ in range(n_pages)]

    # Chapters of roughly equal length (within about a third), so chapter clues behave predictably.
    step = n_pages / n_chapters
    starts = [0] + sorted({min(n_pages - 1, max(1, int(round(k * step + rng.uniform(-step / 3, step / 3)))))
                           for k in range(1, n_chapters)})
    quotes = rng.sample(CHAPTER_QUOTES, n_chapters) if n_chapters <= len(CHAPTER_QUOTES) else CHAPTER_QUOTES
    chapters = list(zip(quotes, starts))
    for p in starts:                       # a chapter heading and its scene take about a quarter of the page
        del pages[p][int(len(pages[p]) * 0.72):]
    chapter_of = [sum(1 for s in starts if s <= p) - 1 for p in range(n_pages)]
    plan = _plan_suspect_pages(rng, n_pages, chapter_of, first_page_no)
    if not plan:
        raise GenerationError("no room for two suspect pages")
    sp, sq = plan

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
    wolf_pages = set(range(rng.randrange(d["wolf_every"]), n_pages, d["wolf_every"]))
    for p in (sp, sq):
        if not wolf_pages & {p - 1, p, p + 1}:
            wolf_pages.add(rng.choice([x for x in (p - 1, p, p + 1) if 0 <= x < n_pages]))
    for p in sorted(wolf_pages):
        put(p, "Big Bad Wolf")
    # Hansel and Gretel once each, on either side of the suspect pages (in either order). With
    # between_span=(lo, hi) the pages between them are that share of the book, so the clue never
    # knocks out most of it at once ("one clue narrows it to two chapters" is a 1-star complaint).
    gap = max(1, n_pages // 15)
    before, after = rng.randint(max(0, sp - gap), sp - 1), rng.randint(sq + 1, min(n_pages - 1, sq + gap))
    if between_span:
        fits = [(a, b) for a in range(0, sp) for b in range(sq + 1, n_pages)
                if between_span[0] * n_pages <= b - a - 1 <= between_span[1] * n_pages]
        if not fits:
            raise GenerationError("no room for Hansel and Gretel")
        before, after = rng.choice(fits)
    first, second = ("Hansel", "Gretel") if rng.random() < 0.5 else ("Gretel", "Hansel")
    put(before, first)
    put(after, second)
    # The three bears in both suspect chapters and about half of the others.
    for ci, (_, start) in enumerate(chapters):
        end = chapters[ci + 1][1] if ci + 1 < len(chapters) else n_pages
        if ci in (chapter_of[sp], chapter_of[sq]) or rng.random() < bears_share:
            for bear in BEARS:
                put(rng.randrange(start, end), bear)
    reg = Register(pages, chapters, first_page_no).index()
    reg.planned = (sp, sq)
    return reg


# Page clues early: late in the order, the survivors sit only on the suspects' pages
# and a page clue would have nothing left to eliminate.
# The printed order is the suggested order: clues about *where* a guest is come first (hunt for
# landmarks, cross off whole pages), letter clues last, on the few thousand names left. Reviews
# punish letter checks on tens of thousands of names ("would take weeks").
SAMPLE_CLUES = ["king_and_queen", "near_wolf", "odd_page", "between_hansel_gretel", "odd_consonants",
                "ends_consonant", "double_letter", "first_half", "key_letter"]
BOOK_CLUES = ["three_bears", "between_hansel_gretel", "near_wolf", "king_and_queen", "odd_page", "near_queen",
              "odd_consonants", "double_letter", "ends_consonant", "first_half", "even_vowels",
              "last_two_rising", "key_letter"]
PAGE_LEVEL = {"between_hansel_gretel", "near_wolf", "three_bears", "king_and_queen", "odd_page", "near_queen",
              "even_page"}
# Balance targets for a full book (see briefs/2026-09-29_whodunit-design-rules.md).
BOOK_BALANCE = {"between_span": (0.40, 0.60), "bears_share": 0.6, "place_keep_min": 0.30,
                "page_level_keep": (0.02, 0.12)}
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
             density=None, balance=None):
    """Return (register, clues, solution). Raises GenerationError if this seed can't be made to work."""
    rng = random.Random(seed)
    cat = catalogue(queen_window)
    clue_keys = clue_keys or SAMPLE_CLUES
    clues = [cat[k] for k in clue_keys]
    word_clues = [c for c in clues if c.kind == "word"]

    balance = balance or {}
    reg = build_register(rng, n_pages, per_page, n_chapters, first_page_no, density,
                         balance.get("between_span"), balance.get("bears_share", 0.5))

    # 1. The register planned the two suspect pages and put the landmarks around them.
    #    Make the remaining page facts true there (a King and a Queen present, an even
    #    name count). Everything about the suspects must hold under every reading.
    place_clues = [c for c in clues if c.kind == "place"]
    page_pair = reg.planned
    _fix_pages(reg, rng, {c.key for c in clues}, page_pair)

    # Places on those pages where every place clue holds, not a landmark, not first on its page.
    def places(p):
        out = [i for i in range(reg.page_start[p] + 1, reg.page_start[p] + len(reg.pages[p]))
               if reg.flat[i] not in UNIQUE_ANCHORS and words(reg.flat[i])[0] not in ("Queen", "King")
               and _holds_everywhere(reg, i, [c for c in place_clues if c.key != "key_letter"])]
        return rng.choice(out) if out else None
    pair = tuple(places(p) for p in page_pair)
    if None in pair:
        raise GenerationError("no place on a suspect page satisfies the place clues")

    # 2. Name the suspects so they pass every clue, with different lengths for the final deduction.
    #    Suspects never carry a title, so the answer reads the same however titles are counted.
    for n, idx in enumerate(pair):
        for _ in range(20000):
            name = random_name(rng)
            if words(name)[0] in PERSON_TITLES:
                continue
            if not all(_word_passes(name, word_clues, r) for r in READINGS):
                continue
            if n == 1 and len(letters(name)) == len(letters(reg.flat[pair[0]])):
                continue
            p = reg.page_of[idx]
            reg.pages[p][idx - reg.page_start[p]] = name
            reg.index()
            if _holds_everywhere(reg, idx, clues):
                break
        else:
            raise GenerationError("could not name a suspect")
    suspect_names = [reg.flat[i] for i in pair]

    # 3. Rename every other survivor, under any reading, until only the suspects remain.
    for _ in range(max_rounds):
        reg.index()
        by_reading = solve_all_readings(reg, clues)
        extra = sorted({i for alive in by_reading.values() for i in alive} - set(pair))
        if (not all(i in alive for alive in by_reading.values() for i in pair)
                or [reg.flat[i] for i in pair] != suspect_names):
            raise GenerationError("a repair broke a suspect")
        if not extra:
            break
        for i in extra:
            text = reg.flat[i]
            p = reg.page_of[i]
            if text in CHARACTERS:           # a cameo: swap in another character that fails a word clue
                options = [c for c in CHARACTERS if c != text and _word_fails_everywhere(c, word_clues)]
                if not options:
                    raise GenerationError("no character fails the word clues")
                reg.pages[p][i - reg.page_start[p]] = rng.choice(options)
                continue
            if text in UNIQUE_ANCHORS:
                raise GenerationError("a landmark character survived: %s" % text)
            head = words(text)[0]
            opening = i == reg.page_start[p]
            for _ in range(2000):
                new = (head + " " + first_for(rng, head)) if head in ("Queen", "King") else random_name(rng)
                if opening and _key_initial(new) != _key_initial(text):
                    continue                 # the opening name sets the page's key letter: keep it
                if _word_fails_everywhere(new, word_clues):
                    break
            reg.pages[p][i - reg.page_start[p]] = new
    else:
        raise GenerationError("did not converge")

    reg.index()
    for k, alive in solve_all_readings(reg, clues).items():
        assert sorted(alive) == sorted(pair), (READINGS[k], alive, pair)
    alive, counts = solve(reg, clues)
    # Every clue must do real work: remove at least min_cut of what is left before it.
    before = len(reg.flat)
    for c, after in zip(clues, counts):
        if after > before * (1 - min_cut):
            raise GenerationError("clue '%s' barely eliminates anyone (%d -> %d)" % (c.key, before, after))
        before = after
    # Balance, as readers use the clues in any order: no place clue is a knockout on its own,
    # and the page-level clues leave a real but workable list for the letter clues.
    n = len(reg.flat)
    standalone = {c.key: len(solve(reg, [c])[0]) / n for c in clues}
    page_clues = [c for c in clues if c.key in PAGE_LEVEL]
    page_keep = len(solve(reg, page_clues)[0]) / n if page_clues else 1.0
    if balance:
        for c in clues:
            if c.key in PAGE_LEVEL and standalone[c.key] < balance["place_keep_min"]:
                raise GenerationError("clue '%s' alone keeps only %.0f%%" % (c.key, 100 * standalone[c.key]))
        lo, hi = balance["page_level_keep"]
        if not lo <= page_keep <= hi:
            raise GenerationError("page-level clues keep %.1f%%" % (100 * page_keep))
    a, b = pair
    killer = a if len(letters(reg.flat[a])) > len(letters(reg.flat[b])) else b
    checkpoints, page_hints = _checkpoints_and_hints(reg, clues, pair)
    solution = {
        "suspects": [{"name": reg.flat[i], "page": reg.page_no(reg.page_of[i]),
                      "chapter": reg.chapter_of_page[reg.page_of[i]] + 1} for i in pair],
        "killer": reg.flat[killer],
        "counts": counts,
        "pair": list(pair),
        "killer_index": killer,
        "checkpoints": checkpoints,
        "page_hints": page_hints,
        "standalone": standalone,
        "page_level_keep": page_keep,
        "total_names": len(reg.flat),
        "seed": seed,
    }
    return reg, clues, solution


def _checkpoints_and_hints(reg, clues, pair):
    """Checkpoints: pages and names still in play after each clue, used in order.
    Hints for the Verdict pages: for every page without a suspect, the clue that clears it.
    ("single", k) means clue k on its own rules out every guest on the page; ("last", k) means that,
    using the clues in order, the page's last guest falls to clue k (numbered from 1)."""
    reg.set_reading({})
    alive = set(range(len(reg.flat)))
    fell_at = {}                                   # page -> clue number that removed its last guest
    checkpoints = []
    for k, c in enumerate(clues, 1):
        alive = {i for i in alive if c.test(reg, i)}
        pages_left = {reg.page_of[i] for i in alive}
        for p in range(len(reg.pages)):
            if p not in pages_left and p not in fell_at:
                fell_at[p] = k
        checkpoints.append({"clue": k, "pages": len(pages_left), "names": len(alive)})
    alone = [set(solve(reg, [c])[0]) for c in clues]
    suspect_pages = {reg.page_of[i] for i in pair}
    hints = {}
    for p in range(len(reg.pages)):
        if p in suspect_pages:
            continue
        span = range(reg.page_start[p], reg.page_start[p] + len(reg.pages[p]))
        single = next((k for k, keep in enumerate(alone, 1) if not any(i in keep for i in span)), None)
        hints[p] = ("single", single) if single else ("last", fell_at[p])
    return checkpoints, hints


def generate_any(seeds, **kw):
    """Try seeds in turn until one works."""
    last = None
    for s in seeds:
        try:
            return generate(seed=s, **kw)
        except GenerationError as e:
            last = e
    raise GenerationError("no seed worked: %s" % last)
