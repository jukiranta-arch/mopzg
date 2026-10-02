"""Render the whole book as a print-ready 6 x 9 inch interior PDF (needs reportlab and Pillow).

Front matter: title page, copyright, contents, the town map facing the introduction, How This Book Works,
Before You Start. Then each case: an opening page (picture and story) facing the clues, the list (pages
numbered from 1 through the whole book), and an answer page with the check line and the evidence. The last
answer page says Stop; the solutions are printed upside down on its back. There are no notes pages: none of
the winners' samples has them between cases.

The look (fonts, running heads, name rows, pictures) lives in village.design.
"""

import random

from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from . import story
from .book import verdicts
from .design import (BODY, BODY_B, BODY_I, BOTTOM, BOX_GREY, CHAPTER_SIZE, DISPLAY, DISPLAY_B, DISPLAY_I,
                     FOLIO_SIZE, FOLIO_Y, H, HEAD_GREY, HEAD_Y, INNER, NAME_LEADING, NAME_LEADING_MAX, NAME_SIZE, OUTER,
                     SOLUTION_HEAD_SIZE, TEXT_LEADING, TEXT_SIZE, TOP, W, Art, LayoutError, TextOverflow,
                     CAP_HEIGHT, balance_rows, draw_name_row, ornament, tracked, wrap)

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


CLUE_HEAD = 17          # from a clue's heading to its first line, past the rule under the heading
BOX_PAD_X, BOX_PAD_Y = 7, 4


def rule_box(n_lines, st):
    """Where a clue's Rule box sits, measured down from the next line position under the witness line. The grey
    runs from the top of the capitals to the last baseline (plus a little for descenders), with the same padding
    above and below, so the words sit in the middle of it."""
    rs, rl = st["rule"]
    first = 3                                                # the first baseline of the rule
    top = first - BOX_PAD_Y - CAP_HEIGHT * rs                # the top of the grey (above the line position)
    bottom = first + (n_lines - 1) * rl + 0.16 * rs + BOX_PAD_Y
    return dict(top=top, first=first, bottom=bottom, used=bottom + 4 + 0.72 * st["how"][0])


def drop_lines(cap):
    """Lines a drop capital spans: three, or four for capitals that hang below the line."""
    return 4 if cap in "JQ" else 3


class FullBook:
    def __init__(self, path, art=None):
        self.c = canvas.Canvas(path, pagesize=(W, H), initialFontName=BODY, initialFontSize=10)
        self.c.setTitle(story.TITLE)
        self.art = art or Art()
        self.pdf_page = 1
        self.blanks = 0

    # ------------------------------------------------------------ pages and furniture

    def margins(self):
        return (INNER, W - OUTER) if self.pdf_page % 2 == 1 else (OUTER, W - INNER)

    def centre(self):
        x0, x1 = self.margins()
        return (x0 + x1) / 2

    def next(self):
        self.c.showPage()
        self.pdf_page += 1

    def to_right(self):
        """Start the next page on the right; the lists must, for the facing-page clues."""
        if self.pdf_page % 2 == 0:
            self.blanks += 1
            self.next()

    def running_head(self, section):
        """The book's title over left-hand pages, the section over right-hand ones."""
        text = story.TITLE if self.pdf_page % 2 == 0 else section
        tracked(self.c, text.upper(), self.centre(), HEAD_Y, BODY, 7.5, track=1.5, grey=HEAD_GREY)

    def para(self, x0, x1, y, text, font=BODY, size=TEXT_SIZE, leading=TEXT_LEADING, align="left",
             dropcap=False):
        c = self.c
        indent, n_drop = 0, 0
        if dropcap:
            cap, text = text[0], text[1:]
            cap_size = (2 * leading + 0.66 * size) / 0.708          # Playfair's capitals are 0.708 em tall
            c.setFont(DISPLAY, cap_size)
            c.drawString(x0, y - 2 * leading, cap)
            indent, n_drop = c.stringWidth(cap, DISPLAY, cap_size) + 4, drop_lines(cap)
        lines = wrap(text, x1 - x0, font, size, first_w=x1 - x0 - indent, first_n=n_drop)
        c.setFont(font, size)
        for k, ln in enumerate(lines):
            if align == "center":
                c.drawCentredString((x0 + x1) / 2, y, ln)
            else:
                c.drawString(x0 + (indent if k < n_drop else 0), y, ln)
            y -= leading
        if len(lines) < n_drop:
            y -= (n_drop - len(lines)) * leading
        return y

    @staticmethod
    def para_height(x0, x1, text, font=BODY, size=TEXT_SIZE, leading=TEXT_LEADING, dropcap=False):
        n_drop = drop_lines(text[0]) if dropcap else 0
        n = len(wrap(text, x1 - x0, font, size, first_w=x1 - x0 - 3 * size, first_n=n_drop))
        return max(n, n_drop) * leading

    def heading(self, title, y=None, size=22):
        """A page heading in the display face with the divider under it; returns where the text starts."""
        y = y if y is not None else H - TOP - 14
        cx = self.centre()
        self.c.setFont(DISPLAY, size)
        self.c.drawCentredString(cx, y, title)
        ornament(self.c, cx, y - 15, self.art)
        return y - 42

    def text_page(self, title, paragraphs, section=None, size=TEXT_SIZE, leading=TEXT_LEADING, gap=9,
                  dropcap=False):
        """A heading and paragraphs (a paragraph may be a (bold lead, text) pair). If the words don't fit,
        the type steps down a little, never below 9.3 pt."""
        x0, x1 = self.margins()
        for step in range(4):
            s, l, g = size - 0.35 * step, leading - 0.45 * step, max(gap - step, 5)
            need = 0
            for k, p in enumerate(paragraphs):
                if isinstance(p, tuple):
                    need += l + self.para_height(x0, x1, p[1], size=s - 0.5, leading=l - 1) + g
                else:
                    need += self.para_height(x0, x1, p, size=s, leading=l, dropcap=dropcap and k == 0) + g
            if H - TOP - 56 - need >= BOTTOM - l:
                break
        else:
            raise TextOverflow("text page %r overflows" % title)
        if section:
            self.running_head(section)
        y = self.heading(title)
        for k, p in enumerate(paragraphs):
            if isinstance(p, tuple):
                head, text = p
                self.c.setFont(BODY_B, s)
                self.c.drawString(x0, y, head)
                y = self.para(x0, x1, y - (l - 0.5), text, size=s - 0.5, leading=l - 1) - g
            else:
                y = self.para(x0, x1, y, p, size=s, leading=l, dropcap=dropcap and k == 0) - g
        self.next()

    # ------------------------------------------------------------ front matter

    def title_page(self, tagline, subtitle):
        c, cx = self.c, W / 2
        x0, x1 = self.margins()
        art_h = 3.3 * inch
        self.art.draw(c, "title", x0, H - TOP - art_h, x1 - x0, art_h, "Main Street, Juniper Falls")
        y = H - TOP - art_h - 0.6 * inch
        c.setFont(DISPLAY, 21)
        c.drawCentredString(cx, y, "Murder in")
        c.setFont(DISPLAY_B, 36)
        c.drawCentredString(cx, y - 40, "Juniper Falls")
        ornament(c, cx, y - 60, self.art, w=120)
        c.setFont(DISPLAY_I, 13.5)
        c.drawCentredString(cx, y - 90, subtitle)
        tracked(c, tagline.upper(), cx, y - 116, BODY, 8.5, track=1.4, grey=HEAD_GREY)
        self.next()

    def copyright_page(self):
        x0, x1 = self.margins()
        y = BOTTOM + 150
        for p in story.COPYRIGHT + ["Typeset in Charis SIL and Playfair Display."]:
            y = self.para(x0, x1, y, p, size=8.5, leading=11.5) - 6
        self.next()

    def contents_page(self, entries):
        """entries: (title, text at the right, or ""); None as the title leaves a gap."""
        c = self.c
        x0, x1 = self.margins()
        y = self.heading("Contents") - 6
        for title, right in entries:
            if title is None:
                y -= 10
                continue
            c.setFont(BODY, 10.5)
            c.drawString(x0, y, title)
            if right:
                rw = c.stringWidth(right, BODY_I, 10)
                c.setFont(BODY_I, 10)
                c.drawString(x1 - rw, y, right)
                lead_from, lead_to = x0 + c.stringWidth(title, BODY, 10.5) + 8, x1 - rw - 6
                c.setFillGray(0.55)
                c.setFont(BODY, 10)
                x = lead_to - 3
                while x > lead_from:
                    c.drawString(x, y, ".")
                    x -= 5
                c.setFillGray(0)
            y -= 19
        c.setFillGray(HEAD_GREY)
        self.para(x0, x1, y - 14, "Page numbers are the numbers printed at the foot of the list pages.",
                  font=BODY_I, size=9.5, leading=12.5)
        c.setFillGray(0)
        self.next()

    def map_page(self):
        x0, x1 = self.margins()
        c = self.c
        c.setFont(DISPLAY_I, 13)
        c.drawCentredString(self.centre(), H - TOP - 6, "Juniper Falls")
        self.art.draw(c, "map", x0, BOTTOM, x1 - x0, H - TOP - 26 - BOTTOM, "the town map")
        self.next()

    # ------------------------------------------------------------ a case

    def opening(self, label, title, when, art_key, paragraphs):
        """The first page of a case: label, name, picture and story, facing the first page of clues. The
        picture takes the room the story leaves, between 1.6 and 2.9 inches tall."""
        c = self.c
        x0, x1 = self.margins()
        cx = self.centre()
        top = H - TOP + 6
        c.setFont(BODY, 9)
        c.setFillGray(HEAD_GREY)
        c.drawCentredString(cx, top, label)
        c.setFillGray(0)
        c.setFont(DISPLAY, 27)
        c.drawCentredString(cx, top - 32, title)
        y = top - 32
        if when:
            c.setFont(DISPLAY_I, 12.5)
            c.drawCentredString(cx, y - 20, when)
            y -= 20
        y -= 14
        for size, leading, gap in ((10.3, 14, 7), (10, 13.4, 6), (9.7, 13, 5)):
            text_h = sum(self.para_height(x0, x1, p, size=size, leading=leading, dropcap=k == 0) + gap
                         for k, p in enumerate(paragraphs))
            art_h = min(2.9 * inch, y - 12 - size - text_h - (BOTTOM - leading))
            if art_h >= 1.6 * inch:
                break
        else:
            raise TextOverflow("opening page %r overflows" % title)
        self.art.draw(c, art_key, x0, y - art_h, x1 - x0, art_h, title)
        y -= art_h + 12 + size
        for k, p in enumerate(paragraphs):
            y = self.para(x0, x1, y, p, size=size, leading=leading, dropcap=k == 0) - gap
        self.next()

    CLUE_STYLES = [  # story size and leading, rule size and leading, how size and leading, space after a clue
        dict(story=(9.6, 12.4), rule=(10, 13.0), how=(9.4, 12.2), after=13),
        dict(story=(9.3, 11.9), rule=(9.8, 12.6), how=(9.1, 11.7), after=12),
        dict(story=(9.1, 11.5), rule=(9.6, 12.2), how=(8.9, 11.3), after=11),
        dict(story=(8.9, 11.1), rule=(9.4, 11.8), how=(8.7, 10.9), after=10),
    ]

    def _clue_blocks(self, clues, examples, width, st):
        """Each clue as its parts and height, in the given style."""
        blocks = []
        for cl in clues:
            rule = wrap("Rule: " + cl.rule, width - 2 * BOX_PAD_X, BODY_B, st["rule"][0])
            parts = [(cl.story, BODY_I) + st["story"], (cl.how, BODY) + st["how"]]
            if examples.get(cl.key):
                parts.append(("Example: " + examples[cl.key], BODY_I) + st["how"])
            h = (CLUE_HEAD + 3 + rule_box(len(rule), st)["used"] +
                 sum(len(wrap(t, width, f, s)) * l + 2 for t, f, s, l in parts) + st["after"])
            blocks.append((cl, rule, parts, h))
        return blocks

    def _clue_breaks(self, blocks, first_top, top):
        """Which clues start a new page."""
        breaks, y = set(), first_top
        for k, (_, _, _, h) in enumerate(blocks):
            if y - h < BOTTOM - 8 - 9:
                breaks.add(k)
                y = top
            y -= h
        return breaks

    def clue_pages(self, clues, examples, section, pages=2):
        """The clues, in the loosest style that fits them on `pages` pages (so the list starts on the right
        without a blank page)."""
        c = self.c
        x0, x1 = self.margins()
        first_top = H - TOP - 14 - 42
        for st in self.CLUE_STYLES:
            blocks = self._clue_blocks(clues, examples, x1 - x0, st)
            breaks = self._clue_breaks(blocks, first_top, H - TOP + 6)
            if len(breaks) + 1 <= pages:
                break
        if len(breaks) + 1 < pages:           # fewer pages would put the list on a left-hand page: split evenly
            breaks = {len(blocks) * k // pages for k in range(1, pages)}
        self.running_head(section)
        y = self.heading("The Clues")
        y += 4
        for n, (cl, rule, parts, h) in enumerate(blocks, 1):
            if n - 1 in breaks:
                self.next()
                x0, x1 = self.margins()
                self.running_head(section)
                y = H - TOP + 6
            c.setFont(BODY_B, 9)
            c.setFillGray(HEAD_GREY)
            c.drawString(x0, y, "CLUE %d" % n)
            c.setFillGray(0)
            c.setFont(DISPLAY_B, 12.5)
            c.drawString(x0 + 44, y, cl.title)
            c.setStrokeGray(0.62)
            c.setLineWidth(0.5)
            c.line(x0, y - 5, x1, y - 5)
            c.setStrokeGray(0)
            y -= CLUE_HEAD
            t, f, s, l = parts[0]
            y = self.para(x0, x1, y, t, font=f, size=s, leading=l) - 3
            g = rule_box(len(rule), st)
            c.setFillGray(BOX_GREY)
            c.roundRect(x0, y - g["bottom"], x1 - x0, g["bottom"] - g["top"], 2.5, stroke=0, fill=1)
            c.setFillGray(0)
            c.setFont(BODY_B, st["rule"][0])
            yy = y - g["first"]
            for ln in rule:
                c.drawString(x0 + BOX_PAD_X, yy, ln)
                yy -= st["rule"][1]
            y -= g["used"]
            for t, f, s, l in parts[1:]:
                y = self.para(x0, x1, y, t, font=f, size=s, leading=l) - 2
            y -= st["after"]
        self.next()

    def ledger(self, led, page_from, section):
        """The list, pages numbered from page_from; returns {flat index: (row, place)}."""
        c = self.c
        led.first_page_no = page_from
        starts = {s: (k, place) for k, (place, s) in enumerate(led.chapters)}
        position, i = {}, 0
        for p, names in enumerate(led.pages):
            x0, x1 = self.margins()
            cx = self.centre()
            self.running_head(section)
            y = H - TOP
            if p in starts:
                k, place = starts[p]
                c.setFont(DISPLAY_I, 12)
                c.drawCentredString(cx, y - 2, "Chapter %s" % NUMBERS[k])
                c.setFont(DISPLAY, CHAPTER_SIZE)
                c.drawCentredString(cx, y - 26, place)
                ornament(c, cx, y - 39, self.art, w=70)
                y -= 62
            rows = balance_rows(names, x1 - x0)
            # Fill the page to the foot, as the winners' pages are, by opening the leading a little; the last
            # page of a list is left as it falls.
            leading = NAME_LEADING
            if p < len(led.pages) - 1 and len(rows) > 1:
                leading = max(NAME_LEADING, min(NAME_LEADING_MAX, (y - BOTTOM - NAME_SIZE) / (len(rows) - 1)))
            for r_no, row in enumerate(rows, 1):
                draw_name_row(c, x0, x1, y, row, last=r_no == len(rows))
                for at in range(1, len(row) + 1):
                    position[i] = (r_no, at)
                    i += 1
                y -= leading
            if y + leading - NAME_SIZE < BOTTOM - 0.01:
                raise LayoutError("ledger page %d overflows" % led.page_no(p))
            c.setFont(BODY, FOLIO_SIZE)
            c.drawCentredString(cx, FOLIO_Y, str(led.page_no(p)))
            self.next()
        return position

    def answer_page(self, who, what, check, section, evidence=None, stop=False):
        c = self.c
        x0, x1 = self.margins()
        cx = self.centre()
        self.running_head(section)
        y = self.heading("Your Answer")
        y = self.para(x0, x1, y, "When you have used all the clues, one name is left.") - 22
        c.setFont(BODY, 11)
        c.drawString(x0, y, "%s:" % who)
        c.setLineWidth(0.6)
        c.line(x0 + c.stringWidth("%s:" % who, BODY, 11) + 8, y - 2, x1, y - 2)
        y -= 28
        c.drawString(x0, y, "on list page:")
        c.line(x0 + c.stringWidth("on list page:", BODY, 11) + 8, y - 2, x0 + 150, y - 2)
        y -= 34
        n_letters, total = check
        texts = [("%s name has %d letters, and they add up to %d. Give each letter its place in the alphabet, "
                  "A = 1, B = 2 and so on to Z = 26, and add them up. For example, ROSA is 18 + 15 + 19 + 1 = 53."
                  % (what, n_letters, total)),
                 ("Plenty of names add up to %d, so this gives nothing away. If yours doesn't match, recheck your "
                  "clues before you go on." % total)]
        inner = (x0 + 12, x1 - 12)
        box_h = 34 + sum(self.para_height(*inner, t, size=10, leading=13.5) + 6 for t in texts)
        c.setStrokeGray(0.45)
        c.setLineWidth(0.7)
        c.rect(x0, y - box_h + 12, x1 - x0, box_h)
        c.setStrokeGray(0)
        c.setFont(DISPLAY_B, 13)
        c.drawString(inner[0], y - 8, "Check your answer")
        yy = y - 27
        for t in texts:
            yy = self.para(*inner, yy, t, size=10, leading=13.5) - 6
        y -= box_h + 18
        if stop:
            c.setFont(DISPLAY_B, 26)
            c.drawCentredString(cx, BOTTOM + 120, "Stop!")
            self.para(x0 + 20, x1 - 20, BOTTOM + 92, "The other side of this page gives every answer in the book, "
                      "and the mastermind's story. Turn over only when you have finished.", size=11, align="center")
        elif evidence:
            key, caption = evidence
            box = min(2.1 * inch, y - 4 - BOTTOM - 26)
            self.art.draw(c, key, cx - box / 2, y - 4 - box, box, box, "")
            c.setFont(BODY_I, 9.5)
            c.setFillGray(HEAD_GREY)
            c.drawCentredString(cx, y - 4 - box - 16, caption)
            c.setFillGray(0)
        self.next()


def render_book(book, path, seed=1, art=None):
    rng = random.Random(seed)
    b = FullBook(path, art)
    c = b.c
    total = sum(len(cs.ledger.flat) for cs in book.cases) + len(book.finale.ledger.flat)
    thousands = format(total // 1000 * 1000, ",")
    c.setSubject(story.SUBTITLE.format(thousands=thousands))

    # The list page numbers of each case, for the contents page
    ranges, page_no = [], 1
    for cs in list(book.cases) + [book.finale]:
        ranges.append((page_no, page_no + len(cs.ledger.pages) - 1))
        page_no += len(cs.ledger.pages)

    b.title_page("Over %s Suspects · 5 Linked Cases · 1 Mastermind" % thousands,
                 "A Find-the-Killer Murder Mystery Puzzle Book")
    b.copyright_page()
    entries = [("Juniper Falls", ""), ("How This Book Works", ""), ("Before You Start", ""), (None, "")]
    for cs, (a, z) in zip(book.cases, ranges):
        entries.append(("Case %s · %s" % (cs.plan.number, cs.plan.shop), "list pages %d–%d" % (a, z)))
    entries += [("The Finale · The Town Meeting", "list pages %d–%d" % ranges[-1]), (None, ""),
                ("The Solutions", "at the back, upside down")]
    b.contents_page(entries)
    b.map_page()                  # a left-hand page, facing the introduction
    b.text_page("Juniper Falls", story.INTRO, section="Juniper Falls", dropcap=True)
    b.text_page("How This Book Works", story.HOW, section="How This Book Works")
    b.text_page("Before You Start", story.BEFORE, section="Before You Start", size=10.3, leading=13.8, gap=7)

    page_no = 1
    positions = []
    for case in book.cases:
        t, s = case.plan, story.CASES[case.plan.key]
        section = "Case %s · %s" % (t.number, t.shop)
        if b.pdf_page % 2 == 1:
            raise TextOverflow("case %s would open on a right-hand page, away from its clues" % t.key)
        b.opening("CASE %s" % t.number.upper(), t.shop, "%s, %s" % (s["when"], s["event"]), "case_" + t.key,
                  s["story"] + ["Your case file is %s: %s names. Somewhere inside is the killer, and every "
                                "clue that follows is true of the killer." % (
                                    s["list_name"], format(len(case.ledger.flat), ","))])
        ex = {cl.key: example(cl, case.ledger, {case.ledger.flat[case.killer]}, rng) for cl in case.clues}
        b.clue_pages(case.clues, ex, section)
        b.to_right()
        positions.append(b.ledger(case.ledger, page_no, section))
        page_no += len(case.ledger.pages)
        b.answer_page("The %s killer is" % t.shop[4:].lower(), "The killer's", case.check, section,
                      evidence=("evidence_" + t.key, "Evidence No. %d: %s" % (len(positions), s["token"])))

    # The finale
    f = book.finale
    section = "The Finale · The Town Meeting"
    b.opening("THE FINALE", "The Town Meeting", "", "case_finale", story.FINALE["story"] + [
        "Your case file is the town register: %s names. Somewhere inside is the mastermind, and every clue "
        "that follows is true of the mastermind." % format(len(f.ledger.flat), ",")])
    b.clue_pages(f.clues, {}, section)
    b.to_right()
    fpos = b.ledger(f.ledger, page_no, section)
    # The last answer page says Stop, so it must be a right-hand page with the solutions on its back
    b.to_right()
    b.answer_page("The mastermind is", "The mastermind's", f.check, section, stop=True)

    def upside_down(draw):
        c.saveState()
        c.translate(W, H)
        c.rotate(180)
        draw()
        c.restoreState()
        b.next()

    def answers():
        x0, x1 = OUTER, W - OUTER
        c.setFont(DISPLAY_B, SOLUTION_HEAD_SIZE)
        c.drawCentredString(W / 2, H - TOP - 14, "The Solutions")
        ornament(c, W / 2, H - TOP - 29, b.art)
        y = H - TOP - 54
        for case, pos in zip(book.cases, positions):
            led, i = case.ledger, case.killer
            row, at = pos[i]
            killer = led.flat[i]
            c.setFont(DISPLAY_B, 11.5)
            c.drawString(x0, y, "Case %s, %s: %s" % (case.plan.number, case.plan.shop, killer))
            y = b.para(x0, x1, y - 14, "List page %d, row %d, name %d on the row. %s" % (
                led.page_no(led.page_of[i]), row, at, story.CASES[case.plan.key]["ending"].format(killer=killer)),
                size=9.3, leading=12.2) - 8
        initials = "".join(case.ledger.flat[case.killer][0] for case in book.cases)
        b.para(x0, x1, y, "The first letters, %s, spell %s." % (", ".join(initials), book.mastermind),
               font=BODY_I, size=10)

    def finale():
        x0, x1 = OUTER, W - OUTER
        c.setFont(DISPLAY_B, SOLUTION_HEAD_SIZE)
        c.drawCentredString(W / 2, H - TOP - 14, "The Mastermind")
        ornament(c, W / 2, H - TOP - 29, b.art)
        y = H - TOP - 54
        who = f.ledger.flat[f.killer]
        for k, p in enumerate(story.FINALE["ending"]):
            y = b.para(x0, x1, y, p.format(mastermind=who), font=DISPLAY_B if k == 0 else BODY,
                       size=14 if k == 0 else 10.3, leading=18 if k == 0 else 14) - 8
        row, at = fpos[f.killer]
        b.para(x0, x1, y, "%s is on list page %d of the town register, row %d, name %d on the row." % (
            who, f.ledger.page_no(f.ledger.page_of[f.killer]), row, at), font=BODY_I, size=10)

    upside_down(answers)
    upside_down(finale)       # the mastermind's story, also upside down, facing the solutions
    if (b.pdf_page - 1) % 2:  # the page count must be even
        b.blanks += 1
        b.next()
    c.save()
    return dict(pages=b.pdf_page - 1, blanks=b.blanks, positions=positions, finale_positions=fpos,
                art_missing=sorted(set(b.art.missing)), art_used=b.art.used, art_low=b.art.low)
