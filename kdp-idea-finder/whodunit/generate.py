"""Build a register and a clue set with exactly two surviving suspects.

Method: fill pages with random first names, plan two suspect pages (odd-numbered,
in different indoor chapters) and place the landmarks around them, give the
suspects names that pass every clue, then keep renaming any other survivor
until only the two are left. Every change is re-checked by the solver under
every reading, so the finished puzzle is verified, not assumed.
"""

import random

from .model import BEARS, READINGS, ROYAL_WORDS, Register, catalogue, letters, solve, solve_all_readings, words
from .names import CHARACTERS, FIRST, PLACES_INDOOR, PLACES_OUTDOOR, ROYALS

LANDMARKS = {"Hansel", "Gretel", "Big Bad Wolf", *BEARS}          # can never be renamed
CAST = set(CHARACTERS) | set(ROYALS) | LANDMARKS                   # printed in italics
ROYALS_BY_TITLE = [r for r in ROYALS if words(r)[0] in ROYAL_WORDS]  # royal under every reading


class GenerationError(RuntimeError):
    pass


def random_name(rng):
    return rng.choice(FIRST)


def _word_passes(text, word_clues, reading=None):
    reg = Register([[text]], [("", 0)]).index()
    reg.set_reading(reading or {})
    return all(c.test(reg, 0) for c in word_clues)


def _word_fails_everywhere(text, word_clues):
    """True if the name fails some word clue under every reading, so no slip can keep it alive."""
    return not any(_word_passes(text, word_clues, r) for r in READINGS)


def _holds_everywhere(reg, i, clues):
    ok = True
    for r in READINGS:
        reg.set_reading(r)
        if not all(c.test(reg, i) for c in clues):
            ok = False
            break
    reg.set_reading({})
    return ok


def _plan_suspect_pages(rng, n_pages, chapter_of, indoor, first_page_no):
    """Two odd-numbered pages in different indoor chapters, a sensible distance apart, with room
    for Hansel before the first and Gretel after the second."""
    near, far = max(1, n_pages // 12), max(2, n_pages // 2)
    odd = [p for p in range(1, n_pages - 1)
           if (first_page_no + p) % 2 == 1 and chapter_of[p] in indoor]
    pairs = [(p, q) for p in odd for q in odd
             if near <= q - p <= far and chapter_of[p] != chapter_of[q]]
    return rng.choice(pairs) if pairs else None


def build_register(rng, n_pages, per_page, n_chapters, n_indoor, first_page_no=1, density=None,
                   between_span=None, bears_share=0.5):
    """Random guests plus landmarks. The two suspect pages are planned first and the landmarks
    placed around them (Wolf nearby, Hansel before, Gretel after, bears in both chapters), so the
    place clues can hold for the suspects while cutting everyone else."""
    d = {"character": 1 / 45, "royal_pages": 0.6, "wolf_every": 5}
    d.update(density or {})
    pages = [[random_name(rng) for _ in range(rng.randint(*per_page))] for _ in range(n_pages)]

    # Chapters of roughly equal length, each a place in the palace: n_indoor rooms, the rest outdoors.
    step = n_pages / n_chapters
    starts = [0] + sorted({min(n_pages - 1, max(1, int(round(k * step + rng.uniform(-step / 3, step / 3)))))
                           for k in range(1, n_chapters)})
    n_chapters = len(starts)
    places = rng.sample(sorted(PLACES_INDOOR), n_indoor) + \
        rng.sample(sorted(PLACES_OUTDOOR), n_chapters - n_indoor)
    rng.shuffle(places)
    chapters = list(zip(places, starts))
    indoor = {i for i, place in enumerate(places) if place in PLACES_INDOOR}
    for p in starts:                       # a chapter heading and its scene take about a quarter of the page
        del pages[p][int(len(pages[p]) * 0.72):]
    chapter_of = [sum(1 for s in starts if s <= p) - 1 for p in range(n_pages)]
    plan = _plan_suspect_pages(rng, n_pages, chapter_of, indoor, first_page_no)
    if not plan:
        raise GenerationError("no room for two suspect pages")
    sp, sq = plan

    taken = set()

    def put(p, names_):
        """Place landmark names one after another, never first on a page, never over another landmark."""
        for _ in range(1000):
            slot = rng.randrange(1, len(pages[p]) - len(names_) + 1)
            if not any((p, slot + k) in taken for k in range(len(names_))):
                break
        else:
            raise GenerationError("page %d is full" % p)
        for k, name in enumerate(names_):
            taken.add((p, slot + k))
            pages[p][slot + k] = name

    total = sum(len(x) for x in pages)
    for _ in range(int(total * d["character"])):
        put(rng.randrange(n_pages), [rng.choice(CHARACTERS)])
    for _ in range(int(n_pages * d["royal_pages"])):
        put(rng.randrange(n_pages), [rng.choice(ROYALS)])
    wolf_pages = set(range(rng.randrange(d["wolf_every"]), n_pages, d["wolf_every"]))
    for p in (sp, sq):
        if not wolf_pages & {p - 1, p, p + 1}:
            wolf_pages.add(rng.choice([x for x in (p - 1, p, p + 1) if 0 <= x < n_pages]))
    for p in sorted(wolf_pages):
        put(p, ["Big Bad Wolf"])
    # Hansel and Gretel once each, on either side of the suspect pages (in either order).
    gap = max(1, n_pages // 15)
    before, after = rng.randint(max(0, sp - gap), sp - 1), rng.randint(sq + 1, min(n_pages - 1, sq + gap))
    if between_span:
        fits = [(a, b) for a in range(0, sp) for b in range(sq + 1, n_pages)
                if between_span[0] * n_pages <= b - a - 1 <= between_span[1] * n_pages]
        if not fits:
            raise GenerationError("no room for Hansel and Gretel")
        before, after = rng.choice(fits)
    first, second = ("Hansel", "Gretel") if rng.random() < 0.5 else ("Gretel", "Hansel")
    put(before, [first])
    put(after, [second])
    # The Three Bears, standing together, in both suspect chapters and some of the others.
    for ci, (_, start) in enumerate(chapters):
        end = chapters[ci + 1][1] if ci + 1 < len(chapters) else n_pages
        if ci in (chapter_of[sp], chapter_of[sq]) or rng.random() < bears_share:
            put(rng.randrange(start, end), list(BEARS))
    reg = Register(pages, chapters, first_page_no, indoor=indoor, cast=set(CAST)).index()
    reg.planned = (sp, sq)
    reg.landmark_slots = taken
    return reg


# The printed order is the suggested order. Every page must matter, so the opening clues are
# quick checks you make on every name, at a glance (first letter, last letter, a double letter):
# they thin every page and empty none. Only then come the clues about where the killer was,
# then highlighting around characters, then the counting clues on the last few hundred names.
# (A clue that blanks most pages before any name is read is the Guest List's 1-star complaint.)
SAMPLE_CLUES = ["first_half", "ends_consonant", "double_letter", "near_wolf", "royal_on_page",
                "between_hansel_gretel", "chapter_indoors", "near_character", "key_letter"]
BOOK_CLUES = ["first_half", "ends_consonant", "double_letter", "near_wolf", "royal_on_page",
              "between_hansel_gretel", "chapter_indoors", "three_bears", "near_character", "odd_consonants",
              "even_vowels", "key_letter"]
GLANCE = {"first_half", "ends_consonant", "double_letter"}      # checked on every name at a glance
CHUNK = {"chapter_indoors", "three_bears", "between_hansel_gretel", "odd_page"}
HUNT = {"near_wolf", "royal_on_page", "near_character"}
PAGE_LEVEL = CHUNK | HUNT
# Balance targets for a full book (see briefs/2026-09-29_winners-samples.md).
BOOK_BALANCE = {"between_span": (0.40, 0.60), "bears_share": 0.5, "place_keep_min": 0.30,
                "page_level_keep": (0.01, 0.08)}


def _fix_pages(reg, rng, keys, page_nos):
    """Make the fixable page facts true on the suspect pages, editing only ordinary names."""
    for p in page_nos:
        names = reg.pages[p]
        if "royal_on_page" in keys and not any(words(n)[0] in ROYAL_WORDS for n in names):
            free = [k for k in range(1, len(names)) if (p, k) not in reg.landmark_slots and names[k] not in CAST]
            k = rng.choice(free)
            names[k] = rng.choice(ROYALS_BY_TITLE)
            reg.landmark_slots.add((p, k))
    reg.index()


def generate(seed=1, n_pages=30, per_page=(200, 225), n_chapters=4, n_indoor=None,
             clue_keys=None, cast_window=10, first_page_no=1, max_rounds=300, min_cut=0.03,
             density=None, balance=None):
    """Return (register, clues, solution). Raises GenerationError if this seed can't be made to work."""
    rng = random.Random(seed)
    cat = catalogue(cast_window)
    clue_keys = clue_keys or SAMPLE_CLUES
    clues = [cat[k] for k in clue_keys]
    word_clues = [c for c in clues if c.kind == "word"]
    n_indoor = n_indoor or max(2, round(n_chapters * 0.6))

    balance = balance or {}
    reg = build_register(rng, n_pages, per_page, n_chapters, n_indoor, first_page_no, density,
                         balance.get("between_span"), balance.get("bears_share", 0.5))

    # 1. Suspect pages were planned with the landmarks around them; make the remaining page facts
    #    true there. Everything about the suspects must hold under every reading.
    place_clues = [c for c in clues if c.kind == "place"]
    page_pair = reg.planned
    _fix_pages(reg, rng, {c.key for c in clues}, page_pair)

    def places(p):
        out = [i for i in range(reg.page_start[p] + 1, reg.page_start[p] + len(reg.pages[p]))
               if reg.flat[i] not in CAST
               and _holds_everywhere(reg, i, [c for c in place_clues if c.key != "key_letter"])]
        return rng.choice(out) if out else None
    pair = tuple(places(p) for p in page_pair)
    if None in pair:
        raise GenerationError("no place on a suspect page satisfies the place clues")

    # 2. Name the suspects so they pass every clue, with different lengths for the final deduction.
    #    If the key-letter clue is used, the page's opening name is chosen to fit the suspect's name.
    fitting = [n for n in FIRST if all(_word_passes(n, word_clues, r) for r in READINGS)]
    rng.shuffle(fitting)
    keyed = "key_letter" in {c.key for c in clues}
    for n, idx in enumerate(pair):
        p = reg.page_of[idx]
        for name in fitting:
            if n == 1 and len(letters(name)) == len(letters(reg.flat[pair[0]])):
                continue
            reg.pages[p][idx - reg.page_start[p]] = name
            if keyed and letters(reg.pages[p][0])[0] not in letters(name):
                reg.pages[p][0] = rng.choice([f for f in FIRST if f[0].upper() in letters(name)])
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
            if text in LANDMARKS:
                raise GenerationError("a landmark survived: %s" % text)
            if text in CAST:                 # a cameo: swap in another of its kind that fails a word clue
                pool = ROYALS if text in ROYALS else CHARACTERS
                if text in ROYALS and words(text)[0] in ROYAL_WORDS:
                    pool = ROYALS_BY_TITLE   # keep the page royal under every reading
                options = [c for c in pool if c != text and _word_fails_everywhere(c, word_clues)]
                if not options:
                    raise GenerationError("no cameo fails the word clues")
                reg.pages[p][i - reg.page_start[p]] = rng.choice(options)
                continue
            opening = i == reg.page_start[p]
            for _ in range(2000):
                new = random_name(rng)
                if opening and new[0] != text[0]:
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
    # Balance, as readers use the clues in any order: no page-level clue is a knockout on its own,
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
        # The opening glance clues must leave every page (or nearly every page) with names in play.
        opening = 0
        while opening < len(clues) and clues[opening].key in GLANCE:
            opening += 1
        if opening:
            pages_left = len({reg.page_of[i] for i in solve(reg, clues[:opening])[0]})
            if pages_left < 0.95 * len(reg.pages):
                raise GenerationError("the opening clues empty %d pages" % (len(reg.pages) - pages_left))
    a, b = pair
    killer = a if len(letters(reg.flat[a])) > len(letters(reg.flat[b])) else b
    solution = {
        "suspects": [{"name": reg.flat[i], "page": reg.page_no(reg.page_of[i]),
                      "chapter": reg.chapter_of_page[reg.page_of[i]] + 1} for i in pair],
        "killer": reg.flat[killer],
        "counts": counts,
        "pair": list(pair),
        "killer_index": killer,
        "checkpoints": _checkpoints(reg, clues),
        "standalone": standalone,
        "page_level_keep": page_keep,
        "total_names": len(reg.flat),
        "seed": seed,
    }
    return reg, clues, solution


def _checkpoints(reg, clues):
    """Pages and names still in play after each clue, using the clues in order."""
    reg.set_reading({})
    alive = set(range(len(reg.flat)))
    out = []
    for k, c in enumerate(clues, 1):
        alive = {i for i in alive if c.test(reg, i)}
        out.append({"clue": k, "key": c.key, "pages": len({reg.page_of[i] for i in alive}), "names": len(alive)})
    return out


def generate_any(seeds, **kw):
    """Try seeds in turn until one works."""
    last = None
    for s in seeds:
        try:
            return generate(seed=s, **kw)
        except GenerationError as e:
            last = e
    raise GenerationError("no seed worked: %s" % last)
