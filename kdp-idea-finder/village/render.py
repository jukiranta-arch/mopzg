"""Render one case as a 6 x 9 inch test PDF (needs reportlab), in the order
Who Killed Mr Darcy? uses: the story, the case, the clues, Before You Start,
then the ledger (pages numbered from 1), and at the back the final deduction,
a Stop page, and the solution upside down on its back.
"""

import random

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from whodunit.render import BOTTOM, INNER, OUTER, SERIF, SERIF_B, SERIF_I, TOP, H, W, LayoutError

from .case import CLUES, FINAL, LANDMARKS, MUSKETEERS, READINGS, ROBIN, WINDOW, Ledger, letters

REG_SIZE, REG_LEADING = 10.5, 14.5
DOT = "·"
TITLE = "The Ashcombe Raffle"
CASE = "Case One: The Summer Fête"
NUMBERS = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve"]

STORY = [
    "Every July, Ashcombe St Mary holds its Summer Fête on the green behind the church, and every July the "
    "same people win the same prizes. This year was different.",
    "At ten past four, when the brass band stopped for tea, Mrs Hester Greaves, chair of the fête committee "
    "for twenty-two years, was found in a deckchair behind the cake stall. Dr Moffat said it was her heart, "
    "until he noticed the smell of bitter almonds in her teacup.",
    "In her gloved hand was a raffle ticket: pink, number 1. The raffle tickets that year were blue.",
    "Two visitors were seen slipping out from behind the cake stall just before four. Nobody saw their faces.",
    "Detective Sergeant Ruth Ambrose closed the gate at half past four. Nobody had left. Every visitor had "
    "signed the gate ledger on the way in, and every one of them was still on the green.",
    "She turned the pink ticket over. On the back, in neat capitals, someone had written: ONE OF FIVE.",
]

CASE_PAGE = [
    "Your case file is the gate ledger.",
    "{clues} clues.",
    "{total} names.",
    "Somewhere inside are the two visitors seen behind the cake stall.",
    "Every clue lets you strike names from the ledger: thousands become hundreds, hundreds become dozens, until "
    "only two remain.",
    "But which one poisoned Hester Greaves?",
    "The answer is waiting at the back of the book, in one final deduction, but only once you have found the "
    "two suspects.",
    "All you need is a pencil and some patience.",
]

BEFORE = [
    ("What is a name.", "A name is everything between two dots in the ledger: a single name (Rosa), a full name "
     "(Ada Finch), or a famous name (Charles Dickens). Each name is one visitor. Names repeat; each Rosa is a "
     "different Rosa."),
    ("Exact spelling only.", "When a clue names someone, only that exact name qualifies, on its own. Robin Hood "
     "is Robin Hood, not Robin Finch; John is John, not John Baker; Juliet is Juliet, not Julie."),
    ("Letters in a name.", "When a clue looks at the letters in a name, count every letter of the whole name, "
     "A to Z. Spaces don't count: Ada Finch has eight letters."),
    ("Vowels and consonants.", "The vowels are A, E, I, O and U. Every other letter is a consonant, and Y is "
     "always a consonant."),
    ("Names don't break across rows.", "Every name sits whole on a row, as the dot at the end of each row shows."),
    ("A few tips.", "The clues don't need to be tackled in the order they're given; read them all first and start "
     "with the ones that give you the biggest head start. Work in pencil, in case you change your mind."),
]

ENDING = [
    "The killer is {killer}.",
    "When Ruth Ambrose read the name aloud in the tea tent, {killer} put down a cup of tea and said nothing at "
    "all. In {killer}'s coat pocket was a book of pink raffle tickets. Ticket 1 had been torn out. So had "
    "tickets 2, 3, 4 and 5.",
    "“I never had the others,” {killer} said at last. “The book came in the post, with ticket 1 "
    "already gone and a letter telling me what to do with it. I burned the letter. I was told to.”",
    "{innocent} had only gone behind the cake stall for a cigarette, and saw nothing.",
    "Somewhere in Ashcombe St Mary, four more people had received a pink ticket. The fête was only the "
    "first.",
]


class Book:
    def __init__(self, path):
        self.c = canvas.Canvas(path, pagesize=(W, H), initialFontName=SERIF, initialFontSize=10)
        self.c.setTitle(TITLE)
        self.c.setSubject(CASE)
        self.pdf_page = 1

    def margins(self):
        return (INNER, W - OUTER) if self.pdf_page % 2 == 1 else (OUTER, W - INNER)

    def next(self):
        self.c.showPage()
        self.pdf_page += 1

    def to_right_hand(self):
        if self.pdf_page % 2 == 0:
            self.next()

    @staticmethod
    def wrap(text, width, font, size):
        lines, line = [], ""
        for word in text.split(" "):
            trial = (line + " " + word).strip()
            if stringWidth(trial, font, size) <= width:
                line = trial
            else:
                lines.append(line)
                line = word
        return lines + ([line] if line else [])

    def para(self, x0, x1, y, text, font=SERIF, size=10.5, leading=14.5, align="left"):
        self.c.setFont(font, size)
        for ln in self.wrap(text, x1 - x0, font, size):
            if align == "center":
                self.c.drawCentredString((x0 + x1) / 2, y, ln)
            else:
                self.c.drawString(x0, y, ln)
            y -= leading
        return y

    def heading(self, text, size=16):
        self.c.setFont(SERIF_B, size)
        self.c.drawCentredString(W / 2, H - TOP - 18, text)
        return H - TOP - 52

    def footer(self, n):
        self.c.setFont(SERIF, 9)
        self.c.drawCentredString(W / 2, BOTTOM / 2, str(n))


# ---------------------------------------------------------------- examples

def _plain(led, avoid):
    return sorted({n for n in led.flat if n not in LANDMARKS and n not in avoid})


def _always(clue, name):
    one = Ledger([[name]], [("", 0)]).index()
    return {clue.test(one, r)[0] for r in READINGS}


def examples(led, avoid, rng):
    """Example lines for each clue, built from ledger names that are never the suspects."""
    names = _plain(led, avoid)
    by_key = {c.key: c for c in CLUES}

    def pick(key, verdict, cond=lambda n: True):
        return rng.choice([n for n in names if _always(by_key[key], n) == {verdict} and cond(n)])

    out = {}
    n = pick("odd_consonants", True, lambda n: " " in n)
    cons = [c for c in letters(n) if c not in "AEIOU"]
    out["odd_consonants"] = "%s has %s consonants: %s. That's an odd number." % (
        n, NUMBERS[len(cons) - 1].lower() if len(cons) <= 8 else len(cons), ", ".join(cons))
    yes, no = pick("ends_consonant", True), pick("ends_consonant", False)
    out["ends_consonant"] = "%s ends in “%s”, so it qualifies. %s ends in “%s”, so it doesn't." % (
        yes, yes[-1], no, no[-1])
    yes = pick("double_letter", True)
    pair = next(m.group(0) for w in yes.split() for m in [__import__("re").search(r"([a-z])\1", w.lower())] if m)
    out["double_letter"] = "%s has a double letter: the “%s”." % (yes, pair)
    yes = pick("a_to_m", True)
    out["a_to_m"] = "%s begins with %s, so it qualifies." % (yes, yes[0])
    out["robin"] = ("If Robin Hood appears on page 10, a suspect could be on page 9, 10 or 11.")
    out["musketeers"] = ("If Aramis is the 30th name on a page, the 20th to 40th names on that page qualify, "
                         "apart from Aramis himself.")
    return out


# ---------------------------------------------------------------- ledger rows

def layout_rows(names, width, size):
    """Split a page's names into rows; every row ends with a dot."""
    dot_w = stringWidth(" " + DOT + " ", SERIF, size)
    rows, row, used = [], [], 0.0
    for n in names:
        w = stringWidth(n, SERIF, size) + dot_w
        if row and used + w > width:
            rows.append(row)
            row, used = [], 0.0
        row.append(n)
        used += w
    return rows + ([row] if row else [])


def draw_row(c, x0, x1, y, row, size, justify):
    widths = [stringWidth(n, SERIF, size) for n in row]
    dot = stringWidth(DOT, SERIF, size)
    gap = stringWidth(" ", SERIF, size)
    spare = (x1 - x0) - sum(widths) - len(row) * (dot + 2 * gap)
    extra = spare / len(row) if justify else 0
    x = x0
    c.setFont(SERIF, size)
    for n, w in zip(row, widths):
        c.drawString(x, y, n)
        x += w + gap + extra / 2
        c.drawString(x, y, DOT)
        x += dot + gap + extra / 2


# ---------------------------------------------------------------- the book

def notes(b):
    x0, x1 = b.margins()
    y = b.heading("Notes") - 10
    b.c.setLineWidth(0.4)
    b.c.setStrokeGray(0.6)
    while y > BOTTOM + 20:
        b.c.line(x0, y, x1, y)
        y -= 24
    b.c.setStrokeGray(0)
    b.next()


def render(case, path, seed=1):
    led, killer, innocent = case.ledger, case.killer, case.innocent
    led.first_page_no = 1
    rng = random.Random(seed)
    b = Book(path)
    c = b.c
    total = format(len(led.flat), ",")

    # Title
    c.setFont(SERIF, 10)
    c.drawCentredString(W / 2, H - 1.6 * 72, "TEST COPY · ONE CASE OF FIVE")
    c.setFont(SERIF_B, 26)
    c.drawCentredString(W / 2, H / 2 + 40, TITLE)
    c.setFont(SERIF, 15)
    c.drawCentredString(W / 2, H / 2, CASE)
    b.next()
    b.next()

    # The story
    x0, x1 = b.margins()
    y = b.heading("Ashcombe St Mary")
    for p in STORY:
        y = b.para(x0, x1, y, p) - 9
    b.next()

    # The case
    x0, x1 = b.margins()
    y = b.heading("The Case")
    for p in CASE_PAGE:
        y = b.para(x0, x1, y, p.format(clues=NUMBERS[len(CLUES) - 1], total=total), size=11, leading=15) - 9
    b.next()

    # The clues
    ex = examples(led, {led.flat[killer], led.flat[innocent]}, rng)
    x0, x1 = b.margins()
    y = b.heading("The Clues")
    y = b.para(x0, x1, y, "Two suspects are hidden in the ledger, on different pages, in different chapters. "
               "Every clue below is true of both.", font=SERIF_I) - 10
    for n, cl in enumerate(CLUES, 1):
        parts = [(cl.text, SERIF_B, 10.5, 14), (cl.explain, SERIF, 10, 13)]
        if cl.key in ex:
            parts.append(("Example: " + ex[cl.key], SERIF_I, 10, 13))
        need = 16 + sum(len(b.wrap(t, x1 - x0, f, s)) * l + 3 for t, f, s, l in parts) + 8
        if y - need < BOTTOM:
            b.next()
            x0, x1 = b.margins()
            y = H - TOP - 20
        c.setFont(SERIF_B, 10)
        c.drawString(x0, y, "CLUE %d" % n)
        y -= 15
        for t, f, s, l in parts:
            y = b.para(x0, x1, y, t, font=f, size=s, leading=l) - 3
        y -= 8
    b.next()

    # Before you start
    x0, x1 = b.margins()
    y = b.heading("Before You Start")
    y = b.para(x0, x1, y, "A few things worth knowing before you begin. Come back to them whenever a clue makes "
               "you pause.", font=SERIF_I) - 10
    for head, text in BEFORE:
        c.setFont(SERIF_B, 10.5)
        c.drawString(x0, y, head)
        y = b.para(x0, x1, y - 14, text, size=10, leading=13.5) - 9
    b.next()

    # The ledger
    b.to_right_hand()
    starts = {s: (k, place) for k, (place, s) in enumerate(led.chapters)}
    position = {}
    i = 0
    for p, names in enumerate(led.pages):
        x0, x1 = b.margins()
        y = H - TOP
        if p in starts:
            k, place = starts[p]
            c.setFont(SERIF, 10)
            c.drawCentredString(W / 2, y - 4, "CHAPTER %s" % NUMBERS[k].upper())
            c.setFont(SERIF_B, 16)
            c.drawCentredString(W / 2, y - 26, place)
            y -= 52
        rows = layout_rows(names, x1 - x0, REG_SIZE)
        for r_no, row in enumerate(rows, 1):
            draw_row(c, x0, x1, y, row, REG_SIZE, justify=r_no < len(rows))
            for at in range(1, len(row) + 1):
                position[i] = (r_no, at)
                i += 1
            y -= REG_LEADING
        if y + REG_LEADING - REG_SIZE < BOTTOM:
            raise LayoutError("ledger page %d overflows" % led.page_no(p))
        b.footer(led.page_no(p))
        b.next()

    # The final deduction, on a left-hand page so the Stop page faces it
    if b.pdf_page % 2 == 1:
        notes(b)
    x0, x1 = b.margins()
    y = b.heading("The Final Deduction")
    for p in ["You should now have two names left: the two visitors seen behind the cake stall. Only one of "
              "them poisoned Hester Greaves.",
              "Dr Moffat found a smudge of icing on the poisoned teacup, and a fingerprint in it. By the size of "
              "the hand, he says, it belonged to someone who signs a long name."]:
        y = b.para(x0, x1, y, p) - 9
    y = b.para(x0, x1, y, FINAL[0], font=SERIF_B) - 2
    y = b.para(x0, x1, y, FINAL[1], size=10, leading=13) - 16
    y = b.para(x0, x1, y, "The killer is:  ______________________________", size=11) - 22
    n_letters, total_sum = case.check
    c.setFont(SERIF_B, 11)
    c.drawString(x0, y, "Check your answer")
    y = b.para(x0, x1, y - 15, "The killer's name has %d letters, and they add up to %d (A = 1, B = 2 and so on "
               "to Z = 26). If yours doesn't, recheck your clues before you turn the page." % (n_letters, total_sum),
               size=10, leading=13.5)
    b.next()

    # Stop, and the solution on its back
    x0, x1 = b.margins()
    c.setFont(SERIF_B, 22)
    c.drawCentredString(W / 2, H / 2 + 30, "Stop!")
    b.para(x0 + 20, x1 - 20, H / 2, "The other side of this page names the killer.", size=11, align="center")
    b.next()
    c.saveState()
    c.translate(W, H)
    c.rotate(180)
    x0, x1 = OUTER, W - OUTER
    c.setFont(SERIF_B, 16)
    c.drawCentredString(W / 2, H - TOP - 18, "The Solution")
    y = H - TOP - 52
    for k, p in enumerate(ENDING):
        y = b.para(x0, x1, y, p.format(killer=led.flat[killer], innocent=led.flat[innocent]),
                   font=SERIF_B if k == 0 else SERIF, size=12.5 if k == 0 else 10.5) - 8
    for idx, label in ((killer, "the killer"), (innocent, "the other suspect")):
        p = led.page_of[idx]
        r, at = position[idx]
        y = b.para(x0, x1, y, "%s (%s): page %d, row %d, name %d on the row; %d letters." % (
            led.flat[idx], label, led.page_no(p), r, at, len(letters(led.flat[idx]))), font=SERIF_I, size=10)
    c.restoreState()
    b.next()
    c.save()
    return dict(position=position, pages=b.pdf_page - 1)
