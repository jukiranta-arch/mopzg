"""Render a generated puzzle as a print-ready 6 x 9 inch PDF (needs reportlab).

The layout follows the best sellers (briefs/2026-09-29_winners-samples.md):
- the register is plain first names in justified lines; fairy-tale characters in italics;
- chapters are places in the palace, each opened by a short scene;
- clue cards: a witness line, then a plain Rule, an example and a tick box, with
  checkpoints between the clue groups;
- hints at the back, then the solution upside down behind a warning page.
"""

import os
import random

from reportlab.lib.pagesizes import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .generate import GLANCE
from .model import BEARS, READINGS, ROYAL_WORDS, Register, letters, words
from .names import ENDING, MOTIVES, PLACES_INDOOR, PLACES_OUTDOOR, ROYALS, WITNESS

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
REG_SIZE, REG_LEADING = 10.5, 14      # register type: large and calm, as in The Killer Isn't Alice
GAP = 0.7                             # minimum space between names, in ems


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
        line, lines = "", []
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

    def heading(self, title, size=16):
        self.c.setFont(SERIF_B, size)
        self.c.drawCentredString(W / 2, H - TOP - 20, title)

    def footer(self, number):
        self.c.setFont(SERIF, 9)
        self.c.drawCentredString(W / 2, BOTTOM / 2, str(number))

    def notes_page(self, title="Notes"):
        x0, x1 = self.margins()
        self.heading(title)
        c = self.c
        c.setLineWidth(0.4)
        c.setStrokeGray(0.6)
        y = H - TOP - 60
        while y > BOTTOM + 20:
            c.line(x0, y, x1, y)
            y -= 24
        c.setStrokeGray(0)
        self.next()


def _verdicts(clue, name):
    one = Register([[name]], [("", 0)]).index()
    out = set()
    for r in READINGS:
        one.set_reading(r)
        out.add(bool(clue.test(one, 0)))
    return out


def _example_pair(reg, clue, rng, avoid=()):
    """One name that passes and one that fails, both unambiguous under every reading.
    Never a suspect's name: an example must not give the answer away."""
    plain = sorted({n for n in reg.flat if n not in reg.cast} - set(avoid))
    yes = [n for n in plain if _verdicts(clue, n) == {True}]
    no = [n for n in plain if _verdicts(clue, n) == {False}]
    return rng.choice(yes), rng.choice(no)


def _layout_lines(names, cast, width, size):
    """Split a page's names into lines that fit the width. Returns lists of names."""
    gap = GAP * size
    lines, line, used = [], [], 0.0
    for name in names:
        w = stringWidth(name, SERIF_I if name in cast else SERIF, size)
        if line and used + gap + w > width:
            lines.append(line)
            line, used = [], 0.0
        used += (gap if line else 0) + w
        line.append(name)
    if line:
        lines.append(line)
    return lines


def _draw_line(c, x0, x1, y, line, cast, size, justify):
    widths = [stringWidth(n, SERIF_I if n in cast else SERIF, size) for n in line]
    gap = GAP * size
    if justify and len(line) > 1:
        gap = (x1 - x0 - sum(widths)) / (len(line) - 1)
    x = x0
    for name, w in zip(line, widths):
        c.setFont(SERIF_I if name in cast else SERIF, size)
        c.drawString(x, y, name)
        x += w + gap


def _about(n):
    if n < 1000:
        return format(n, ",")
    return "about " + format(int(round(n, -2)), ",")


def _pages_list(nums):
    """1, 2, 3, 5, 9, 10 -> '1–3, 5, 9–10'"""
    nums = sorted(nums)
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(str(nums[i]) if i == j else "%d–%d" % (nums[i], nums[j]))
        i = j + 1
    return ", ".join(out)


def _where_to_look(reg, clue, example):
    """The second-level hint: facts from this register that make the clue easy to apply."""
    k = clue.key
    no = reg.page_no
    if k == "chapter_indoors":
        inside = [reg.chapters[i][0] for i in sorted(reg.indoor)]
        return "The chapters set inside the palace are: %s. Cross out every other chapter." % ", ".join(inside)
    if k == "three_bears":
        chs = sorted({reg.chapter_of_page[reg.page_of[j]] + 1 for j in range(len(reg.flat) - 2)
                      if tuple(reg.flat[j:j + 3]) == BEARS})
        return "The Three Bears stand together in chapter%s %s." % ("s" if len(chs) > 1 else "",
                                                                     ", ".join(map(str, chs)))
    if k == "between_hansel_gretel":
        return "Hansel is on page %d and Gretel is on page %d." % (
            no(reg.page_of[reg.flat.index("Hansel")]), no(reg.page_of[reg.flat.index("Gretel")]))
    if k == "near_wolf":
        return "The Big Bad Wolf is on pages %s." % _pages_list(
            {no(reg.page_of[j]) for j, n in enumerate(reg.flat) if n == "Big Bad Wolf"})
    if k == "royal_on_page":
        names = sorted({n for n in reg.flat if any(w in ROYAL_WORDS for w in words(n))})
        return "The royal guests are %s. Mark every page they appear on." % ", ".join(names)
    if k == "near_character":
        return ("Highlight each name in italics and the ten names on either side of it. Every name outside "
                "the highlights is crossed out.")
    if k == "odd_page":
        return "Cross out every even-numbered page."
    if k == "key_letter":
        return "Write the first letter of each page’s opening name at the top of the page, then check the names."
    return "Work name by name. %s" % example


def render(reg, clues, solution, path, title="Who Killed Prince Charming?",
           subtitle="A Fairy-Tale Murder Mystery Puzzle", edition_note="SAMPLE CASE"):
    rng = random.Random(solution["seed"])
    b = Book(path, title, subtitle)
    c = b.c
    n_names = solution["total_names"]
    avoid = [s_["name"] for s_ in solution["suspects"]]
    examples = {}
    for cl in clues:
        if cl.kind == "word":
            yes, no = _example_pair(reg, cl, rng, avoid)
            examples[cl.key] = "Example: %s is kept. %s is crossed out." % (yes, no)

    # --- Title page
    c.setFont(SERIF_B, 30)
    c.drawCentredString(W / 2, H - 2.4 * inch, "WHO KILLED")
    c.drawCentredString(W / 2, H - 2.9 * inch, "PRINCE CHARMING?")
    c.setFont(SERIF_I, 13)
    c.drawCentredString(W / 2, H - 3.4 * inch, subtitle)
    c.setFont(SERIF, 11)
    c.drawCentredString(W / 2, H - 3.9 * inch,
                        "%s guests · %d clues · 1 killer" % (format(n_names, ","), len(clues)))
    if edition_note:
        c.setFont(SERIF_B, 10)
        c.drawCentredString(W / 2, 1.2 * inch, edition_note)
    b.next()

    # --- The case
    x0, x1 = b.margins()
    b.heading("The Case")
    story = [
        "The Happily Ever After Ball was the event of the year. Every character from every tale had come, "
        "along with half the kingdom, and rather more wolves than anyone had invited.",
        "At the first stroke of midnight, Prince Charming fell face-first into the wedding cake. "
        "By the twelfth stroke he was dead.",
        "The Captain of the Guard barred the gates and wrote down the name of every guest, room by room and "
        "garden by garden: %s names in all. Witnesses agree that two guests slipped away from the dance "
        "floor just before midnight. One of them is the killer." % format(n_names, ","),
        "The witnesses have given %d clues. Every clue is true of both of the guests who slipped away. Work "
        "through the register, cross out every guest a clue rules out, and you will be left with two names. "
        "The Final Deduction tells you which of them did it." % len(clues),
        "All you need is a pencil, a highlighter, and a sharp eye.",
    ]
    y = H - TOP - 55
    for para in story:
        y = b.text_block(x0, x1, y, para) - 8
    b.next()

    # --- Rules
    x0, x1 = b.margins()
    b.heading("Before You Begin")
    rules = [
        ("One name, one guest.", "Every guest is written as a single first name. Some names appear more than "
         "once: each one is a different guest, so check each on its own."),
        ("Fairy-tale characters.", "Characters from the old tales are printed in italics, like Snow White. "
         "Each is one guest, however many words the name has."),
        ("Letters.", "Every printed letter counts. The vowels are A, E, I, O and U; every other letter is a "
         "consonant, and that includes Y."),
        ("Reading order.", "Names run left to right, line by line, page by page. A name never breaks across "
         "two lines."),
        ("Pages and chapters.", "Page numbers are printed at the foot of each register page. Each chapter is "
         "one place in the palace; The Palace page lists them all."),
        ("Clues in any order.", "The clues can be used in any order and you will reach the same two names. "
         "They are printed in a good order: first quick checks you make on every name, then clues about where "
         "the killer was that night, then the finest letter checks on the few names left."),
        ("Checkpoints.", "Between the groups of clues, a checkpoint tells you how many pages or names should "
         "still be in play. If yours is different, read the last clues again."),
        ("Stuck?", "Every clue has a hint at the back of the book. The solution is on the very last pages, "
         "upside down, behind a warning page."),
    ]
    y = H - TOP - 50
    for head, body in rules:
        c.setFont(SERIF_B, 10.5)
        c.drawString(x0, y, head)
        y = b.text_block(x0, x1, y - 13, body, size=10, leading=13) - 6
    b.next()

    # --- The Palace (contents) and the Who's Who
    x0, x1 = b.margins()
    b.heading("The Palace")
    y = b.text_block(x0, x1, H - TOP - 48, "The guards took down every name, place by place. These are the "
                     "chapters of the register.", font=SERIF_I, size=10, leading=13) - 8
    c.setFont(SERIF_B, 10)
    c.drawString(x0, y, "Chapter")
    c.drawRightString(x1, y, "Pages")
    y -= 16
    bounds = [s for _, s in reg.chapters] + [len(reg.pages)]
    for i, (place, start) in enumerate(reg.chapters):
        c.setFont(SERIF, 10.5)
        c.drawString(x0, y, "%d.  %s" % (i + 1, place))
        c.drawRightString(x1, y, "%d–%d" % (reg.page_no(start), reg.page_no(bounds[i + 1] - 1)))
        y -= 16
    y -= 16
    c.setFont(SERIF_B, 13)
    c.drawString(x0, y, "Who’s Who")
    y = b.text_block(x0, x1, y - 16, "Fairy-tale characters at the ball (printed in italics in the register): "
                     + ", ".join(sorted({n for n in reg.flat if n in reg.cast})) + ".", size=9.5, leading=12.5)
    b.next()

    # --- The clues, as cards, with checkpoints between the groups
    def clue_page_start(first):
        x0, x1 = b.margins()
        b.heading("The Clues" if first else "The Clues (continued)")
        return x0, x1, H - TOP - 50

    # Checkpoints after each group: the opening glance clues, the clues about where the killer
    # was, and the final letter clues.
    kinds = ["letter" if cl.kind == "word" or cl.key == "key_letter" else "place" for cl in clues]
    groups = [k for k in range(1, len(clues)) if kinds[k] != kinds[k - 1]]
    checkpoints = {cp["clue"]: cp for cp in solution["checkpoints"]}
    labels = iter("ABCDEFG")

    x0, x1, y = clue_page_start(True)
    for n, cl in enumerate(clues, 1):
        witness = WITNESS.get(cl.key, "")
        need = 30 + 13 * (2 + len(witness) // 60 + len(cl.text) // 60) + (13 if cl.key in examples else 0)
        if y - need < BOTTOM:
            b.next()
            x0, x1, y = clue_page_start(False)
        c.setFillGray(0.92)
        c.rect(x0, y - 4, x1 - x0, 17, stroke=0, fill=1)
        c.setFillGray(0)
        c.setFont(SERIF_B, 10)
        c.drawString(x0 + 6, y + 1, "CLUE %d" % n)
        c.rect(x1 - 16, y - 1, 9, 9)              # tick box
        y -= 20
        y = b.text_block(x0, x1, y, witness, font=SERIF_I, size=9.5, leading=12) - 3
        c.setFont(SERIF_B, 10.5)
        c.drawString(x0, y, "Rule:")
        y = b.text_block(x0 + 32, x1, y, cl.text, size=10.5, leading=13.5)
        if cl.key in examples:
            y = b.text_block(x0 + 32, x1, y - 1, examples[cl.key], font=SERIF_I, size=9.5, leading=12)
        y -= 12
        if n in groups or n == len(clues):
            cp = checkpoints[n]
            label = next(labels)
            if n == len(clues):
                text = "“If you have done it right,” says the Fairy Godmother, “two names are left. Now turn " \
                       "to the Final Deduction.”"
            elif kinds[n - 1] == "letter":
                text = ("“After clues 1 to %d,” says the Fairy Godmother, “there should be %s names left, and "
                        "still some on %s. More, and a name slipped past you. Fewer, and you crossed out "
                        "someone innocent.”" % (n, _about(cp["names"]), "every page" if cp["pages"] ==
                                                len(reg.pages) else "%d pages" % cp["pages"]))
            else:
                text = ("“After clues 1 to %d,” says the Fairy Godmother, “there should be %s names left, on "
                        "%d pages. Check again before the last clues.”"
                        % (n, _about(cp["names"]), cp["pages"]))
            if y - 60 < BOTTOM:
                b.next()
                x0, x1, y = clue_page_start(False)
            c.setLineWidth(0.8)
            top = y + 10
            y = b.text_block(x0 + 10, x1 - 10, y - 14, text, font=SERIF_I, size=9.5, leading=12)
            c.setFont(SERIF_B, 9.5)
            c.drawString(x0 + 10, top - 12, "CHECKPOINT %s" % label)
            c.rect(x0, y + 4, x1 - x0, top - y - 4)
            y -= 16
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
    scenes = {**PLACES_INDOOR, **PLACES_OUTDOOR}
    position = {}                    # flat index -> (line on its page, place on that line), from 1
    lines_on_page = {}
    chapter_starts = {start: (i, place) for i, (place, start) in enumerate(reg.chapters)}
    for p, names in enumerate(reg.pages):
        x0, x1 = b.margins()
        y = H - TOP
        if p in chapter_starts:
            i, place = chapter_starts[p]
            c.setFont(SERIF, 9.5)
            c.drawCentredString(W / 2, y - 6, "CHAPTER %d" % (i + 1))
            c.setFont(SERIF_B, 17)
            c.drawCentredString(W / 2, y - 28, place)
            y = b.text_block(x0 + 12, x1 - 12, y - 50, scenes[place], font=SERIF_I, size=9.5, leading=12.5) - 12
        lines = _layout_lines(names, reg.cast, x1 - x0, size)
        k = 0
        for ln_no, line in enumerate(lines, 1):
            _draw_line(c, x0, x1, y, line, reg.cast, size, justify=ln_no < len(lines))
            for at in range(1, len(line) + 1):
                position[reg.page_start[p] + k] = (ln_no, at)
                k += 1
            y -= leading
        lines_on_page[p] = len(lines)
        if y + leading - size < BOTTOM:
            raise LayoutError("register page %d overflows; use fewer names per page" % reg.page_no(p))
        b.footer(reg.page_no(p))
        b.next()

    # --- Final deduction
    x0, x1 = b.margins()
    b.heading("The Final Deduction")
    y = H - TOP - 60
    for para in [
        "You should now have two names left. Only one of them is the killer.",
        "As the clock struck twelve, the Fairy Godmother saw a guest run down the palace stairs and "
        "lose a shoe on the last step. “The one I saw,” she tells the guards, “has the "
        "longer name of the two.”",
        "Count the letters in each name. The longer name is your killer.",
        "The killer is: ______________________________   on page ______",
        "Stuck? The hints come next. The solution is on the last pages of the book, upside down, behind a "
        "warning page.",
    ]:
        y = b.text_block(x0, x1, y, para) - 10
    b.next()

    # --- Hints: what each clue means, then where to look in this register
    def hint_page_start(first):
        x0, x1 = b.margins()
        b.heading("Hints" if first else "Hints (continued)")
        y = H - TOP - 44
        if first:
            y = b.text_block(x0, x1, y, "Read only the hint you need. A tells you what the clue means; B tells "
                             "you where to look.", font=SERIF_I, size=10, leading=13) - 8
        return x0, x1, y

    x0, x1, y = hint_page_start(True)
    for n, cl in enumerate(clues, 1):
        a_text = "A. " + cl.explain
        b_text = "B. " + _where_to_look(reg, cl, examples.get(cl.key, ""))
        need = 14 + 12 * (2 + (len(a_text) + len(b_text)) // 70)
        if y - need < BOTTOM:
            b.next()
            x0, x1, y = hint_page_start(False)
        c.setFont(SERIF_B, 10)
        c.drawString(x0, y, "Clue %d" % n)
        y = b.text_block(x0 + 10, x1, y - 13, a_text, size=9.5, leading=12) - 2
        y = b.text_block(x0 + 10, x1, y, b_text, size=9.5, leading=12) - 10
    b.next()

    # --- Notes, then a warning page, then the solution upside down on its back
    b.notes_page()
    if b.pdf_page % 2 == 0:            # the warning must be a right-hand page, the solution on its back
        b.notes_page()
    x0, x1 = b.margins()
    c.setFont(SERIF_B, 20)
    c.drawCentredString(W / 2, H / 2 + 30, "Stop!")
    b.text_block(x0 + 20, x1 - 20, H / 2, "The other side of this page tells you who killed Prince Charming. "
                 "Turn over only when you have your answer, or when you give up.", size=11, leading=15,
                 align="center")
    b.next()

    killer, pair = solution["killer_index"], solution["pair"]
    innocent = pair[0] if pair[1] == killer else pair[1]
    names = {"killer": reg.flat[killer], "innocent": reg.flat[innocent]}
    names["motive"] = rng.choice(MOTIVES).format(**names)
    c.saveState()
    c.translate(W, H)
    c.rotate(180)
    x0, x1 = OUTER, W - OUTER
    c.setFont(SERIF_B, 16)
    c.drawCentredString(W / 2, H - TOP - 20, "The Solution")
    y = H - TOP - 55
    for i, para in enumerate(ENDING):
        y = b.text_block(x0, x1, y, para.format(**names), font=SERIF_B if i == 0 else SERIF,
                         size=12 if i == 0 else 10.5, leading=16 if i == 0 else 14) - 8
    y -= 4
    for idx in (killer, innocent):
        p = reg.page_of[idx]
        ln, at = position[idx]
        total = lines_on_page[p]
        where = "line %d from the top" % ln if ln <= (total + 1) // 2 else "line %d from the bottom" % (total - ln + 1)
        y = b.text_block(x0, x1, y, "%s%s: page %d, %s, name %d on the line; %d letters." % (
            reg.flat[idx], " (the killer)" if idx == killer else "", reg.page_no(p), where, at,
            len(letters(reg.flat[idx]))), font=SERIF_I, size=9.5, leading=12)
    y = b.text_block(x0, x1, y - 6, "Names left after each clue: " + ", ".join(
        "%d: %s" % (k, format(cp["names"], ",")) for k, cp in enumerate(solution["checkpoints"], 1)) + ".",
        font=SERIF_I, size=9, leading=11.5)
    c.restoreState()
    b.next()
    b.notes_page()
    if (b.pdf_page - 1) % 2:               # an even page count, as print interiors expect
        c.setFont(SERIF, 1)
        c.drawString(0, 0, " ")
        b.next()
    c.save()
    return b.pdf_page - 1
