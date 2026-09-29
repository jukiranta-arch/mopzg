"""Render a generated puzzle as a print-ready 6 x 9 inch PDF (needs reportlab).

Layout: front matter padded to an even page count, so register page 1 lands
on a right-hand page and printed page numbers match the facing-page rules.
"""

import random

import os

from reportlab.lib.pagesizes import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .model import PERSON_TITLES, READINGS, Register, letters, words

W, H = 6 * inch, 9 * inch
INNER, OUTER, TOP, BOTTOM = 0.70 * inch, 0.50 * inch, 0.60 * inch, 0.65 * inch
# KDP needs every font embedded. Liberation Serif (SIL Open Font License, Times metrics)
# ships in fonts/ and is embedded in the PDF; the built-in Times fonts are not.
_FONTS = os.path.join(os.path.dirname(__file__), "fonts")
for _name, _file in (("BookSerif", "LiberationSerif-Regular.ttf"), ("BookSerif-Bold", "LiberationSerif-Bold.ttf"),
                     ("BookSerif-Italic", "LiberationSerif-Italic.ttf")):
    pdfmetrics.registerFont(TTFont(_name, os.path.join(_FONTS, _file)))
SERIF, SERIF_B, SERIF_I = "BookSerif", "BookSerif-Bold", "BookSerif-Italic"
SEP = "  ·  "
REG_SIZE, REG_LEADING = 10, 13       # register type: big enough for older eyes


class LayoutError(RuntimeError):
    pass


class Book:
    def __init__(self, path, title, subtitle):
        self.c = canvas.Canvas(path, pagesize=(W, H), initialFontName=SERIF, initialFontSize=10)
        self.c.setTitle(title)
        self.c.setSubject(subtitle)
        self.pdf_page = 1

    def margins(self):
        right_hand = self.pdf_page % 2 == 1
        left = INNER if right_hand else OUTER
        return left, W - (OUTER if right_hand else INNER)

    def next(self):
        self.c.showPage()
        self.pdf_page += 1

    def text_block(self, x0, x1, y, text, font=SERIF, size=10.5, leading=14, align="left"):
        """Word-wrapped paragraph; returns the y below it."""
        c = self.c
        c.setFont(font, size)
        line = ""
        lines = []
        for word in text.split(" "):
            trial = (line + " " + word).strip()
            if stringWidth(trial, font, size) <= x1 - x0:
                line = trial
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        for ln in lines:
            if align == "center":
                c.drawCentredString((x0 + x1) / 2, y, ln)
            else:
                c.drawString(x0, y, ln)
            y -= leading
        return y

    def footer(self, number):
        self.c.setFont(SERIF, 9)
        self.c.drawCentredString(W / 2, BOTTOM / 2, str(number))


def _verdicts(clue, name):
    one = Register([[name]], [("", 0)]).index()
    out = set()
    for r in READINGS:
        one.set_reading(r)
        out.add(bool(clue.test(one, 0)))
    return out


def _example_pair(reg, clue, rng):
    """One name that passes and one that fails, both plain (no title) and unambiguous under every reading."""
    plain = sorted({n for n in reg.flat if len(n) < 22 and words(n)[0] not in PERSON_TITLES})
    yes = [n for n in plain if _verdicts(clue, n) == {True}]
    no = [n for n in plain if _verdicts(clue, n) == {False}]
    return rng.choice(yes), rng.choice(no)


def render(reg, clues, solution, path, title="Who Killed Prince Charming?",
           subtitle="A Fairy-Tale Murder Mystery Puzzle", edition_note="SAMPLE CASE"):
    rng = random.Random(solution["seed"])
    b = Book(path, title, subtitle)
    c = b.c
    n_names = solution["total_names"]

    # --- Title page
    c.setFont(SERIF_B, 30)
    c.drawCentredString(W / 2, H - 2.4 * inch, "WHO KILLED")
    c.drawCentredString(W / 2, H - 2.9 * inch, "PRINCE CHARMING?")
    c.setFont(SERIF_I, 13)
    c.drawCentredString(W / 2, H - 3.4 * inch, subtitle)
    c.setFont(SERIF, 11)
    c.drawCentredString(W / 2, H - 3.9 * inch,
                        "%s names · %d clues · 1 killer" % (format(n_names, ","), len(clues)))
    if edition_note:
        c.setFont(SERIF_B, 10)
        c.drawCentredString(W / 2, 1.2 * inch, edition_note)
    b.next()

    # --- The case
    x0, x1 = b.margins()
    c.setFont(SERIF_B, 16)
    c.drawCentredString(W / 2, H - TOP - 20, "The Case")
    story = [
        "The Happily Ever After Ball was the event of the year. Every character from every tale had come: "
        "princesses and paupers, giants and goose girls, and rather more wolves than anyone had invited.",
        "At the first stroke of midnight, Prince Charming fell face-first into the wedding cake. "
        "By the twelfth stroke he was dead.",
        "The palace guards barred the doors and wrote down the name of every guest: %s names in all. "
        "Witnesses agree that two guests slipped away from the dance floor just before midnight. "
        "One of them is the killer." % format(n_names, ","),
        "The guards have gathered %d clues. Every clue is true of both suspects. Work through the guest "
        "register, strike out every name a clue rules out, and you will be left with two. The Final "
        "Deduction at the back of the book tells you which of them did it." % len(clues),
        "All you need is a pencil, patience, and a sharp eye.",
    ]
    y = H - TOP - 55
    for para in story:
        y = b.text_block(x0, x1, y, para) - 8
    b.next()

    # --- Rules
    x0, x1 = b.margins()
    c.setFont(SERIF_B, 16)
    c.drawCentredString(W / 2, H - TOP - 20, "Before You Begin")
    rules = [
        ("What is a name?", "Everything between two dots in the register is one name: a single name "
         "(Cinderella), a full name (Ada Finch) or a name with a title (Queen Mabel, Mrs Lark)."),
        ("Titles don’t count.", "A title at the start of a name (Mr, Mrs, Miss, Dr, Sir, Lady, Dame, Lord, "
         "Captain, King or Queen) is left out when a clue checks letters: Queen Mabel is checked as Mabel."),
        ("Letters only.", "Only the letters A to Z count. Spaces, hyphens and apostrophes do not."),
        ("Vowels and consonants.", "The vowels are A, E, I, O and U. Every other letter is a consonant, "
         "and that includes Y."),
        ("Reading order.", "Names run left to right, line by line, page by page. A name never "
         "breaks across two lines."),
        ("Pages.", "Page numbers are printed at the foot of each register page. Facing pages are the two "
         "you see side by side when the book lies open: an even page on the left, the next odd page on the right."),
        ("Same name, different guest.", "Some names appear more than once. Each one is a different guest: "
         "check each on its own."),
        ("Any order.", "The clues can be used in any order and you will reach the same two names."),
        ("Exact spelling.", "When a clue names a character, only that exact spelling counts."),
    ]
    y = H - TOP - 50
    for head, body in rules:
        c.setFont(SERIF_B, 10.5)
        c.drawString(x0, y, head)
        y = b.text_block(x0, x1, y - 13, body, size=10, leading=13) - 6
    b.next()

    # --- Clues
    def clue_page_start():
        x0, x1 = b.margins()
        c.setFont(SERIF_B, 16)
        c.drawCentredString(W / 2, H - TOP - 20, "The Clues")
        return x0, x1, H - TOP - 50

    x0, x1, y = clue_page_start()
    for n, cl in enumerate(clues, 1):
        need = 110
        if y - need < BOTTOM:
            b.next()
            x0, x1, y = clue_page_start()
        box_h = 38
        c.setFillGray(0.9)
        c.rect(x0, y - box_h + 12, x1 - x0, box_h, stroke=0, fill=1)
        c.setFillGray(0)
        c.setFont(SERIF_B, 9.5)
        c.drawCentredString((x0 + x1) / 2, y, "CLUE %d" % n)
        b.text_block(x0 + 8, x1 - 8, y - 14, cl.text, size=10.5, leading=13, align="center")
        y -= box_h + 6
        y = b.text_block(x0, x1, y, cl.explain, font=SERIF_I, size=9.5, leading=12)
        if cl.kind == "word":
            yes, no = _example_pair(reg, cl, rng)
            y = b.text_block(x0, x1, y - 2, "Example: %s qualifies. %s does not." % (yes, no), size=9.5, leading=12)
        y -= 14
    b.next()
    if b.pdf_page % 2 == 0:          # register page 1 must be a right-hand page
        b.next()

    # --- Register
    size, leading = REG_SIZE, REG_LEADING
    for p, names in enumerate(reg.pages):
        x0, x1 = b.margins()
        y = H - TOP
        chapter_starts = {start: (i, q) for i, (q, start) in enumerate(reg.chapters)}
        if p in chapter_starts:
            i, quote = chapter_starts[p]
            c.setFont(SERIF, 9)
            c.drawCentredString(W / 2, y - 6, "CHAPTER %d" % (i + 1))
            c.setFont(SERIF_I, 15)
            c.drawCentredString(W / 2, y - 28, "“%s”" % quote)
            y -= 52
        c.setFont(SERIF, size)
        line = []
        for name in names:
            trial = SEP.join(line + [name])
            if stringWidth(trial, SERIF, size) <= x1 - x0:
                line.append(name)
            else:
                c.drawString(x0, y, SEP.join(line) + SEP.rstrip())
                y -= leading
                line = [name]
        if line:
            c.drawString(x0, y, SEP.join(line) + SEP.rstrip())
            y -= leading
        if y < BOTTOM:
            raise LayoutError("register page %d overflows; use fewer names per page" % reg.page_no(p))
        b.footer(reg.page_no(p))
        b.next()

    # --- Final deduction
    x0, x1 = b.margins()
    c.setFont(SERIF_B, 16)
    c.drawCentredString(W / 2, H - TOP - 20, "The Final Deduction")
    y = H - TOP - 60
    for para in [
        "You should now have two names left. Only one of them is the killer.",
        "As the clock struck twelve, the Fairy Godmother saw a guest run down the palace stairs and "
        "lose a shoe on the last step. “The one I saw,” she tells the guards, “has the "
        "longer name of the two.”",
        "Count the letters A to Z in each name. The longer name is your killer.",
        "The killer is: ______________________________",
    ]:
        y = b.text_block(x0, x1, y, para) - 10
    b.next()

    # --- Notes: a buffer page so turning from the deduction doesn't reveal the answer
    x0, x1 = b.margins()
    c.setFont(SERIF_B, 16)
    c.drawCentredString(W / 2, H - TOP - 20, "Notes")
    c.setLineWidth(0.4)
    c.setStrokeGray(0.6)
    y = H - TOP - 60
    while y > BOTTOM + 20:
        c.line(x0, y, x1, y)
        y -= 24
    c.setStrokeGray(0)
    b.next()

    # --- Solution
    x0, x1 = b.margins()
    c.setFont(SERIF_B, 16)
    c.drawCentredString(W / 2, H - TOP - 20, "Solution")
    y = H - TOP - 55
    s1, s2 = solution["suspects"]
    for s in (s1, s2):
        y = b.text_block(x0, x1, y, "%s, page %d, chapter %d (%d letters)" % (
            s["name"], s["page"], s["chapter"], len(letters(s["name"])))) - 4
    y = b.text_block(x0, x1, y - 6, "The killer is %s." % solution["killer"], font=SERIF_B) - 10
    y = b.text_block(x0, x1, y, "Names left after each clue:", font=SERIF_I, size=10) - 2
    left = n_names
    for n, (cl, cnt) in enumerate(zip(clues, solution["counts"]), 1):
        y = b.text_block(x0, x1, y, "Clue %d: %s → %s" % (n, format(left, ","), format(cnt, ",")), size=10, leading=13)
        left = cnt
    c.save()
    return b.pdf_page
