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
from .names import ENDING, MOTIVES, chapter_scenes

W, H = 6 * inch, 9 * inch
# A generous inner margin: names that "run into the fold" are a complaint in competitors' reviews.
INNER, OUTER, TOP, BOTTOM = 0.85 * inch, 0.50 * inch, 0.60 * inch, 0.65 * inch
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


def _example_pair(reg, clue, rng, avoid=()):
    """One name that passes and one that fails, both plain (no title) and unambiguous under every reading.
    Never a suspect's name: an example must not give the answer away."""
    plain = sorted({n for n in reg.flat if len(n) < 22 and words(n)[0] not in PERSON_TITLES} - set(avoid))
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
        "Deduction at the back of the book tells you which of them did it, and the Verdict pages check "
        "your answer without giving it away." % len(clues),
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
        ("Any order.", "The clues can be used in any order and you will reach the same two names. They are "
         "printed in a good order: the first ones clear whole pages, the letter clues come last."),
        ("Checking your answer.", "The Checkpoints page tells you how many pages should still be in play "
         "after each clue. At the end, the Verdict pages check your answer without spoiling it."),
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
            yes, no = _example_pair(reg, cl, rng, [s_["name"] for s_ in solution["suspects"]])
            y = b.text_block(x0, x1, y - 2, "Example: %s qualifies. %s does not." % (yes, no), size=9.5, leading=12)
        y -= 14
    b.next()

    # --- Checkpoints: how much should still be in play, clue by clue (no spoilers)
    x0, x1 = b.margins()
    c.setFont(SERIF_B, 16)
    c.drawCentredString(W / 2, H - TOP - 20, "Checkpoints")
    y = b.text_block(x0, x1, H - TOP - 50,
                     "Using the clues in the order printed, this is how many register pages should still have at "
                     "least one name you have not crossed out, and roughly how many names. If you are far off, "
                     "read the last clue again before going on.", size=10, leading=13) - 10
    c.setFont(SERIF_B, 10)
    c.drawString(x0, y, "After clue")
    c.drawRightString(x0 + 190, y, "Pages in play")
    c.drawRightString(x1, y, "Names in play")
    y -= 16
    c.setFont(SERIF, 10)
    for cp in solution["checkpoints"]:
        c.drawString(x0 + 20, y, str(cp["clue"]))
        c.drawRightString(x0 + 190, y, str(cp["pages"]))
        c.drawRightString(x1, y, _about(cp["names"]))
        y -= 15
    b.next()

    # --- Clue card to cut out, with a blank back
    x0, x1 = b.margins()
    c.setDash(3, 3)
    c.setLineWidth(0.6)
    c.rect(x0 - 6, BOTTOM - 6, x1 - x0 + 12, H - TOP - BOTTOM + 12)
    c.setDash()
    c.setFont(SERIF_B, 12)
    c.drawCentredString(W / 2, H - TOP - 14, "CLUE CARD")
    c.setFont(SERIF_I, 8.5)
    c.drawCentredString(W / 2, H - TOP - 26, "Cut along the dotted line and keep it beside the register.")
    y = H - TOP - 46
    for n, cl in enumerate(clues, 1):
        y = b.text_block(x0 + 4, x1 - 4, y, "%d.  %s" % (n, cl.text), size=9.5, leading=12) - 5
    b.next()
    c.setFont(SERIF_I, 9)
    c.drawCentredString(W / 2, H / 2, "The other side of this page is your clue card.")
    b.next()
    if b.pdf_page % 2 == 0:          # register page 1 must be a right-hand page
        b.next()

    # --- Register
    size, leading = REG_SIZE, REG_LEADING
    scenes = chapter_scenes(len(reg.chapters))
    position = {}                    # flat index -> (line on its page, place on that line), from 1
    lines_on_page = {}
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
            y = b.text_block(x0 + 12, x1 - 12, y - 50, scenes[i], font=SERIF_I, size=9.5, leading=12.5) - 10
        c.setFont(SERIF, size)
        line, line_no = [], 1
        for k, name in enumerate(names):
            trial = SEP.join(line + [name])
            if line and stringWidth(trial, SERIF, size) > x1 - x0:
                c.drawString(x0, y, SEP.join(line) + SEP.rstrip())
                y -= leading
                line, line_no = [], line_no + 1
            line.append(name)
            position[reg.page_start[p] + k] = (line_no, len(line))
        if line:
            c.drawString(x0, y, SEP.join(line) + SEP.rstrip())
            y -= leading
        lines_on_page[p] = line_no
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
        "The killer is: ______________________________   on page ______",
        "Now check your answer: turn to the Verdict with the same number as your killer’s page.",
    ]:
        y = b.text_block(x0, x1, y, para) - 10
    b.next()

    # --- The Verdict: one entry per register page; only the killer's page confirms the answer
    killer, pair = solution["killer_index"], solution["pair"]
    innocent = pair[0] if pair[1] == killer else pair[1]
    killer_page, innocent_page = reg.page_of[killer], reg.page_of[innocent]

    def verdict(p):
        no = reg.page_no(p)
        if p == killer_page:
            ln, at = position[killer]
            total = lines_on_page[p]
            where = ("line %d from the top" % ln if ln <= (total + 1) // 2
                     else "line %d from the bottom" % (total - ln + 1))
            return ("You have found the killer’s page. The guilty guest is name %d on %s of the names on "
                    "page %d. If that is your guest, turn to the second-to-last page of the book and turn "
                    "the book upside down." % (at, where, no))
        if p == innocent_page:
            return ("One guest on page %d did slip away from the dance floor, but not the one the Fairy "
                    "Godmother saw. Look at the Final Deduction again." % no)
        kind, k = solution["page_hints"][p]
        if kind == "single":
            return "Nobody on page %d is the killer: Clue %d rules out every guest here." % (no, k)
        return ("Nobody on page %d is the killer. Using the clues in order, the last guest here is ruled out "
                "by Clue %d." % (no, k))

    def verdict_page_start(first):
        x0, x1 = b.margins()
        c.setFont(SERIF_B, 16)
        c.drawCentredString(W / 2, H - TOP - 20, "The Verdict" if first else "The Verdict (continued)")
        y = H - TOP - 44
        if first:
            y = b.text_block(x0, x1, y, "Find the entry with the same number as your killer’s page. Read "
                             "only that one.", font=SERIF_I, size=10, leading=13) - 8
        return x0, x1, y

    x0, x1, y = verdict_page_start(True)
    for p in range(len(reg.pages)):
        text_ = verdict(p)
        lines_needed = 1 + int(stringWidth(text_, SERIF, 9) / (x1 - x0 - 28))
        if y - lines_needed * 11.5 < BOTTOM:
            b.next()
            x0, x1, y = verdict_page_start(False)
        c.setFont(SERIF_B, 9)
        c.drawRightString(x0 + 20, y, str(reg.page_no(p)))
        y = b.text_block(x0 + 28, x1, y, text_, size=9, leading=11.5) - 4
    b.next()

    # --- Notes, then a warning page, then the ending upside down on its back
    def notes_page(title="Notes"):
        x0, x1 = b.margins()
        c.setFont(SERIF_B, 16)
        c.drawCentredString(W / 2, H - TOP - 20, title)
        c.setLineWidth(0.4)
        c.setStrokeGray(0.6)
        y = H - TOP - 60
        while y > BOTTOM + 20:
            c.line(x0, y, x1, y)
            y -= 24
        c.setStrokeGray(0)
        b.next()

    notes_page()
    if b.pdf_page % 2 == 0:            # the warning must be a right-hand page, the ending on its back
        notes_page()
    x0, x1 = b.margins()
    c.setFont(SERIF_B, 20)
    c.drawCentredString(W / 2, H / 2 + 30, "Stop!")
    b.text_block(x0 + 20, x1 - 20, H / 2, "The other side of this page tells you who killed Prince Charming. "
                 "Turn over only when the Verdict sends you here.", size=11, leading=15, align="center")
    b.next()

    names = {"killer": reg.flat[killer], "innocent": reg.flat[innocent]}
    names["motive"] = rng.choice(MOTIVES).format(**names)
    c.saveState()
    c.translate(W, H)
    c.rotate(180)
    x0, x1 = OUTER, W - OUTER
    c.setFont(SERIF_B, 16)
    c.drawCentredString(W / 2, H - TOP - 20, "The Truth")
    y = H - TOP - 55
    for i, para in enumerate(ENDING):
        y = b.text_block(x0, x1, y, para.format(**names), font=SERIF_B if i == 0 else SERIF,
                         size=12 if i == 0 else 10.5, leading=16 if i == 0 else 14) - 8
    y -= 6
    for s_ in solution["suspects"]:
        y = b.text_block(x0, x1, y, "%s: page %d, chapter %d, %d letters." % (
            s_["name"], s_["page"], s_["chapter"], len(letters(s_["name"]))), font=SERIF_I, size=9.5,
            leading=12)
    c.restoreState()
    b.next()
    notes_page()
    if (b.pdf_page - 1) % 2:               # an even page count, as print interiors expect
        c.setFont(SERIF, 1)
        c.drawString(0, 0, " ")
        b.next()
    c.save()
    return b.pdf_page - 1


def _about(n):
    """Checkpoint name counts: exact when small, rounded when large."""
    if n < 100:
        return str(n)
    if n < 1000:
        return "about %d" % (round(n, -1))
    return "about %s" % format(int(round(n, -2)), ",")
