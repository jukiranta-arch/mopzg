"""The look of the book: fonts, page furniture, and the building blocks every page is drawn with.

Taken from the winners' samples (briefs/2026-10-02_visual-research.md):

- names set like The Killer Isn't Alice: a Charter-style book face (Charis SIL), rows filled edge to edge with
  the spare space spread evenly, one size and leading on every list page;
- a quiet running head at the top of each page, as Alice, Autumn and Never Checked In have;
- headings in a display serif (Playfair Display), the rule of each clue in a light grey box, as Mr Darcy and
  The Autumn Killer do;
- black-ink illustrations at the start of each case, as The Killer Was On The Guest List does. Each picture is
  a file in the art folder; a missing one is drawn as a marked placeholder, and a final build refuses to run
  with any placeholder left.

Both font families are under the SIL Open Font License (village/fonts/*-OFL.txt) and are embedded in the PDF.
"""

import functools
import os

from PIL import Image
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
# The checker tells bold and italic apart by these names, so keep "Bold" and "Italic" in them.
_FILES = {"Body": "CharisSIL-Regular", "Body-Bold": "CharisSIL-Bold", "Body-Italic": "CharisSIL-Italic",
          "Body-BoldItalic": "CharisSIL-BoldItalic", "Display": "PlayfairDisplay-Regular",
          "Display-Bold": "PlayfairDisplay-Bold", "Display-Italic": "PlayfairDisplay-Italic"}
for _name, _file in _FILES.items():
    pdfmetrics.registerFont(TTFont(_name, os.path.join(FONT_DIR, _file + ".ttf")))
BODY, BODY_B, BODY_I, BODY_BI = "Body", "Body-Bold", "Body-Italic", "Body-BoldItalic"
DISPLAY, DISPLAY_B, DISPLAY_I = "Display", "Display-Bold", "Display-Italic"

W, H = 6 * inch, 9 * inch
# A generous inner margin: names that "run into the fold" are a complaint in competitors' reviews.
INNER, OUTER = 0.80 * inch, 0.55 * inch
TOP, BOTTOM = 0.82 * inch, 0.72 * inch          # the text block; the running head and folio sit outside it
HEAD_Y, FOLIO_Y = H - 0.48 * inch, 0.42 * inch

TEXT_SIZE, TEXT_LEADING = 10.5, 14.5
NAME_SIZE, NAME_LEADING = 10.0, 14.0             # list pages; the checker reads names at exactly this size
NAME_LEADING_MAX = 15.8                          # a list page opens its leading up to this to fill the page
FOLIO_SIZE = 9.5                                 # list page numbers; the checker reads them at this size
CHAPTER_SIZE = 19                                # chapter names on list pages
SOLUTION_HEAD_SIZE = 21                          # the headings of the upside-down solution pages
DOT = "·"
CAP_HEIGHT = 0.671                               # Charis SIL's capitals, in ems
DOT_GREY = 0.40
BOX_GREY = 0.88                                  # 12% ink: KDP asks for at least 10% for a grey fill to print
RULE_GREY = 0.55
HEAD_GREY = 0.30

ART_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "books", "juniper-falls", "art")
MIN_DPI = 300


class LayoutError(RuntimeError):
    """A list page overflows: the generator tries another seed."""


class TextOverflow(RuntimeError):
    """A page of fixed text overflows: the words or the design must change, not the seed."""


def width(text, font, size):
    return stringWidth(text, font, size)


def wrap(text, w, font, size, first_w=None, first_n=0):
    """Split text into lines no wider than w; the first first_n lines may be narrower (first_w)."""
    lines, line = [], ""
    for word in text.split(" "):
        limit = first_w if len(lines) < first_n else w
        trial = (line + " " + word).strip()
        if stringWidth(trial, font, size) <= limit:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + ([line] if line else [])


# ---------------------------------------------------------------- name rows

def balance_rows(names, w, size=NAME_SIZE, font=BODY):
    """Break a page's names into the fewest rows that fit, then choose the breaks that make the spare space
    in each row as even as possible (the last row is set loose). Returns a list of rows."""
    ws = [stringWidth(n, font, size) for n in names]
    sep = stringWidth(DOT, font, size) + 2 * name_gap(size, font)
    pre = [0.0]
    for x in ws:
        pre.append(pre[-1] + x + sep)

    def need(i, j):
        return pre[j] - pre[i]

    rows, i = 0, 0
    while i < len(ws):
        j = i + 1
        while j < len(ws) and need(i, j + 1) <= w:
            j += 1
        rows, i = rows + 1, j

    @functools.lru_cache(maxsize=None)
    def best(i, r):
        if i == len(ws):
            return (0.0, ()) if r == 0 else (float("inf"), ())
        if r == 0:
            return float("inf"), ()
        out = (float("inf"), ())
        j = i + 1
        while j <= len(ws) and need(i, j) <= w:
            cost = 0.0 if j == len(ws) else ((w - need(i, j)) / (j - i)) ** 2
            c, rest = best(j, r - 1)
            if c + cost < out[0]:
                out = (c + cost, (j,) + rest)
            j += 1
        return out

    import sys
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 4 * len(ws) + 100))
    cuts = best(0, rows)[1]
    out, i = [], 0
    for j in cuts:
        out.append(names[i:j])
        i = j
    return out


def name_gap(size=NAME_SIZE, font=BODY):
    return stringWidth(" ", font, size) * 1.15


def draw_name_row(c, x0, x1, y, row, last, size=NAME_SIZE, font=BODY):
    """Names with a grey dot after each. A full row is justified: its first name starts at the left margin and
    its last dot ends exactly at the right one, and the spare space goes to the gaps between names, around the
    dots, never inside a name. The last row of a page is set loose."""
    gap = name_gap(size, font)
    ws = [stringWidth(n, font, size) for n in row]
    dot = stringWidth(DOT, font, size)
    between = len(row) - 1
    fixed = sum(ws) + len(row) * dot + (2 * between + 1) * gap
    extra = 0 if last or not between else ((x1 - x0) - fixed) / between
    x = x0
    for k, (n, wd) in enumerate(zip(row, ws)):
        c.setFont(font, size)
        c.setFillGray(0)
        c.drawString(x, y, n)
        x += wd + gap + (extra / 2 if k < between else 0)
        c.setFillGray(DOT_GREY)
        if k == between and not last and between:
            c.drawRightString(x1, y, DOT)
        else:
            c.drawString(x, y, DOT)
        x += dot + gap + extra / 2
    c.setFillGray(0)


# ---------------------------------------------------------------- pictures

class Art:
    """Pictures from the art folder, made ready for print: flattened onto white, greyscale, and checked for
    300 DPI at the size printed. Missing pictures are drawn as placeholders and listed."""

    def __init__(self, folder=ART_DIR, cache=None):
        self.folder = folder
        self.cache = cache or os.path.join(folder, ".print")
        self.used, self.missing, self.low = [], [], []

    def path(self, key):
        for ext in (".png", ".jpg", ".jpeg", ".webp"):
            p = os.path.join(self.folder, key + ext)
            if os.path.exists(p):
                return p
        return None

    def prepared(self, key, src):
        os.makedirs(self.cache, exist_ok=True)
        out = os.path.join(self.cache, key + ".png")
        if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(src):
            im = Image.open(src)
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGBA")
                bg = Image.new("RGBA", im.size, "white")
                bg.alpha_composite(im)
                im = bg
            im = im.convert("L")
            # Trim the white margin an image generator leaves, keeping a little air, so the drawing fills its box
            ink = im.point(lambda v: 255 if v < 235 else 0).getbbox()
            if ink:
                pad = max(4, int(0.02 * max(im.size)))
                im = im.crop((max(0, ink[0] - pad), max(0, ink[1] - pad),
                              min(im.width, ink[2] + pad), min(im.height, ink[3] + pad)))
            im.save(out)
        return out

    def size(self, key, src):
        """The pixel size of the picture as printed: after the white margin is trimmed."""
        return Image.open(self.prepared(key, src)).size

    def draw(self, c, key, x, y, w, h, caption=""):
        """Fit picture `key` inside the box (x, y is the bottom left), centred; returns the box it used."""
        src = self.path(key)
        if not src:
            self.missing.append(key)
            c.saveState()
            c.setStrokeGray(0.6)
            c.setDash(3, 3)
            c.setLineWidth(0.6)
            c.rect(x, y, w, h)
            c.setFillGray(0.45)
            c.setFont(BODY_I, 9)
            c.drawCentredString(x + w / 2, y + h / 2 + 4, "Illustration: %s" % key)
            if caption:
                c.drawCentredString(x + w / 2, y + h / 2 - 9, caption)
            c.restoreState()
            return x, y, w, h
        pw, ph = self.size(key, src)
        scale = min(w / pw, h / ph)
        dw, dh = pw * scale, ph * scale
        dpi = pw / (dw / inch)
        self.used.append((key, pw, ph, dw / inch, dh / inch, dpi))
        if dpi < MIN_DPI:
            self.low.append((key, round(dpi)))
        c.drawImage(self.prepared(key, src), x + (w - dw) / 2, y + (h - dh) / 2, dw, dh)
        return x + (w - dw) / 2, y + (h - dh) / 2, dw, dh


# ---------------------------------------------------------------- small pieces

def tracked(c, text, x, y, font, size, track=1.6, align="center", grey=0):
    """Letter-spaced text for running heads and labels, drawn with the PDF's own character spacing so the
    words still read (and search) as words."""
    w = stringWidth(text, font, size) + track * (len(text) - 1)
    x0 = {"center": x - w / 2, "right": x - w, "left": x}[align]
    t = c.beginText(x0, y)
    t.setFont(font, size)
    t.setCharSpace(track)
    t.setFillGray(grey)
    t.textOut(text)
    t.setCharSpace(0)               # PDF keeps character spacing after the text block ends: reset it
    c.drawText(t)
    c.setFillGray(0)
    return w


def ornament(c, cx, y, art=None, w=90):
    """A divider under headings: the juniper sprig if it has been drawn, else a fine rule with a diamond."""
    if art and art.path("ornament"):
        art.draw(c, "ornament", cx - 0.45 * inch, y - 0.16 * inch, 0.9 * inch, 0.32 * inch)
        return
    c.saveState()
    c.setStrokeGray(RULE_GREY)
    c.setLineWidth(0.5)
    c.line(cx - w / 2, y, cx - 5, y)
    c.line(cx + 5, y, cx + w / 2, y)
    c.setFillGray(RULE_GREY)
    p = c.beginPath()
    p.moveTo(cx, y + 2.6)
    p.lineTo(cx + 2.6, y)
    p.lineTo(cx, y - 2.6)
    p.lineTo(cx - 2.6, y)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()
