"""Render the whole book as a print-ready 6 x 9 inch interior PDF (needs reportlab).

Layout per case follows Who Killed Mr Darcy?: a case title page, the story,
the clues (each with how it works and an example), the ledger (names separated
by dots, pages numbered), then an answer page with the check line. The rules
are printed once, at the front. All solutions are at the very back, upside
down on the back of a Stop page.
"""

import random
import re

from whodunit.render import BOTTOM, INNER, OUTER, SERIF, SERIF_B, SERIF_I, TOP, H, W, LayoutError

from . import story
from .book import verdicts
from .render import REG_LEADING, REG_SIZE, Book, draw_row, layout_rows

NUMBERS = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve"]


def example(clue, led, avoid, rng):
    """For a clue about the name itself: one name from this list that qualifies and one that doesn't."""
    if not clue.word or clue.key == "mastermind_name":
        return ""
    names = sorted({n for n in led.flat if n not in avoid})
    rng.shuffle(names)
    yes = next((n for n in names if verdicts(clue, n) == {True}), None)
    no = next((n for n in names if verdicts(clue, n) == {False}), None)
    if not yes or not no:
        return ""
    return "%s qualifies; %s doesn't." % (yes, no)


class FullBook(Book):
    def __init__(self, path):
        super().__init__(path)
        self.c.setTitle(story.TITLE)

    def blank(self):
        self.next()

    def notes(self):
        x0, x1 = self.margins()
        y = self.heading("Notes") - 10
        self.c.setLineWidth(0.4)
        self.c.setStrokeGray(0.6)
        while y > BOTTOM + 20:
            self.c.line(x0, y, x1, y)
            y -= 24
        self.c.setStrokeGray(0)
        self.next()

    def to_right(self, with_notes=False):
        if self.pdf_page % 2 == 0:
            self.notes() if with_notes else self.next()

    def text_page(self, title, paragraphs, size=10.5, leading=14.5, gap=9):
        x0, x1 = self.margins()
        y = self.heading(title)
        for p in paragraphs:
            if isinstance(p, tuple):
                head, text = p
                self.c.setFont(SERIF_B, size)
                self.c.drawString(x0, y, head)
                y = self.para(x0, x1, y - (leading - 0.5), text, size=size - 0.5, leading=leading - 1) - gap
            else:
                y = self.para(x0, x1, y, p, size=size, leading=leading) - gap
            if y < BOTTOM:
                raise LayoutError("text page %r overflows" % title)
        self.next()

    def clue_pages(self, clues, examples, intro):
        x0, x1 = self.margins()
        y = self.heading("The Clues")
        y = self.para(x0, x1, y, intro, font=SERIF_I) - 10
        for n, cl in enumerate(clues, 1):
            parts = [(cl.story, SERIF_I, 10, 13), ("Rule: " + cl.rule, SERIF_B, 10.5, 14), (cl.how, SERIF, 9.5, 12.5)]
            if examples.get(cl.key):
                parts.append(("Example: " + examples[cl.key], SERIF_I, 9.5, 12.5))
            need = 16 + sum(len(self.wrap(t, x1 - x0, f, s)) * l + 3 for t, f, s, l in parts) + 8
            if y - need < BOTTOM:
                self.next()
                x0, x1 = self.margins()
                y = H - TOP - 20
            self.c.setFont(SERIF_B, 10)
            self.c.drawString(x0, y, "CLUE %d" % n)
            self.c.setFont(SERIF_B, 11)
            self.c.drawString(x0 + 48, y, cl.title)
            y -= 15
            for t, f, s, l in parts:
                y = self.para(x0, x1, y, t, font=f, size=s, leading=l) - 3
            y -= 8
        self.next()

    def ledger(self, led, page_from):
        """Draw a ledger with pages numbered from page_from; returns {flat index: (row, place)}."""
        led.first_page_no = page_from
        starts = {s: (k, place) for k, (place, s) in enumerate(led.chapters)}
        position, i = {}, 0
        for p, names in enumerate(led.pages):
            x0, x1 = self.margins()
            y = H - TOP
            if p in starts:
                k, place = starts[p]
                self.c.setFont(SERIF, 10)
                self.c.drawCentredString(W / 2, y - 4, "CHAPTER %s" % NUMBERS[k].upper())
                self.c.setFont(SERIF_B, 16)
                self.c.drawCentredString(W / 2, y - 26, place)
                y -= 52
            rows = layout_rows(names, x1 - x0, REG_SIZE)
            for r_no, row in enumerate(rows, 1):
                draw_row(self.c, x0, x1, y, row, REG_SIZE, justify=r_no < len(rows))
                for at in range(1, len(row) + 1):
                    position[i] = (r_no, at)
                    i += 1
                y -= REG_LEADING
            if y + REG_LEADING - REG_SIZE < BOTTOM:
                raise LayoutError("ledger page %d overflows" % led.page_no(p))
            self.footer(led.page_no(p))
            self.next()
        return position

    def answer_page(self, who, what, check):
        x0, x1 = self.margins()
        y = self.heading("Your Answer")
        y = self.para(x0, x1, y, "When you have used all the clues, one name is left.") - 18
        y = self.para(x0, x1, y, "%s:  ______________________________   page  ______" % who, size=11) - 26
        n_letters, total = check
        self.c.setFont(SERIF_B, 11)
        self.c.drawString(x0, y, "Check your answer")
        y = self.para(x0, x1, y - 15, "%s name has %d letters, and they add up to %d. Give each letter its place in "
                      "the alphabet, A = 1, B = 2 and so on to Z = 26, and add them up. For example, ROSA is "
                      "18 + 15 + 19 + 1 = 53." % (what, n_letters, total), size=10, leading=13.5) - 8
        self.para(x0, x1, y, "Plenty of names add up to %d, so this gives nothing away. If yours doesn't match, "
                  "recheck your clues before you go on." % total, size=10, leading=13.5)
        self.next()


def render_book(book, path, seed=1):
    rng = random.Random(seed)
    b = FullBook(path)
    c = b.c

    # Title page and its blank back
    c.setFont(SERIF_B, 26)
    c.drawCentredString(W / 2, H / 2 + 50, story.TITLE)
    total = sum(len(c.ledger.flat) for c in book.cases) + len(book.finale.ledger.flat)
    subtitle = story.SUBTITLE.format(thousands=format(total // 1000 * 1000, ","))
    c.setSubject(subtitle)
    y = b.para(OUTER + 30, W - OUTER - 30, H / 2 + 10, subtitle, size=12, leading=16, align="center")
    b.next()
    x0, x1 = b.margins()
    y = BOTTOM + 120
    for p in story.COPYRIGHT:
        y = b.para(x0, x1, y, p, size=8.5, leading=11) - 6
    b.next()

    b.text_page("Juniper Falls", story.INTRO)
    b.text_page("How This Book Works", story.HOW)
    b.text_page("Before You Start", story.BEFORE, size=10.5, leading=14, gap=7)

    page_no = 1
    positions = []
    for k, case in enumerate(book.cases):
        t, s = case.plan, story.CASES[case.plan.key]
        b.to_right(with_notes=True)
        # Case title page and the story on its back... the story faces the clues
        c.setFont(SERIF, 12)
        c.drawCentredString(W / 2, H / 2 + 40, "CASE %s" % t.number.upper())
        c.setFont(SERIF_B, 26)
        c.drawCentredString(W / 2, H / 2, t.shop)
        c.setFont(SERIF_I, 12)
        c.drawCentredString(W / 2, H / 2 - 30, "%s, %s" % (s["when"], s["event"]))
        b.next()
        b.text_page(t.place[0].upper() + t.place[1:], s["story"] + [
            "Your case file is %s: %s names. Somewhere inside is the killer." % (
                s["list_name"], format(len(case.ledger.flat), ","))])
        ex = {cl.key: example(cl, case.ledger, {case.ledger.flat[case.killer]}, rng) for cl in case.clues}
        b.clue_pages(case.clues, ex, "The killer is hidden in %s. Every clue below is true of the killer." %
                     s["list_name"])
        b.to_right(with_notes=True)
        positions.append(b.ledger(case.ledger, page_no))
        page_no += len(case.ledger.pages)
        b.answer_page("The %s killer is" % t.shop[4:].lower(), "The killer's", case.check)

    # The finale
    f = book.finale
    b.to_right(with_notes=True)
    c.setFont(SERIF, 12)
    c.drawCentredString(W / 2, H / 2 + 40, "THE FINALE")
    c.setFont(SERIF_B, 26)
    c.drawCentredString(W / 2, H / 2, "The Town Meeting")
    b.next()
    b.text_page("The Town Meeting", story.FINALE["story"] + [
        "Your case file is the town register: %s names. Somewhere inside is the mastermind." %
        format(len(f.ledger.flat), ",")])
    fex = {}
    b.clue_pages(f.clues, fex, "The mastermind is hidden in the town register. Every clue below is true of the "
                 "mastermind.")
    b.to_right(with_notes=True)
    fpos = b.ledger(f.ledger, page_no)
    b.answer_page("The mastermind is", "The mastermind's", f.check)

    # Stop, then the solutions upside down on its back
    b.to_right(with_notes=True)
    x0, x1 = b.margins()
    c.setFont(SERIF_B, 22)
    c.drawCentredString(W / 2, H / 2 + 30, "Stop!")
    b.para(x0 + 20, x1 - 20, H / 2, "The other side of this page gives every answer in the book, and the "
           "mastermind's story. Turn over only when you have finished.", size=11, align="center")
    b.next()

    def upside_down(draw):
        c.saveState()
        c.translate(W, H)
        c.rotate(180)
        draw()
        c.restoreState()
        b.next()

    def answers():
        x0, x1 = OUTER, W - OUTER
        c.setFont(SERIF_B, 16)
        c.drawCentredString(W / 2, H - TOP - 18, "The Solutions")
        y = H - TOP - 52
        for case, pos in zip(book.cases, positions):
            led, i = case.ledger, case.killer
            p = led.page_of[i]
            row, at = pos[i]
            killer = led.flat[i]
            c.setFont(SERIF_B, 11)
            c.drawString(x0, y, "Case %s, %s: %s" % (case.plan.number, case.plan.shop, killer))
            y = b.para(x0, x1, y - 14, "Page %d, row %d, name %d on the row. %s" % (
                led.page_no(p), row, at, story.CASES[case.plan.key]["ending"].format(killer=killer)),
                size=9.5, leading=12.5) - 8
        initials = "".join(case.ledger.flat[case.killer][0] for case in book.cases)
        y = b.para(x0, x1, y, "The first letters, %s, spell %s." % (", ".join(initials), book.mastermind),
                   font=SERIF_I, size=10)

    def finale():
        x0, x1 = OUTER, W - OUTER
        c.setFont(SERIF_B, 16)
        c.drawCentredString(W / 2, H - TOP - 18, "The Mastermind")
        y = H - TOP - 52
        who = f.ledger.flat[f.killer]
        for k, p in enumerate(story.FINALE["ending"]):
            y = b.para(x0, x1, y, p.format(mastermind=who), font=SERIF_B if k == 0 else SERIF,
                       size=12.5 if k == 0 else 10.5) - 8
        p = f.ledger.page_of[f.killer]
        row, at = fpos[f.killer]
        b.para(x0, x1, y, "%s is on page %d of the town register, row %d, name %d on the row." % (
            who, f.ledger.page_no(p), row, at), font=SERIF_I, size=10)

    upside_down(answers)
    # The mastermind's story is printed upside down too, on a right-hand page after a blank.
    upside_down(finale)
    if (b.pdf_page - 1) % 2:
        b.notes()
    c.save()
    return dict(pages=b.pdf_page - 1, positions=positions, finale_positions=fpos)
