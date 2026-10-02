"""Render one case as a 6 x 9 inch test PDF (needs reportlab), in the order
Who Killed Mr Darcy? uses: the story, the case, the clues, Before You Start,
then the ledger (pages numbered from 1), and at the back the final deduction,
a Stop page, and the solution upside down on its back.
"""

import random

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from whodunit.render import BOTTOM, INNER, OUTER, SERIF, SERIF_B, SERIF_I, TOP, H, W, LayoutError

from .case import CLUES, LANDMARKS, READINGS, WINDOW, Ledger, letters

REG_SIZE, REG_LEADING = 10.5, 14.5
DOT = "·"
TITLE = "Murder in Juniper Falls"
CASE = "Case One: The Bookstore"
NUMBERS = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve"]

STORY = [
    "Juniper Falls is the kind of town where everybody knows your name, your order at the diner, and which "
    "library books you never returned. For thirty years its heart has been Pell's Books on Main Street.",
    "Every October, Pell's holds its Midnight Sale: hot cider, half-price hardcovers, and a raffle for anyone who "
    "signs the sale sheets. This year the whole town came.",
    "At five past midnight, Harriet Pell, who had owned the store since before most of her customers could read, "
    "was found slumped over the register. Doc Whitaker said it was her heart, until he smelled bitter almonds in "
    "her cup of cider.",
    "Tucked into the book on the counter was a bookmark nobody had seen before, stamped with a single number: 1.",
    "Sheriff Ruth Ambrose locked the front door at a quarter past twelve. Nobody had left. Every customer had "
    "signed a sale sheet in the section they were shopping, and every one of them was still in the store.",
    "She turned the bookmark over. On the back, in neat capitals, someone had written: ONE OF FIVE.",
]

CASE_PAGE = [
    "Your case file is the Midnight Sale ledger: every sale sheet from every section of the store.",
    "{clues} clues.",
    "{total} names.",
    "Somewhere inside is the person who poisoned Harriet Pell.",
    "Every clue lets you strike names from the ledger: thousands become hundreds, hundreds become dozens, until "
    "only one remains.",
    "The answer page is at the back of the book, with a check that tells you whether you are right without "
    "giving the name away.",
    "All you need is a pencil and some patience.",
]

BEFORE = [
    ("What is a name.", "A name is everything between two dots in the ledger: a single name (Rosa), a full name "
     "(Ada Finch), or a famous name (Oliver Twist). Each name is one customer. Names repeat; each Rosa is a "
     "different Rosa."),
    ("Exact spelling only.", "When a clue names someone, only that exact name qualifies, on its own. Tom Sawyer "
     "is Tom Sawyer, not Tom Baker; Beth is Beth, not Beth Lowe; Juliet is Juliet, not Julie."),
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
    "When Sheriff Ambrose read the name aloud, {killer} set down a paper cup of cider and said nothing at all. In "
    "{killer}'s coat pocket was a small paper bag from the stationer's: five blank bookmarks and a rubber stamp. "
    "One bookmark was missing.",
    "\u201cI never wanted the others,\u201d {killer} said at last. \u201cThe package came in the mail with a "
    "letter telling me what to do. I burned the letter. I was told to.\u201d",
    "Somewhere in Juniper Falls, four more people had received a package. The bookstore was only the first.",
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
    """Example lines for each clue, built from ledger names that are never the killer."""
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
    out["tom"] = "If Tom Sawyer appears on page 10, the killer could be on page 9, 10 or 11."
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
    led, killer = case.ledger, case.killer
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
    y = b.heading("Juniper Falls")
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
    ex = examples(led, {led.flat[killer]}, rng)
    x0, x1 = b.margins()
    y = b.heading("The Clues")
    y = b.para(x0, x1, y, "The killer is hidden in the ledger. Every clue below is true of the killer.",
               font=SERIF_I) - 10
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

    # The answer page, on a left-hand page so the Stop page faces it
    if b.pdf_page % 2 == 1:
        notes(b)
    x0, x1 = b.margins()
    y = b.heading("Your Answer")
    y = b.para(x0, x1, y, "When you have used all nine clues, one name is left.") - 18
    y = b.para(x0, x1, y, "The killer is:  ______________________________   page  ______", size=11) - 26
    n_letters, total_sum = case.check
    c.setFont(SERIF_B, 11)
    c.drawString(x0, y, "Check your answer")
    y = b.para(x0, x1, y - 15, "The killer's name has %d letters, and they add up to %d. Give each letter its "
               "place in the alphabet, A = 1, B = 2 and so on to Z = 26, and add them up. For example, ROSA is "
               "18 + 15 + 19 + 1 = 53." % (n_letters, total_sum), size=10, leading=13.5) - 8
    y = b.para(x0, x1, y, "Plenty of names in the ledger add up to %d, so this gives nothing away. If yours "
               "doesn't match, recheck your clues before you turn the page." % total_sum, size=10, leading=13.5)
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
        y = b.para(x0, x1, y, p.format(killer=led.flat[killer]),
                   font=SERIF_B if k == 0 else SERIF, size=12.5 if k == 0 else 10.5) - 8
    p = led.page_of[killer]
    r, at = position[killer]
    b.para(x0, x1, y, "%s is on page %d, row %d, name %d on the row, in the chapter %s." % (
        led.flat[killer], led.page_no(p), r, at, led.chapters[led.chapter_of_page[p]][0]), font=SERIF_I, size=10)
    c.restoreState()
    b.next()
    c.save()
    return dict(position=position, pages=b.pdf_page - 1)
