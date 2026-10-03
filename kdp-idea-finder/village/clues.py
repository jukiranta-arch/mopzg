"""The clue library: every kind of clue the winning books use, as factories.

Each factory returns a Clue with
- `rule`: the plain sentence printed after "Rule:" (village/check_book.py parses these sentences on its own);
- `how`: one or two sentences on how to apply it;
- `test(led, reading)`: one verdict per entry, under one of the readings (book.READINGS);
- `place(ctx)` for hunt clues: puts the clue's famous names into the ledger so that the killer's page passes
  under every reading and roughly half of the ledger fails;
- `fix(ctx)` for clues about the killer's own spot: adjusts the entries around the killer once it is placed;
- `word(name, reading)` for clues about the name alone.

Sources (briefs/2026-09-29_winners-samples.md and the Guest List, Autumn Killer and Eliminate samples):
Who Killed Mr Darcy?, The Killer Was On The Guest List, The Autumn Killer, The Killer Never Checked In.
"""

import re
from dataclasses import dataclass, field

VOWELS = set("AEIOU")


def letters(name):
    return re.sub(r"[^A-Za-z]", "", name).upper()


def first_of(name):
    return name.split()[0]


def surname_of(name):
    parts = name.split()
    return parts[-1] if len(parts) > 1 else ""


def vowel(c, reading):
    return c in VOWELS or (c == "Y" and bool(reading.get("y_vowel")))


def article(name):
    return "an" if name[0] in "AEIOU" else "a"


def join_and(names):
    names = list(names)
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def join_or(names):
    names = list(names)
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]


@dataclass
class Clue:
    key: str
    kind: str                     # "hunt", "word", "spot" (about the killer's own spot) or "chain"
    rule: str
    how: str
    test: object
    title: str = ""
    story: str = ""
    place: object = None          # place(ctx): before the killer is chosen
    fix: object = None            # fix(ctx): after the killer is placed
    word: object = None           # word(name, reading) for word and chain clues
    landmarks: tuple = ()         # famous names this clue uses
    example: str = ""


# ---------------------------------------------------------------- word clues

def _word_clue(key, rule, how, fn, kind="word"):
    c = Clue(key, kind, rule, how, lambda led, reading: [fn(n, reading) for n in led.flat])
    c.word = fn
    return c


def scope_text(scope):
    return {"whole": "name", "first": "first name", "surname": "surname"}[scope]


def part(name, scope):
    return {"whole": name, "first": first_of(name), "surname": surname_of(name)}[scope]


def odd_consonants(scope="whole"):
    return _word_clue("odd_consonants_" + scope,
                      "The killer's %s has an odd number of consonants." % scope_text(scope),
                      "Count every letter that isn't a vowel. Y is always a consonant.",
                      lambda n, r: bool(part(n, scope)) and sum(not vowel(c, r) for c in letters(part(n, scope))) % 2 == 1)


def even_vowels(scope="whole"):
    return _word_clue("even_vowels_" + scope,
                      "The killer's %s has an even number of vowels." % scope_text(scope),
                      "Count every A, E, I, O and U. Y is not a vowel. None counts as even.",
                      lambda n, r: bool(part(n, scope)) and sum(vowel(c, r) for c in letters(part(n, scope))) % 2 == 0)


def ends_consonant(scope="whole"):
    return _word_clue("ends_consonant_" + scope, "The killer's %s ends in a consonant." % scope_text(scope),
                      "Look only at the very last letter. Y is a consonant.",
                      lambda n, r: bool(part(n, scope)) and not vowel(letters(part(n, scope))[-1], r))


def ends_vowel(scope="whole"):
    return _word_clue("ends_vowel_" + scope, "The killer's %s ends in a vowel." % scope_text(scope),
                      "Look only at the very last letter. The vowels are A, E, I, O and U; Y is not one.",
                      lambda n, r: bool(part(n, scope)) and vowel(letters(part(n, scope))[-1], r))


def double_letter(scope="whole"):
    return _word_clue("double_" + scope, "The killer's %s contains a double letter." % scope_text(scope),
                      "Two of the same letter side by side, like the “ll” in Bella. Letters split by a "
                      "space don't count.",
                      lambda n, r: any(re.search(r"([a-z])\1", w.lower()) for w in part(n, scope).split()))


def no_double_letter(scope="whole"):
    return _word_clue("no_double_" + scope, "The killer's %s has no double letter." % scope_text(scope),
                      "No two of the same letter sit side by side, like the “ll” in Bella.",
                      lambda n, r: bool(part(n, scope)) and
                      not any(re.search(r"([a-z])\1", w.lower()) for w in part(n, scope).split()))


def last_two_in_order():
    return _word_clue("last_two_in_order", "The last two letters of the killer's name are in alphabetical order.",
                      "Marlow ends O, W: in order. Bella ends L, A: not in order. A double letter at the end, like "
                      "the “nn” in Ann, is not in order.",
                      lambda n, r: len(letters(n)) > 1 and letters(n)[-2] < letters(n)[-1])


def none_of(chars):
    chars = chars.upper()
    shown = join_or(list(chars))
    return _word_clue("none_of_" + chars, "The killer's name contains no %s." % shown,
                      "Check every letter of the whole name, first name and surname.",
                      lambda n, r: not set(letters(n)) & set(chars))


def contains(ch):
    ch = ch.upper()
    return _word_clue("contains_" + ch, "The killer's name contains %s %s." % (article(ch), ch),
                      "Anywhere in the whole name, first name or surname.",
                      lambda n, r: ch in letters(n))


def surname_longer():
    return _word_clue("surname_longer", "The killer's surname is longer than the killer's first name.",
                      "Count the letters in each half of the name. A name with no surname is crossed out.",
                      lambda n, r: bool(surname_of(n)) and len(letters(surname_of(n))) > len(letters(first_of(n))))


def first_at_least(k):
    return _word_clue("first_at_least_%d" % k, "The killer's first name has at least %d letters." % k,
                      "Count only the first name.", lambda n, r: len(letters(first_of(n))) >= k)


def whole_at_most(k):
    return _word_clue("whole_at_most_%d" % k, "The killer's name has at most %d letters." % k,
                      "Count every letter of the whole name; spaces don't count.",
                      lambda n, r: len(letters(n)) <= k)


def initial_in_surname():
    return _word_clue("initial_in_surname", "The first letter of the killer's first name appears again in the "
                      "killer's surname.", "Take the first letter of the first name and look for it anywhere in the "
                      "surname. A name with no surname is crossed out.",
                      lambda n, r: bool(surname_of(n)) and letters(n)[0] in letters(surname_of(n)))


def repeated_letter(scope="surname"):
    return _word_clue("repeated_" + scope, "Some letter appears at least twice in the killer's %s." % scope_text(scope),
                      "The two need not sit side by side: Ellison qualifies, with two Ls.",
                      lambda n, r: bool(part(n, scope)) and len(set(letters(part(n, scope)))) < len(letters(part(n, scope))))


def all_letters_different():
    return _word_clue("all_different", "No letter appears twice in the killer's name.",
                      "Every letter of the whole name is different. Ada fails: it has two As.",
                      lambda n, r: len(set(letters(n))) == len(letters(n)))


def at_least_vowels(k):
    return _word_clue("at_least_vowels_%d" % k, "The killer's name has at least %d vowels." % k,
                      "Count every A, E, I, O and U in the whole name. Y is not a vowel.",
                      lambda n, r: sum(vowel(c, r) for c in letters(n)) >= k)


def surname_begins_consonant():
    return _word_clue("surname_begins_consonant", "The killer's surname begins with a consonant.",
                      "Look only at the first letter of the surname. A name with no surname is crossed out.",
                      lambda n, r: bool(surname_of(n)) and not vowel(letters(surname_of(n))[0], r))


def alphabet_neighbours():
    return _word_clue("alphabet_neighbours", "Two letters that sit side by side in the killer's name are also "
                      "neighbours in the alphabet.",
                      "Like the S and T in Stella, or the E and D in Edith, in either order. Letters split by a space "
                      "don't count.",
                      lambda n, r: any(abs(ord(a) - ord(b)) == 1 for w in n.split()
                                       for a, b in zip(letters(w), letters(w)[1:])))


def even_length():
    return _word_clue("even_length", "The killer's name has an even number of letters.",
                      "Count every letter of the whole name; spaces don't count.",
                      lambda n, r: len(letters(n)) % 2 == 0)


# ---------------------------------------------------------------- chain clues (use an earlier answer)

def chain_last_letter(prev_label, prev_name):
    last = letters(prev_name)[-1]
    c = _word_clue("chain", "The killer's name contains the last letter of the %s killer's name." % prev_label,
                   "Use your answer from the %s. Take the very last letter of that name; this killer's name "
                   "contains it somewhere." % prev_label, lambda n, r: last in letters(n), kind="chain")
    return c


def chain_first_letter_of_surname(prev_label, prev_name):
    ch = letters(surname_of(prev_name) or prev_name)[0]
    return _word_clue("chain", "The killer's name contains the first letter of the %s killer's surname." % prev_label,
                      "Use your answer from the %s. Take the first letter of that surname; this killer's name "
                      "contains it somewhere." % prev_label, lambda n, r: ch in letters(n), kind="chain")


def chain_same_first_length(prev_label, prev_name):
    k = len(letters(first_of(prev_name)))
    return _word_clue("chain", "The killer's first name has as many letters as the %s killer's first name." % prev_label,
                      "Use your answer from the %s and count the letters of its first name." % prev_label,
                      lambda n, r: len(letters(first_of(n))) == k, kind="chain")


def chain_shares_no_letter(prev_label, prev_name):
    used = set(letters(first_of(prev_name)))
    return _word_clue("chain", "The killer's surname shares no letter with the %s killer's first name." % prev_label,
                      "Use your answer from the %s. A name with no surname is crossed out." % prev_label,
                      lambda n, r: bool(surname_of(n)) and not set(letters(surname_of(n))) & used, kind="chain")


# ---------------------------------------------------------------- hunt clues (about where the killer is)

def _pages_with(led, name):
    return {led.page_of[i] for i, n in enumerate(led.flat) if n == name}


def near_page(name, others=2):
    """Darcy: within one page of a recurring famous name."""
    def test(led, r):
        ps = _pages_with(led, name)
        if not r.get("near_page_only"):
            ps = {q for p in ps for q in (p - 1, p, p + 1)}
        return [p in ps for p in led.page_of]

    def place(ctx):
        far = [p for p in range(ctx.n_pages) if abs(p - ctx.kp) > 2]
        for p in {ctx.kp} | set(ctx.rng.sample(far, others)):
            ctx.put(name, p)
    return Clue("near_page", "hunt", "The killer is within one page of %s %s." % (article(name), name),
                "“Within one page” means the page before, the same page or the page after. %s appears "
                "more than once; any appearance counts." % name, test, place=place, landmarks=(name,))


def within_pages(name, n):
    """Darcy and the Guest List: within N pages of a name that appears once."""
    def test(led, r):
        (q,) = _pages_with(led, name)
        w = n + r.get("pages", 0)
        return [abs(p - q) <= w for p in led.page_of]

    def place(ctx):
        q = ctx.rng.choice([p for p in range(ctx.n_pages) if abs(p - ctx.kp) <= n - 1])
        ctx.put(name, q)
    return Clue("within_pages", "hunt", "The killer is within %d pages of %s." % (n, name),
                "%s appears only once. Count pages from that page: within %d pages means any page up to %d before "
                "or after it, or the same page." % (name, n, n), test, place=place, landmarks=(name,))


def beyond_pages(name, n):
    def test(led, r):
        (q,) = _pages_with(led, name)
        w = n + r.get("pages", 0)
        return [abs(p - q) > w for p in led.page_of]

    def place(ctx):
        q = ctx.rng.choice([p for p in range(ctx.n_pages) if abs(p - ctx.kp) >= n + 2])
        ctx.put(name, q)
    return Clue("beyond_pages", "hunt", "The killer is more than %d pages away from %s." % (n, name),
                "%s appears only once. Cross out that page and the %d pages either side of it." % (name, n),
                test, place=place, landmarks=(name,))


def between(a, b):
    def test(led, r):
        (pa,), (pb,) = _pages_with(led, a), _pages_with(led, b)
        lo, hi = min(pa, pb), max(pa, pb)
        if r.get("between_inclusive"):
            return [lo <= p <= hi for p in led.page_of]
        return [lo < p < hi for p in led.page_of]

    def place(ctx):
        for _ in range(200):
            gap = ctx.rng.randint(9, 11)
            lo = ctx.rng.randint(0, ctx.n_pages - gap - 2)
            pa, pb = (lo, lo + gap + 1) if ctx.rng.random() < 0.5 else (lo + gap + 1, lo)
            if min(pa, pb) + 2 <= ctx.kp <= max(pa, pb) - 2:
                ctx.put(a, pa)
                ctx.put(b, pb)
                return
        raise ValueError("no room for between")
    return Clue("between", "hunt", "The killer is between %s's page and %s's page." % (a, b),
                "%s and %s each appear only once. Their own two pages don't count: the killer's page lies somewhere "
                "in between." % (a, b), test, place=place, landmarks=(a, b))


def group_chapter_not(group, label, note):
    n = len(group)

    def test(led, r):
        seen = {}
        for i, x in enumerate(led.flat):
            if x in group:
                seen.setdefault(led.chapter_of_page[led.page_of[i]], set()).add(x)
        full = {ch for ch, s in seen.items() if len(s) == n}
        return [led.chapter_of_page[p] not in full for p in led.page_of]

    def place(ctx):
        kch = ctx.ch_of[ctx.kp]
        full = set(ctx.rng.sample([c for c in range(ctx.n_ch) if c != kch], 2))
        for ch in range(ctx.n_ch):
            chosen = group if ch in full else ctx.rng.sample(group, ctx.rng.randint(1, n - 1))
            for g in chosen:
                ctx.put(g, ctx.rng.choice([p for p in range(ctx.n_pages) if ctx.ch_of[p] == ch]))
    word = ["", "one", "two", "three", "four", "five", "six"][n]
    return Clue("group_chapter", "hunt", "The killer is not in a chapter that contains all %s %s." % (word, label),
                "The %s are %s: %s, exactly as written. All %s must appear somewhere in the chapter, in any order. "
                "More than one chapter may contain all of them." % (label, note, join_and(group), word),
                test, place=place, landmarks=tuple(group))


def in_chapter_with(name):
    def test(led, r):
        chs = {led.chapter_of_page[p] for p in _pages_with(led, name)}
        return [led.chapter_of_page[p] in chs for p in led.page_of]

    def place(ctx):
        kch = ctx.ch_of[ctx.kp]
        other = ctx.rng.choice([c for c in range(ctx.n_ch) if c != kch])
        for ch in (kch, other):
            ctx.put(name, ctx.rng.choice([p for p in range(ctx.n_pages) if ctx.ch_of[p] == ch]))
    return Clue("in_chapter_with", "hunt", "The killer is in a chapter where %s appears." % name,
                "%s appears in more than one chapter. Keep every chapter that holds one, and cross out the "
                "rest." % name, test, place=place, landmarks=(name,))


def chapter_exactly_twice(name):
    def test(led, r):
        counts = {}
        for p in [led.page_of[i] for i, n in enumerate(led.flat) if n == name]:
            counts[led.chapter_of_page[p]] = counts.get(led.chapter_of_page[p], 0) + 1
        ok = {ch for ch, c in counts.items() if (c >= 2 if r.get("at_least") else c == 2)}
        return [led.chapter_of_page[p] in ok for p in led.page_of]

    def place(ctx):
        kch = ctx.ch_of[ctx.kp]
        others = [c for c in range(ctx.n_ch) if c != kch]
        ctx.rng.shuffle(others)
        plan = {kch: 2, others[0]: 2, others[1]: 1, others[2]: 1}
        for ch, k in plan.items():
            pages = [p for p in range(ctx.n_pages) if ctx.ch_of[p] == ch]
            for p in ctx.rng.sample(pages, k):
                ctx.put(name, p)
    return Clue("chapter_twice", "hunt", "The killer is in a chapter where %s appears exactly twice." % name,
                "Count the %ss in each chapter. Keep only the chapters with exactly two." % name,
                test, place=place, landmarks=(name,))


def duo_chapters_not(duos, label):
    """Darcy: not in a chapter that opens and closes with a famous duo."""
    def test(led, r):
        bad = set()
        for k, (_, s) in enumerate(led.chapters):
            e = (led.chapters[k + 1][1] if k + 1 < len(led.chapters) else len(led.pages)) - 1
            if (led.pages[s][0], led.pages[e][-1]) in duos:
                bad.add(k)
        return [led.chapter_of_page[p] not in bad for p in led.page_of]

    def place(ctx):
        kch = ctx.ch_of[ctx.kp]
        chs = ctx.rng.sample([c for c in range(ctx.n_ch) if c != kch], len(duos))
        for (a, b), ch in zip(duos, chs):
            s = min(p for p in range(ctx.n_pages) if ctx.ch_of[p] == ch)
            e = max(p for p in range(ctx.n_pages) if ctx.ch_of[p] == ch)
            ctx.put(a, s, at=0)
            ctx.put(b, e, at=-1)
    names = [x for d in duos for x in d]
    return Clue("duo_chapters", "hunt", "The killer is not in a chapter that opens and closes with %s." % label,
                "Three chapters begin and end with the two halves of a famous pair: the chapter's very first name "
                "and its very last name. The pairs are %s." % join_and("%s and %s" % d for d in duos),
                test, place=place, landmarks=tuple(names))


def pair_page(a, b):
    def test(led, r):
        pa, pb = _pages_with(led, a), _pages_with(led, b)
        ps = (pa | pb) if r.get("pair_either") else (pa & pb)
        return [p in ps for p in led.page_of]

    def place(ctx):
        both = {ctx.kp} | set(ctx.rng.sample(range(ctx.n_pages), ctx.n_pages // 2 - 1))
        for p in both:
            ctx.put(a, p)
            ctx.put(b, p)
        for p in ctx.rng.sample([p for p in range(ctx.n_pages) if p not in both], 3):
            ctx.put(ctx.rng.choice((a, b)), p)
    return Clue("pair_page", "hunt", "The killer's page contains both %s %s and %s %s." % (article(a), a, article(b), b),
                "Both names must be on the page, anywhere on it.", test, place=place, landmarks=(a, b))


def one_not_both(a, b):
    def test(led, r):
        pa, pb = _pages_with(led, a), _pages_with(led, b)
        ps = (pa | pb) if r.get("xor_inclusive") else (pa ^ pb)
        return [p in ps for p in led.page_of]

    def place(ctx):
        pages = list(range(ctx.n_pages))
        ctx.rng.shuffle(pages)
        rest = [p for p in pages if p != ctx.kp]
        ctx.put(ctx.rng.choice((a, b)), ctx.kp)
        for p in rest[:5]:
            ctx.put(a, p)
            ctx.put(b, p)
        for p in rest[5:9]:
            ctx.put(ctx.rng.choice((a, b)), p)
    return Clue("one_not_both", "hunt", "The killer's page contains %s %s or %s %s, but not both." % (
        article(a), a, article(b), b),
        "Keep pages with exactly one of the two. Cross out pages with both, and pages with neither.",
        test, place=place, landmarks=(a, b))


def near_group(group, label, plural, n=10):
    """Darcy and the Guest List: within N names of one of a group, counted in reading order."""
    def test(led, r):
        w = n + r.get("window", 0)
        out = [False] * len(led.flat)
        for j, x in enumerate(led.flat):
            if x in group:
                for k in range(max(0, j - w), min(len(out), j + w + 1)):
                    if k != j:
                        out[k] = True
        return out

    def place(ctx):
        for _ in range(ctx.scattered):
            ctx.put(ctx.rng.choice(group), ctx.rng.randrange(ctx.n_pages))

    def fix(ctx):
        ctx.put(ctx.rng.choice(group), ctx.kp, near=ctx.kpos, window=n)
    return Clue("near_group", "hunt", "The killer is within %d names of %s." % (n, label),
                "%s are %s. Count names in reading order: the very next name is 1 away, and the count carries on "
                "onto the previous or next page." % (plural, join_and(group)),
                test, place=place, fix=fix, landmarks=tuple(group))


def not_on_page_with(group, label):
    def test(led, r):
        ps = set()
        for g in group:
            ps |= _pages_with(led, g)
        return [p not in ps for p in led.page_of]

    def place(ctx):
        others = [p for p in range(ctx.n_pages) if p != ctx.kp]
        for p in ctx.rng.sample(others, ctx.n_pages // 2):
            ctx.put(ctx.rng.choice(group), p)
    return Clue("not_on_page_with", "hunt", "The killer's page contains none of %s." % label,
                "%s means %s. Cross out every page where any of them appears." % (label[0].upper() + label[1:],
                                                                                 join_or(group)),
                test, place=place, landmarks=tuple(group))


def even_page():
    def test(led, r):
        return [led.page_no(p) % 2 == 0 for p in led.page_of]
    return Clue("even_page", "hunt", "The killer is on an even-numbered page.",
                "Use the page number printed at the foot of each page.", test)


def facing_page(name, others=5):
    """Darcy and the Autumn Killer: the page facing the killer's page in the open book."""
    def test(led, r):
        ps = _pages_with(led, name)
        out = []
        for p in led.page_of:
            odd = led.page_no(p) % 2 == 1
            f = (p - 1 if odd else p + 1) if not r.get("facing_flip") else (p + 1 if odd else p - 1)
            out.append(f in ps)
        return out

    def place(ctx):
        # on both neighbours of the killer's page, so either idea of "facing" keeps the killer
        for p in (ctx.kp - 1, ctx.kp + 1):
            ctx.put(name, p)
        far = [p for p in range(ctx.n_pages) if abs(p - ctx.kp) > 1]
        for p in ctx.rng.sample(far, others):
            ctx.put(name, p)
    return Clue("facing", "hunt", "The page facing the killer's page contains %s %s." % (article(name), name),
                "In the open book an even page sits on the left and the odd page after it on the right; those two "
                "face each other. The first page of a list faces nothing.", test, place=place, landmarks=(name,))


def page_before(group, label):
    """The Guest List: one of a group on the page just before the killer's."""
    def test(led, r):
        ps = set()
        for g in group:
            ps |= _pages_with(led, g)
        d = -1 if r.get("before_after_flip") else 1
        return [(p - d) in ps for p in led.page_of]

    def place(ctx):
        for p in (ctx.kp - 1, ctx.kp + 1):
            ctx.put(ctx.rng.choice(group), p)
        far = [p for p in range(ctx.n_pages) if abs(p - ctx.kp) > 1]
        for p in ctx.rng.sample(far, 6):
            ctx.put(ctx.rng.choice(group), p)
    return Clue("page_before", "hunt", "The page just before the killer's page contains %s." % label,
                "The page before, not the page after. %s means %s." % (label[0].upper() + label[1:],
                                                                      join_or(group)),
                test, place=place, landmarks=tuple(group))


def not_chapter_edge():
    def test(led, r):
        out = []
        for p in led.page_of:
            ch = led.chapter_of_page[p]
            first = led.chapters[ch][1]
            last = (led.chapters[ch + 1][1] if ch + 1 < len(led.chapters) else len(led.pages)) - 1
            out.append(first < p < last)
        return out
    return Clue("chapter_edge", "hunt", "The killer is not on the first or last page of a chapter.",
                "Each chapter here runs four pages. Cross out the first and the last page of every chapter.",
                test)


def first_letter_of_page():
    """Darcy: the killer's name contains the first letter of the first name on its page."""
    def test(led, r):
        keys = [letters(pg[0])[0] for pg in led.pages]
        return [keys[led.page_of[i]] in letters(n) for i, n in enumerate(led.flat)]

    def fix(ctx):
        ctx.set_page_first(lambda e: letters(e)[0] in letters(ctx.killer_name))
    return Clue("first_letter_of_page", "spot", "The killer's name contains the first letter of the first name on "
                "the killer's page.", "The first name printed at the top of a page sets that page's letter. Look "
                "for it anywhere in the killer's name.", test, fix=fix)


def no_letter_with_page_first():
    """The Guest List, turned around: shares no letter with the first name on its page."""
    def test(led, r):
        keys = [set(letters(first_of(pg[0]))) for pg in led.pages]
        return [not (keys[led.page_of[i]] & set(letters(first_of(n)))) for i, n in enumerate(led.flat)]

    def fix(ctx):
        ctx.set_page_first(lambda e: not (set(letters(first_of(e))) & set(letters(first_of(ctx.killer_name)))))
    return Clue("no_letter_page_first", "spot", "The killer's first name shares no letter with the first name at "
                "the top of the killer's page.", "Compare first names only. One shared letter anywhere is enough to "
                "cross a name out.", test, fix=fix)


def flank():
    """The Autumn Killer: the name before comes earlier in the alphabet than the name after."""
    def test(led, r):
        f = led.flat
        return [0 < i < len(f) - 1 and letters(f[i - 1]) < letters(f[i + 1]) for i in range(len(f))]

    def fix(ctx):
        ctx.set_flank()
    return Clue("flank", "spot", "The name just before the killer comes earlier in the alphabet than the name just "
                "after the killer.", "Compare the two neighbours in dictionary order, letter by letter, ignoring "
                "spaces. The count carries on across lines and pages.", test, fix=fix)


def initial_of_page_last():
    def test(led, r):
        keys = [letters(pg[-1])[0] for pg in led.pages]
        return [letters(n)[0] == keys[led.page_of[i]] for i, n in enumerate(led.flat)]

    def fix(ctx):
        ctx.set_page_last(lambda e: letters(e)[0] == letters(ctx.killer_name)[0])
    return Clue("initial_of_page_last", "spot", "The killer's name begins with the same letter as the last name "
                "on the killer's page.", "The last name printed at the bottom of each page sets that page's letter.",
                test, fix=fix)
