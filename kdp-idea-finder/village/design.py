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
# A two-ink picture is re-cut at INK_UPSCALE times its size, so its edges print at twice the source resolution:
# 200 DPI of source detail is enough for paper cut-outs (KDP itself sees the enlarged image, well over 300).
MIN_DPI_INKED = 200
# Pictures lighter than this average grey (0 black, 255 white) have their mid-tones darkened to it, so a
# washed-out drawing matches the others; whites stay white and blacks stay black. Darker ones are left alone:
# printing darkens mid-greys a little anyway.
TONE_TARGET = 140
PREP_VERSION = 4                                 # bump when the preparation changes, to rebuild the cache
# Flat inks: None keeps a picture's own tones; 2 snaps it to black and white (linocut, silhouette); 3 to black, one
# grey and white (screen-printed poster). Set once the picture style is chosen.
ART_INKS = 2                                     # cut-paper silhouette: black and white
GREY_INK = 165                                   # the poster's grey: about 35% ink, well above KDP's 10% minimum


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
        out = os.path.join(self.cache, "%s.v%d.png" % (key, PREP_VERSION))
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
            im = flatten_inks(im, ART_INKS) if ART_INKS else even_tone(im)
            im.save(out)
        return out

    def size(self, key, src):
        """The picture's own pixel size after the white margin is trimmed (before any enlargement for flat inks:
        enlarging adds no detail, so it must not count towards the DPI)."""
        w, h = Image.open(self.prepared(key, src)).size
        k = INK_UPSCALE if ART_INKS else 1
        return w // k, h // k

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
        if dpi < (MIN_DPI_INKED if ART_INKS == 2 else MIN_DPI):
            self.low.append((key, round(dpi)))
        c.drawImage(self.prepared(key, src), x + (w - dw) / 2, y + (h - dh) / 2, dw, dh)
        return x + (w - dw) / 2, y + (h - dh) / 2, dw, dh


def ink_thresholds(im, n):
    """The n-1 grey levels that best split a picture's tones into n groups (Otsu's method)."""
    hist = im.histogram()
    total = sum(hist)
    cum, cum_mean = [0] * 257, [0.0] * 257
    for v in range(256):
        cum[v + 1] = cum[v] + hist[v]
        cum_mean[v + 1] = cum_mean[v] + v * hist[v]

    def score(a, b):   # between-class variance contribution of tones a..b-1
        w = cum[b] - cum[a]
        return 0.0 if not w else (cum_mean[b] - cum_mean[a]) ** 2 / w

    if n == 2:
        return [max(range(1, 256), key=lambda t: score(0, t) + score(t, 256))]
    best, cuts = -1.0, None
    for t1 in range(1, 255, 2):
        for t2 in range(t1 + 2, 256, 2):
            v = score(0, t1) + score(t1, t2) + score(t2, 256)
            if v > best:
                best, cuts = v, [t1, t2]
    return cuts


INK_UPSCALE = 2   # flat inks are cut at twice the picture's resolution, so the edges stay smooth, not stepped


def flatten_inks(im, n):
    """Snap a greyscale picture to n flat inks (2: black and white; 3: black, GREY_INK and white), with the speckle
    left by a generator's fine texture cleaned away. The result is INK_UPSCALE times larger, so the hard edges
    between inks are finer than the printer can show."""
    from PIL import ImageFilter
    im = im.resize((im.width * INK_UPSCALE, im.height * INK_UPSCALE), Image.LANCZOS)
    smooth = im.filter(ImageFilter.GaussianBlur(0.8 * INK_UPSCALE))
    cuts = ink_thresholds(smooth, n)
    inks = [0, 255] if n == 2 else [0, GREY_INK, 255]
    lut = [inks[sum(v >= c for c in cuts)] for v in range(256)]
    return smooth.point(lut).filter(ImageFilter.ModeFilter(3))


def even_tone(im, target=TONE_TARGET):
    """Darken the mid-tones of a light greyscale picture until its average grey reaches the target."""
    from PIL import ImageStat
    if ImageStat.Stat(im).mean[0] <= target:
        return im
    lo, hi = 1.0, 3.0
    for _ in range(20):
        g = (lo + hi) / 2
        mean = ImageStat.Stat(im.point(lambda v, g=g: 255 * (v / 255) ** g)).mean[0]
        lo, hi = (g, hi) if mean > target else (lo, g)
    return im.point(lambda v, g=hi: round(255 * (v / 255) ** g))


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


SPRIG_W = 22                                     # the sprig between the divider's lines, about the diamond's size


def ornament(c, cx, y, art=None, w=90):
    """A divider under headings: two fine rules with the small juniper sprig between them (a diamond until the
    sprig has been drawn)."""
    c.saveState()
    sprig = bool(art and art.path("ornament"))
    gap = SPRIG_W / 2 + 4 if sprig else 5
    c.setStrokeGray(RULE_GREY)
    c.setLineWidth(0.5)
    c.line(cx - w / 2, y, cx - gap, y)
    c.line(cx + gap, y, cx + w / 2, y)
    if sprig:
        art.draw(c, "ornament", cx - SPRIG_W / 2, y - SPRIG_W / 2, SPRIG_W, SPRIG_W)
    else:
        c.setFillGray(RULE_GREY)
        p = c.beginPath()
        p.moveTo(cx, y + 2.6)
        p.lineTo(cx + 2.6, y)
        p.lineTo(cx, y - 2.6)
        p.lineTo(cx - 2.6, y)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
    c.restoreState()
