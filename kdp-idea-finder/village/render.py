"""Render one case as a 6 x 9 inch test PDF (needs reportlab).

Order: title, the story, how to play, the gate ledger page (chapters), the
clues, the check page, the ledger itself, then a Stop page with the solution
upside down on its back.
"""

import random

from reportlab.pdfgen import canvas

from whodunit.render import (BOTTOM, GAP, INNER, OUTER, SERIF, SERIF_B, SERIF_I, TOP, H, W, LayoutError,
                             _draw_line, _layout_lines)

from .case import CLUES, READINGS, RESERVED, WINDOW, Ledger, signature

REG_SIZE, REG_LEADING = 12, 16.5
TITLE = "The Ashcombe Raffle"
CASE = "Case One: The Summer Fête"

STORY = [
    "Every July, Ashcombe St Mary holds its Summer Fête on the green behind the church, and every July the "
    "same people win the same prizes. This year was different.",
    "At ten past four, when the brass band stopped for tea, Mrs Hester Greaves, chair of the fête committee for "
    "twenty-two years, was found sitting upright in a deckchair behind the cake stall, a slice of Victoria sponge "
    "untouched on her lap. Dr Moffat said it was her heart, until he noticed the smell of bitter almonds in her "
    "teacup.",
    "In her gloved hand was a raffle ticket: pink, number 1. The raffle tickets that year were blue.",
    "Detective Sergeant Ruth Ambrose of the county police closed the gate at half past four. Nobody had left. "
    "Every visitor had signed the gate ledger on the way in, first names only, as is the custom in Ashcombe, "
    "and every one of them was still on the green.",
    "{total} names. One of them poisoned Hester Greaves.",
    "Ruth spent the evening taking statements. The villagers had seen a great deal, as villagers do, and no two "
    "of them had seen the same thing. Their statements are your clues.",
    "She turned the pink ticket over. On the back, in neat capitals, someone had written: ONE OF FIVE.",
]

RULES = [
    ("Every name is one visitor.", "Names repeat. Each Rosa in the ledger is a different Rosa, and any of them "
     "could be the killer."),
    ("Letters.", "Only the letters A to Z count. The vowels are A, E, I, O and U. Y is never a vowel."),
    ("Reading order.", "Left to right, line by line, page by page, like a book. “Next to” and "
     "“within %d names” follow reading order and carry on across lines and pages." % WINDOW),
    ("Crossed-out names still count.", "When a clue asks you to count names or to find a group, count every "
     "printed name, including the ones you have already crossed out."),
    ("Standing together.", "Names one straight after another in reading order, in the order the clue gives. "
     "A group may run on to the next line."),
    ("Famous names.", "Some famous groups are hidden among the visitors, printed like everyone else. The clues "
     "tell you which ones to hunt for. Spotting the others is just for fun."),
    ("Any order.", "The clues work in any order. The hunt clues (1 to 4) save the most work, because they rule "
     "out long stretches of the ledger. Leave the letter clues (5 to 8) for the names that are left."),
    ("Check your answer.", "When one name is left, the check on the page after the clues tells you whether "
     "you are right, without giving the answer away."),
    ("Tools.", "A pencil, or an erasable highlighter. Ink bleeds through thin paper."),
]

ENDING = [
    "The killer is {killer}.",
    "When Ruth Ambrose read the name aloud in the tea tent, {killer} put down a cup of tea and said nothing at "
    "all. In {killer}'s coat pocket was a book of pink raffle tickets. Ticket 1 had been torn out. So had "
    "tickets 2, 3, 4 and 5.",
    "“I never had the others,” {killer} said at last. “The book came in the post, with ticket 1 "
    "already gone and a letter telling me what to do with it. I burned the letter. I was told to.”",
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
        right_hand = self.pdf_page % 2 == 1
        return (INNER, W - OUTER) if right_hand else (OUTER, W - INNER)

    def next(self):
        self.c.showPage()
        self.pdf_page += 1

    def to_right_hand(self):
        if self.pdf_page % 2 == 0:
            self.next()

    def para(self, x0, x1, y, text, font=SERIF, size=10.5, leading=14.5, align="left"):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        c, lines, line = self.c, [], ""
        for word in text.split(" "):
            trial = (line + " " + word).strip()
            if stringWidth(trial, font, size) <= x1 - x0:
                line = trial
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        c.setFont(font, size)
        for ln in lines:
            if align == "center":
                c.drawCentredString((x0 + x1) / 2, y, ln)
            else:
                c.drawString(x0, y, ln)
            y -= leading
        return y

    def lines(self, x0, x1, text, font=SERIF, size=10.5):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        n, line = 0, ""
        for word in text.split(" "):
            trial = (line + " " + word).strip()
            if stringWidth(trial, font, size) <= x1 - x0:
                line = trial
            else:
                n, line = n + 1, word
        return n + (1 if line else 0)

    def box(self, x, y, size=8):
        self.c.setLineWidth(0.8)
        self.c.rect(x, y - 1, size, size)

    def heading(self, text, size=17):
        self.c.setFont(SERIF_B, size)
        self.c.drawCentredString(W / 2, H - TOP - 18, text)
        return H - TOP - 52

    def footer(self, n):
        self.c.setFont(SERIF, 9)
        self.c.drawCentredString(W / 2, BOTTOM / 2, str(n))


def _clean(name, killer_name):
    """A name that is safe to use as an example: plain, not a landmark, not the killer."""
    return name not in RESERVED and name != killer_name


def _examples(led, killer_name, rng):
    """For each letter clue, one name that stays and one that goes under every reading."""
    out = {}
    names = sorted({n for n in led.flat if _clean(n, killer_name)})
    for c in CLUES:
        if c.kind != "letter":
            continue
        verdict = {}
        for n in names:
            one = Ledger([[n]], [("", 0)]).index()
            verdict[n] = {c.test(one, r)[0] for r in READINGS}
        stay = [n for n, v in verdict.items() if v == {True}]
        go = [n for n, v in verdict.items() if v == {False}]
        out[c.key] = (rng.choice(stay), rng.choice(go))
    return out


def render(case, path, seed=1, ledger_start=None):
    led, killer = case.ledger, case.killer
    killer_name = led.flat[killer]
    rng = random.Random(seed)
    b = Book(path)
    c = b.c

    # --- Title
    c.setFont(SERIF, 10)
    c.drawCentredString(W / 2, H - 1.6 * 72, "TEST COPY · ONE CASE OF FIVE")
    c.setFont(SERIF_B, 26)
    c.drawCentredString(W / 2, H / 2 + 40, TITLE)
    c.setFont(SERIF, 15)
    c.drawCentredString(W / 2, H / 2, CASE)
    c.setFont(SERIF_I, 11)
    c.drawCentredString(W / 2, H / 2 - 40, "%s suspects · 8 clues · 1 killer" % format(len(led.flat), ","))
    b.next()
    b.next()

    # --- Story
    x0, x1 = b.margins()
    y = b.heading("Ashcombe St Mary")
    for k, p in enumerate(STORY):
        text = p.format(total=format(len(led.flat), ","))
        y = b.para(x0, x1, y, text, font=SERIF_B if text.startswith(format(len(led.flat), ",")) else SERIF) - 9
    b.next()

    # --- How to play
    x0, x1 = b.margins()
    y = b.heading("How to Play")
    y = b.para(x0, x1, y, "Cross out every visitor a clue rules out. When you have used all eight clues, one "
               "name will be left: the killer.", font=SERIF_I, size=10.5) - 10
    for head, text in RULES:
        c.setFont(SERIF_B, 10)
        c.drawString(x0, y, head)
        y = b.para(x0 + 10, x1, y - 13, text, size=9.8, leading=13) - 7
    b.next()

    # --- The gate ledger
    x0, x1 = b.margins()
    y = b.heading("The Gate Ledger")
    y = b.para(x0, x1, y, "The ledger was kept by place. Whoever was at the Tea Tent when the bell rang signed "
               "the Tea Tent pages, and so on round the green. Each place is a chapter.", size=10.5) - 14
    ledger_start = ledger_start or 9
    for k, (place, first) in enumerate(led.chapters):
        last = (led.chapters[k + 1][1] if k + 1 < len(led.chapters) else len(led.pages)) - 1
        c.setFont(SERIF_B, 11)
        c.drawString(x0 + 20, y, "Chapter %d   %s" % (k + 1, place))
        c.setFont(SERIF, 11)
        c.drawRightString(x1 - 20, y, "pages %d\u2013%d" % (ledger_start + first, ledger_start + last))
        y -= 20
    y = b.para(x0, x1, y - 14, "The chapters run in the order the green is laid out, from the church gate to "
               "the bowling green. Page numbers carry on from one chapter to the next.", size=10) - 4
    b.next()

    # --- Clues
    examples = _examples(led, killer_name, rng)
    x0, x1 = b.margins()
    y = b.heading("The Statements")
    for n, cl in enumerate(CLUES, 1):
        ex = ""
        if cl.key in examples:
            stay, go = examples[cl.key]
            ex = " For example: %s stays, %s goes." % (stay, go)
        body = cl.example + ex
        need = (13 + 12.8 * b.lines(x0 + 16, x1, cl.witness, SERIF_I, 9.8) + 3
                + 13 * b.lines(x0 + 16, x1, "Rule: " + cl.rule, SERIF_B, 10) + 2
                + 12.3 * b.lines(x0 + 16, x1, body, SERIF, 9.5) + 8)
        if y - need < BOTTOM:
            b.next()
            x0, x1 = b.margins()
            y = b.heading("The Statements (continued)")
        b.box(x0, y)
        c.setFont(SERIF_B, 11)
        c.drawString(x0 + 14, y, "Clue %d" % n)
        y = b.para(x0 + 16, x1, y - 14, cl.witness, font=SERIF_I, size=9.8, leading=12.8) - 3
        y = b.para(x0 + 16, x1, y, "Rule: " + cl.rule, font=SERIF_B, size=10, leading=13) - 2
        y = b.para(x0 + 16, x1, y, body, size=9.5, leading=12.3) - 8
    b.next()

    # --- Check page
    x0, x1 = b.margins()
    y = b.heading("Your Answer")
    y = b.para(x0, x1, y, "The killer is:  ______________________   on page  ______", size=11.5) - 22
    n_letters, total = case.check
    c.setFont(SERIF_B, 12)
    c.drawString(x0, y, "The check")
    y = b.para(x0, x1, y - 16, "The killer's name has %d letters, and its letters add up to %d." % (n_letters, total),
               font=SERIF_B, size=11, leading=15) - 4
    y = b.para(x0, x1, y, "Give each letter its place in the alphabet, A = 1, B = 2 and so on to Z = 26, and add "
               "them up. For example, ROSA is 18 + 15 + 19 + 1 = 53.", size=10) - 10
    y = b.para(x0, x1, y, "Many names in the ledger add up to %d, so the check gives nothing away. But only the "
               "killer survives all eight clues and matches it." % total, size=10) - 10
    y = b.para(x0, x1, y, "If your name doesn't match, one clue went astray. The usual slips:", size=10) - 4
    for slip in ["Y is never a vowel.",
                 "The sisters' own two pages are not between them.",
                 "Clue 3 keeps the pages either side of Bonnie and Clyde too.",
                 "Crossed-out names still count when you count %d names from a Musketeer." % WINDOW]:
        y = b.para(x0 + 12, x1, y, "•  " + slip, size=10, leading=13.5) - 2
    b.next()

    # --- Ledger
    b.to_right_hand()
    first_pdf = b.pdf_page
    led.first_page_no = first_pdf
    position, lines_on_page = {}, {}
    starts = {s: (k, place) for k, (place, s) in enumerate(led.chapters)}
    start = 0
    for p, names in enumerate(led.pages):
        x0, x1 = b.margins()
        y = H - TOP
        c.setFont(SERIF, 8)
        c.drawCentredString(W / 2, H - TOP / 2, "THE GATE LEDGER · %s" % led.chapters[led.chapter_of_page[p]][0].upper())
        if p in starts:
            k, place = starts[p]
            c.setFont(SERIF, 9.5)
            c.drawCentredString(W / 2, y - 4, "CHAPTER %d" % (k + 1))
            c.setFont(SERIF_B, 17)
            c.drawCentredString(W / 2, y - 25, place)
            y -= 50
        else:
            y -= 8
        lines = _layout_lines(names, set(), x1 - x0, REG_SIZE)
        for ln_no, line in enumerate(lines, 1):
            _draw_line(c, x0, x1, y, line, set(), REG_SIZE, justify=ln_no < len(lines))
            for at in range(1, len(line) + 1):
                position[start] = (ln_no, at)
                start += 1
            y -= REG_LEADING
        lines_on_page[p] = len(lines)
        if y + REG_LEADING - REG_SIZE < BOTTOM:
            raise LayoutError("ledger page %d overflows" % led.page_no(p))
        b.footer(led.page_no(p))
        b.next()

    # --- Stop page, solution on its back
    b.to_right_hand()
    x0, x1 = b.margins()
    c.setFont(SERIF_B, 22)
    c.drawCentredString(W / 2, H / 2 + 30, "Stop!")
    b.para(x0 + 20, x1 - 20, H / 2, "The other side of this page names the killer. Turn over only when the check "
           "says you are right, or when you give up.", size=11, leading=15, align="center")
    b.next()
    c.saveState()
    c.translate(W, H)
    c.rotate(180)
    x0, x1 = OUTER, W - OUTER
    c.setFont(SERIF_B, 16)
    c.drawCentredString(W / 2, H - TOP - 18, "The Solution")
    y = H - TOP - 52
    for k, p in enumerate(ENDING):
        y = b.para(x0, x1, y, p.format(killer=killer_name), font=SERIF_B if k == 0 else SERIF,
                   size=12.5 if k == 0 else 10.5) - 8
    p = led.page_of[killer]
    ln, at = position[killer]
    y = b.para(x0, x1, y - 4, "%s is on page %d, line %d, name %d on the line, in the chapter %s." % (
        killer_name, led.page_no(p), ln, at, led.chapters[led.chapter_of_page[p]][0]), font=SERIF_I, size=10) - 4
    hunt_left = case.stats["after_hunt"]
    b.para(x0, x1, y, "After the four hunt clues, %d names are left; the letter clues bring them down to one." %
           hunt_left, font=SERIF_I, size=10)
    c.restoreState()
    b.next()

    c.save()
    return dict(first_ledger_page=first_pdf, position=position, pages=b.pdf_page - 1)
