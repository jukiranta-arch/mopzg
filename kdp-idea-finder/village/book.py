"""The full book: five linked cases in one small town and a mastermind finale
(spec: briefs/2026-10-01_spec-linked-cases.md; clues: village/clues.py; cases: village/plans.py).

Each case is one shop's list of names, laid out like Who Killed Mr Darcy?: entries separated by dots, famous names
hidden among ordinary people, clues that are facts about the killer, one name left, and a check line after the list
that confirms the answer without giving it away. Each case has its own kinds of clue, and every clue has a title and
a witness line, as in The Killer Was On The Guest List.

The cases are linked: from Case Two on, one clue uses the previous killer's name, and the first letters of the five
killers spell the mastermind's first name, whom the finale finds in the town register.

Every case is solved under READINGS, the plausible misreadings of the rules, and is only accepted when each of
them leaves the same one name.
"""

import random
from dataclasses import dataclass, field

from . import clues as C
from .clues import letters
from .namepool import entry_maker, pools
from .plans import PLANS

READINGS = [
    {},                              # the rules as printed
    {"y_vowel": True},               # treats Y as a vowel
    {"window": 1},                   # "within N names" counted one too generously
    {"window": -1},                  # ...or one too strictly
    {"between_inclusive": True},     # counts the two named pages as "between"
    {"near_page_only": True},        # forgets the page before and after
    {"pair_either": True},           # takes "both an A and a B" as either one
    {"pages": 1},                    # "within N pages" / "more than N pages" one page out
    {"pages": -1},
    {"facing_flip": True},           # takes the wrong page as the facing page
    {"before_after_flip": True},     # looks at the page after instead of the page before
    {"xor_inclusive": True},         # takes "one or the other, but not both" as "either"
    {"at_least": True},              # takes "exactly twice" as "at least twice"
]
PAGES_PER_CASE = 20
MASTERMINDS = ["Edith", "Mabel", "Clara", "Hazel", "Agnes", "Ralph", "Grace", "Cyril", "Basil", "Ethel"]


def signature(name):
    """What the check line prints: number of letters, and their sum with A = 1 ... Z = 26."""
    l = letters(name)
    return len(l), sum(ord(c) - 64 for c in l)


@dataclass
class Ledger:
    pages: list
    chapters: list
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

    def at(self, i):
        p = self.page_of[i]
        return p, i - sum(len(x) for x in self.pages[:p])


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
    return {bool(clue.word(name, r)) for r in READINGS}


class GenerationError(ValueError):
    pass


# ---------------------------------------------------------------- a case

@dataclass
class Case:
    plan: object
    ledger: Ledger
    clues: list
    killer: int
    check: tuple
    stats: dict


class Ctx:
    """What the clue factories see while a case is being built."""

    def __init__(self, rng, pages, chapters_per, kp, entry, page_from, scattered=70):
        self.rng, self.pages, self.kp, self.entry = rng, pages, kp, entry
        self.n_pages = len(pages)
        self.n_ch = self.n_pages // chapters_per
        self.ch_of = [p // chapters_per for p in range(self.n_pages)]
        self.taken = [set() for _ in pages]
        self.page_from = page_from
        self.scattered = scattered
        self.kpos = None
        self.killer_name = None

    def put(self, name, page, near=None, window=10, at=None):
        names = self.pages[page]
        if at is not None:
            k = 0 if at == 0 else len(names) - 1
            if k in self.taken[page]:
                raise GenerationError("spot taken")
        else:
            free = [k for k in range(1, len(names) - 1) if not ({k - 1, k, k + 1} & self.taken[page])]
            if near is not None:
                free = [k for k in free if 0 < abs(k - near) <= window - 2]
            if not free:
                raise GenerationError("no room on page %d" % page)
            k = self.rng.choice(free)
        names[k] = name
        self.taken[page].add(k)
        return k

    def _filler(self, pred):
        for _ in range(3000):
            e = self.entry()
            if pred(e):
                return e
        raise GenerationError("no filler fits")

    def set_page_first(self, pred):
        if 0 in self.taken[self.kp]:
            raise GenerationError("page top taken")
        self.pages[self.kp][0] = self._filler(pred)
        self.taken[self.kp].add(0)

    def set_page_last(self, pred):
        k = len(self.pages[self.kp]) - 1
        if k in self.taken[self.kp]:
            raise GenerationError("page bottom taken")
        self.pages[self.kp][k] = self._filler(pred)
        self.taken[self.kp].add(k)

    def set_flank(self):
        a, b = self._filler(lambda e: True), self._filler(lambda e: True)
        while letters(a) == letters(b):
            b = self._filler(lambda e: True)
        lo, hi = sorted((a, b), key=letters)
        self.pages[self.kp][self.kpos - 1] = lo
        self.pages[self.kp][self.kpos + 1] = hi
        self.taken[self.kp] |= {self.kpos - 1, self.kpos + 1}


def plan_clues(plan, chain=None):
    out = [c for c, _, _ in plan.clues]
    for c, title, story in plan.clues:
        c.title, c.story = title, story
    if chain is not None:
        out.append(chain)
    return out


def landmark_risks(plan, chain=None):
    """Clued famous names that pass every word clue of the plan under some reading: they can survive."""
    clues = plan_clues(plan, chain)
    word = [c for c in clues if c.word]
    names = {n for c in clues for n in c.landmarks} | set(plan.eggs)
    return sorted(n for n in names if not any(verdicts(w, n) == {False} for w in word))


def generate_case(plan, rng, initial, page_from, prev=None, n_pages=PAGES_PER_CASE, per_page=None,
                  chapter_pages=4, heading_cost=30):
    """One case whose killer's first name begins with `initial`; `prev` is (previous plan, previous answer)."""
    chain = None
    if plan.chain and prev:
        factory, title, story = plan.chain
        chain = factory(prev[0].label, prev[1])
        chain.title, chain.story = title, story
    clues = plan_clues(plan, chain)
    landmarks = {n for c in clues for n in c.landmarks} | set(plan.eggs)
    firsts, lasts = pools({w for n in landmarks for w in n.split()})
    entry = entry_maker(rng, firsts, lasts, plan.full_share)

    if per_page is None:   # full names take more room on a row
        per_page = (141, 148) if plan.full_share > 0.9 else (190, 197)
        heading_cost = 22 if plan.full_share > 0.9 else 30
    keys = {c.key for c in clues}
    chapters = [(plan.chapters[k], k * chapter_pages) for k in range(n_pages // chapter_pages)]
    pages = [[entry() for _ in range(rng.randint(*per_page) - (heading_cost if p % chapter_pages == 0 else 0))]
             for p in range(n_pages)]

    # The killer's page: away from the ends, and wherever the plan's clues allow.
    choices = [p for p in range(3, n_pages - 3)
               if ("chapter_edge" not in keys or p % chapter_pages in (1, 2))
               and ("even_page" not in keys or (page_from + p) % 2 == 0)]
    ctx = Ctx(rng, pages, chapter_pages, rng.choice(choices), entry, page_from)
    for c in clues:
        if c.place:
            c.place(ctx)
    word = [c for c in clues if c.word]
    for egg in plan.eggs:   # only the extras that a word clue rules out, so none can be left standing
        if any(verdicts(w, egg) == {False} for w in word):
            ctx.put(egg, rng.randrange(n_pages))

    # The killer: a full name with the right initial that every word clue keeps under every reading.
    word = [c for c in clues if c.word]
    for _ in range(4000):
        name = rng.choice([f for f in firsts if f[0] == initial]) + " " + rng.choice(lasts)
        if all(verdicts(c, name) == {True} for c in word):
            break
    else:
        raise GenerationError("no killer name fits (%s, %s)" % (plan.key, initial))
    row = pages[ctx.kp]
    spots = [k for k in range(2, len(row) - 2) if not ({k - 2, k - 1, k, k + 1, k + 2} & ctx.taken[ctx.kp])]
    ctx.kpos = rng.choice(spots)
    row[ctx.kpos] = name
    ctx.taken[ctx.kp].add(ctx.kpos)
    ctx.killer_name = name
    for c in clues:
        if c.fix:
            c.fix(ctx)

    led = Ledger(pages, chapters, page_from).index()
    killer = sum(len(x) for x in pages[:ctx.kp]) + ctx.kpos
    protected = {sum(len(x) for x in pages[:p]) + k for p in range(n_pages) for k in ctx.taken[p]}
    sig = signature(name)

    # Repair: everyone else still standing gets a name that a word clue rules out under every reading;
    # nobody who survives all the clues but one may match the check line.
    failing = sorted({e for e in {entry() for _ in range(3000)} if any(verdicts(c, e) == {False} for c in word)})
    for _ in range(25):
        bad = survivors_all_readings(led, clues) - {killer}
        for c in clues:
            bad |= {i for i in survivors_all_readings(led, clues, skip=c.key)
                    if i != killer and signature(led.flat[i]) == sig}
        if not bad:
            break
        for i in bad:
            if i in protected:
                raise GenerationError("a protected name survives (%s: %s)" % (plan.key, led.flat[i]))
            p, at = led.at(i)
            pages[p][at] = rng.choice([n for n in failing if signature(n) != sig])
        led.index()
    else:
        raise GenerationError("repair did not settle (%s)" % plan.key)
    case = Case(plan, led, clues, killer, sig, {})
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
    hunt = [c for c in clues if c.kind in ("hunt", "spot")]
    return dict(total=total, pages=len(led.pages), killer_name=led.flat[case.killer],
                alone={c.key: round(sum(c.test(led, {})) / total, 2) for c in clues},
                after_each=after, after_hunt=len(solve(led, hunt)),
                finals={k: solve(led, clues, r) for k, r in enumerate(READINGS)})


def validate(case):
    """The spec's rules for a case; returns a list of problems (empty when fine)."""
    led, s, problems, key = case.ledger, case.stats, [], case.plan.key if case.plan else "finale"
    for r, alive in s["finals"].items():
        if alive != [case.killer]:
            problems.append("%s: reading %d leaves %d names" % (key, r, len(alive)))
    for c in case.clues:
        if c.kind == "hunt" and not 0.2 <= s["alone"][c.key] <= 0.8:
            problems.append("%s: clue %s alone keeps %.0f%%" % (key, c.key, 100 * s["alone"][c.key]))
        near = survivors_all_readings(led, case.clues, skip=c.key) - {case.killer}
        if any(signature(led.flat[i]) == case.check for i in near):
            problems.append("%s: check line fits a near-survivor (skipping %s)" % (key, c.key))
    if not 20 <= s["after_hunt"] <= 400:
        problems.append("%s: %d names left for the letter clues" % (key, s["after_hunt"]))
    return problems


# ---------------------------------------------------------------- the finale

FINALE_CHAPTERS = ["Main Street", "Maple Avenue", "Church Lane", "River Road"]


def finale_clues(mastermind):
    def name_is(led, reading):
        return [len(n.split()) == 2 and n.split()[0] == mastermind for n in led.flat]

    def not_on_page(name):
        def test(led, r):
            ps = {led.page_of[i] for i, n in enumerate(led.flat) if n == name}
            return [p not in ps for p in led.page_of]
        return C.Clue("not_on_page", "hunt", "The mastermind is not on a page with %s %s." % (C.article(name), name),
                      "Cross out every page where %s appears." % name, test)

    name = C.Clue("mastermind_name", "word", "The mastermind's first name is spelled by the first letters of the "
                  "five killers, in case order.", "Write down the first letter of each killer's name, from Case One "
                  "to Case Five. They spell a first name. Only full names with exactly that first name qualify.",
                  name_is)
    near1 = C.near_page("Tom Sawyer")
    near1.rule = near1.rule.replace("The killer", "The mastermind")
    betw = C.between("Benjamin Franklin", "Mark Twain")
    betw.rule = betw.rule.replace("The killer", "The mastermind")
    near4 = C.near_page("Cupid")
    near4.rule = near4.rule.replace("The killer", "The mastermind")
    out = [name, near1, not_on_page("Simple Simon"), betw, near4]
    for c, (title, story) in zip(out, [
        ("Five Initials", "Lay your five answers side by side. The mastermind chose the killers for their first "
         "letters, and those letters spell the mastermind's own first name."),
        ("The Boy in the Straw Hat", "The Tom Sawyer boys came to the meeting too, still in their straw hats. The "
         "mastermind sat within one page of one of them in the register."),
        ("The Pieman's Friend", "Simple Simon came straight from choir practice. The mastermind made sure not to "
         "sign the same page as him."),
        ("Two Old Gentlemen", "Benjamin Franklin and Mark Twain signed at opposite ends of the hall. The mastermind "
         "signed somewhere between them."),
        ("Love at First Sight", "Cupid was handing out paper hearts at the door. The mastermind signed within one "
         "page of one of Cupid's signatures."),
    ]):
        c.title, c.story = title, story
    return out


def generate_finale(rng, mastermind, page_from, n_pages=8, per_page=(185, 195), chapter_pages=2, heading_cost=30):
    """The town register: ten people share the mastermind's first name; the callback clues leave one.

    Layout (page indices, mirrored at random): Benjamin Franklin on 0 and Mark Twain on 7, so "between" is 1-6;
    Tom Sawyer and Cupid on the mastermind's page 3 (Tom also on 7, Cupid also on 6); Simple Simon on 1, 2 and 5.
    The namesakes stand on pages 0, 1, 2 and 5, which every reading rules out.
    """
    bad = {"Tom", "Sawyer", "Simple", "Simon", "Benjamin", "Franklin", "Mark", "Twain", "Cupid", mastermind}
    firsts, lasts = pools(bad)
    entry = entry_maker(rng, firsts, lasts, 0.45)

    P = (lambda p: n_pages - 1 - p) if rng.random() < 0.5 else (lambda p: p)
    chapters = [(FINALE_CHAPTERS[k], k * chapter_pages) for k in range(n_pages // chapter_pages)]
    clues = finale_clues(mastermind)
    for _ in range(50):
        pages = [[entry() for _ in range(rng.randint(*per_page) - (heading_cost if p % chapter_pages == 0 else 0))]
                 for p in range(n_pages)]
        ctx = Ctx(rng, pages, chapter_pages, P(3), entry, page_from)
        ctx.put("Benjamin Franklin", P(0))
        ctx.put("Mark Twain", P(7))
        for p in (3, 7):
            ctx.put("Tom Sawyer", P(p))
        for p in (3, 6):
            ctx.put("Cupid", P(p))
        for p in (1, 2, 5):
            ctx.put("Simple Simon", P(p))
        surnames = rng.sample(lasts, 10)
        k = ctx.put(mastermind + " " + surnames[0], P(3))
        for s_name, p in zip(surnames[1:], [0, 1, 2, 5] + [rng.choice([0, 1, 2, 5]) for _ in range(5)]):
            ctx.put(mastermind + " " + s_name, P(p))
        led = Ledger(pages, chapters, page_from).index()
        who = sum(len(x) for x in pages[:P(3)]) + k
        sig = signature(led.flat[who])
        # nobody who survives all the clues but one may match the check line
        for c in clues:
            for i in survivors_all_readings(led, clues, skip=c.key) - {who}:
                if signature(led.flat[i]) == sig and led.flat[i].split()[0] != mastermind:
                    p, at = led.at(i)
                    pages[p][at] = next(e for e in iter(entry, None) if signature(e) != sig)
        led.index()
        finals = [solve(led, clues, r) for r in READINGS]
        namesakes = solve(led, clues[:1])
        each = all(set(namesakes) - set(solve(led, [clues[0], c])) for c in clues[1:])
        clash = any(signature(led.flat[i]) == sig for c in clues
                    for i in survivors_all_readings(led, clues, skip=c.key) - {who})
        if all(v == [who] for v in finals) and len(namesakes) == 10 and each and not clash:
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
            cases, prev = [], None
            for k, (plan, initial) in enumerate(zip(PLANS, mastermind.upper())):
                for _ in range(8):
                    try:
                        case = generate_case(plan, rng, initial, 1 + k * PAGES_PER_CASE, prev)
                    except GenerationError:
                        continue
                    if not validate(case):
                        break
                else:
                    raise GenerationError("no valid %s case for %s" % (plan.key, initial))
                cases.append(case)
                prev = (plan, case.ledger.flat[case.killer])
            finale = generate_finale(rng, mastermind, 1 + len(PLANS) * PAGES_PER_CASE)
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
