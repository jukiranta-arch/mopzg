"""Join the back cover, a spine and the front cover into KDP's one-piece paperback cover PDF.

    python -m village.make_cover OUT.pdf [PREVIEW.png]

The back and front are the finished pictures in books/juniper-falls/art (cover_back.png, cover_front.png).
The spine is drawn here:
- the background blends the purple at the back's right edge into the purple at the front's left edge, row by
  row, so both folds join without a visible seam;
- the title and author are vector type, reading top to bottom (the US convention), in Playfair Display
  (Black for the title, condensed to the front title's proportions; Bold, letterspaced, for the author).

KDP's rules for a 6 x 9 in paperback on white paper (kdp.amazon.com cover calculator):
- spine width = pages x 0.002252 in; full size = 0.125 + 6 + spine + 6 + 0.125 in wide, 9.25 in tall;
- spine text keeps 0.0625 in from each fold; back and front text keeps 0.125 in inside the trim;
- the barcode goes 2 x 1.2 in at the back's lower right, 0.25 in from the spine fold and the bottom trim.

PREVIEW.png draws those lines over the cover: red = trim, blue = folds, green = text safe area, white = barcode.
"""

import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from . import story
from .design import FONT_DIR, DISPLAY_B

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "books", "juniper-falls")
ART = os.path.join(BOOK, "art")

pdfmetrics.registerFont(TTFont("Display-Black", os.path.join(FONT_DIR, "PlayfairDisplay-Black.ttf")))
TITLE_FONT, AUTHOR_FONT = "Display-Black", DISPLAY_B

TRIM_W, TRIM_H, BLEED = 6.0, 9.0, 0.125
PAPER = 0.002252                       # inches per page, white paper
FOLD_CLEAR, SAFE = 0.0625, 0.125
BARCODE_W, BARCODE_H, BARCODE_GAP = 2.0, 1.2, 0.25

# Sampled from the front cover's own lettering.
CREAM = (252 / 255, 236 / 255, 201 / 255)
GOLD = (231 / 255, 178 / 255, 98 / 255)
AUTHOR_CREAM = (249 / 255, 238 / 255, 217 / 255)

TITLE_CAP = 0.140                      # inches; the spine leaves 0.32 - 2 x 0.0625 = 0.195 in
AUTHOR_CAP = 0.095
TITLE_SQUEEZE = 84                     # % horizontal scale: Playfair Black is wider than the front's title
AUTHOR_TRACK = 0.35                    # letterspacing, as a fraction of the size, like the front's author line
END_GAP = 0.60                         # inches from the top and bottom trim to the title and the author


def spine_width(pages):
    return pages * PAPER


def panel(path, w_in, h_in, centre_in):
    """The picture as one panel, w_in x h_in (bleed included), with the picture's centre centre_in from the
    panel's left edge: the centre of the trimmed cover, not of the panel. The bleed is on the outer edge only,
    so centring on the whole panel would leave the artwork 1/16 in off-centre once the bleed is cut. Where the
    picture doesn't reach the panel's edge, the strip is filled by mirroring the picture's own edge (it lies
    in the bleed, which is cut off); where it overhangs the fold, it is cropped."""
    im = Image.open(path).convert("RGB")
    dpi = im.height / h_in
    width = round(w_in * dpi)
    left = round(centre_in * dpi - im.width / 2)            # where the picture's left edge lands in the panel
    out = Image.new("RGB", (width, im.height))
    out.paste(im, (left, 0))
    if left > 0:                                            # gap on the left: mirror the picture's left edge
        strip = im.crop((0, 0, left, im.height)).transpose(Image.FLIP_LEFT_RIGHT)
        out.paste(strip, (0, 0))
    gap = width - (left + im.width)
    if gap > 0:                                             # gap on the right: mirror its right edge
        strip = im.crop((im.width - gap, 0, im.width, im.height)).transpose(Image.FLIP_LEFT_RIGHT)
        out.paste(strip, (width - gap, 0))
    if max(left, gap) > 0.06 * dpi:
        raise SystemExit("%s is too narrow: %.3f in of the bleed would be mirrored" % (path, max(left, gap) / dpi))
    return out


def edge_profile(im, side, band=32, skip=8, window=0.12):
    """The purple along one edge, row by row: a median over the edge band, ignoring objects that cross it,
    then smoothed over a tall window so a tag or a pencil at the edge doesn't show."""
    a = np.asarray(im, dtype=float)
    cols = a[:, skip:skip + band] if side == "left" else a[:, -skip - band:-skip]
    dark = cols.mean(axis=2) < 70
    rows = np.array([np.median(c[d], axis=0) if d.sum() > band // 4 else [np.nan] * 3
                     for c, d in zip(cols, dark)])
    for k in range(3):                 # fill rows where an object covered the whole band
        good = ~np.isnan(rows[:, k])
        rows[:, k] = np.interp(np.arange(len(rows)), np.flatnonzero(good), rows[good, k])
    n = max(3, int(len(rows) * window)) | 1
    pad = np.pad(rows, ((n // 2, n // 2), (0, 0)), mode="edge")
    kernel = np.ones(n) / n
    return np.stack([np.convolve(pad[:, k], kernel, mode="valid") for k in range(3)], axis=1)


def spine_picture(back, front, width_px, height_px, seed=7):
    left = edge_profile(back, "right")
    right = edge_profile(front, "left")
    rows = np.linspace(0, len(left) - 1, height_px).round().astype(int)
    t = np.linspace(0, 1, width_px)[None, :, None]
    base = left[rows][:, None, :] * (1 - t) + right[rows][:, None, :] * t
    grain = np.random.default_rng(seed).normal(0, 2.4, (height_px, width_px, 1))
    return Image.fromarray(np.clip(base + grain, 0, 255).astype(np.uint8))


def draw_spine_text(c, x0, spine_w, height):
    """Title from the top, author from the bottom, both reading top to bottom, centred across the spine."""
    title_size = TITLE_CAP / 0.708 * 72             # Playfair's cap height is 0.708 of the size
    author_size = AUTHOR_CAP / 0.708 * 72
    cx = (x0 + spine_w / 2) * inch
    c.saveState()
    c.translate(cx, height * inch)
    c.rotate(-90)                                   # local x runs down the spine, local y toward the front
    # Title, starting END_GAP below the top trim.
    words = story.TITLE.rsplit(" ", 1)              # "Who Sent the" + "Killers?"
    first, last = words[0].upper() + " ", words[1].upper()
    t = c.beginText()
    t.setFont(TITLE_FONT, title_size)
    t.setHorizScale(TITLE_SQUEEZE)
    t.setTextOrigin((BLEED + END_GAP) * inch, -TITLE_CAP * inch / 2)
    t.setFillColorRGB(*CREAM)
    t.textOut(first)
    t.setFillColorRGB(*GOLD)
    t.textOut(last)
    c.drawText(t)
    title_len = (stringWidth(first + last, TITLE_FONT, title_size) * TITLE_SQUEEZE / 100) / inch
    # Author, ending END_GAP above the bottom trim.
    author = story.AUTHOR.upper()
    track = author_size * AUTHOR_TRACK
    author_len = (stringWidth(author, AUTHOR_FONT, author_size) + track * (len(author) - 1)) / inch
    t = c.beginText()
    t.setFont(AUTHOR_FONT, author_size)
    t.setCharSpace(track)
    t.setTextOrigin((height - BLEED - END_GAP - author_len) * inch, -AUTHOR_CAP * inch / 2)
    t.setFillColorRGB(*AUTHOR_CREAM)
    t.textOut(author)
    c.drawText(t)
    c.restoreState()
    return title_len, author_len


def build(out, pages, preview=None):
    spine = spine_width(pages)
    panel_w, height = BLEED + TRIM_W, BLEED + TRIM_H + BLEED
    full_w = panel_w + spine + panel_w
    # Centre each picture on its trimmed panel: the back's bleed is on its left, the front's on its right.
    back = panel(os.path.join(ART, "cover_back.png"), panel_w, height, BLEED + TRIM_W / 2)
    front = panel(os.path.join(ART, "cover_front.png"), panel_w, height, TRIM_W / 2)
    dpi = min(back.height, front.height) / height
    spine_px = (max(8, round(spine * dpi)), round(height * dpi))
    spine_im = spine_picture(back, front, *spine_px)

    c = canvas.Canvas(out, pagesize=(full_w * inch, height * inch), initialFontName=TITLE_FONT)
    c.setTitle(story.TITLE)
    c.setAuthor(story.AUTHOR)
    c.setSubject("Paperback cover, %d pages, 6 x 9 in, white paper, spine %.4f in" % (pages, spine))
    c.drawImage(ImageReader(back), 0, 0, panel_w * inch, height * inch)
    c.drawImage(ImageReader(spine_im), panel_w * inch, 0, spine * inch, height * inch)
    c.drawImage(ImageReader(front), (panel_w + spine) * inch, 0, panel_w * inch, height * inch)
    title_len, author_len = draw_spine_text(c, panel_w, spine, height)
    c.showPage()
    c.save()

    room = height - 2 * (BLEED + END_GAP)
    if title_len + author_len + 0.5 > room:
        raise SystemExit("spine: title (%.2f in) and author (%.2f in) don't fit in %.2f in" % (
            title_len, author_len, room))
    if TITLE_CAP > spine - 2 * FOLD_CLEAR:
        raise SystemExit("spine: title cap height %.3f in > %.3f in between the fold clearances" % (
            TITLE_CAP, spine - 2 * FOLD_CLEAR))
    info = {"pages": pages, "spine": spine, "size": (full_w, height), "dpi": dpi,
            "title_len": title_len, "author_len": author_len}
    if preview:
        draw_preview(out, preview, info)
    return info


def draw_preview(pdf, png, info, dpi=110):
    import pymupdf
    page = pymupdf.open(pdf)[0]
    pm = page.get_pixmap(dpi=dpi)
    im = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
    d = ImageDraw.Draw(im)
    full_w, height = info["size"]
    panel_w, spine = BLEED + TRIM_W, info["spine"]

    def X(x):
        return x * dpi

    def Y(y):                                       # y in inches from the bottom
        return (height - y) * dpi

    def box(x0, y0, x1, y1, colour, width=2):
        d.rectangle([X(x0), Y(y1), X(x1), Y(y0)], outline=colour, width=width)

    box(BLEED, BLEED, full_w - BLEED, height - BLEED, (255, 0, 0))                          # trim
    for x in (panel_w, panel_w + spine):                                                    # folds
        d.line([X(x), 0, X(x), im.height], fill=(60, 140, 255), width=2)
    box(BLEED + SAFE, BLEED + SAFE, panel_w - SAFE, height - BLEED - SAFE, (0, 220, 0))     # back safe
    box(panel_w + spine + SAFE, BLEED + SAFE, full_w - BLEED - SAFE, height - BLEED - SAFE, (0, 220, 0))
    box(panel_w + FOLD_CLEAR, BLEED + SAFE, panel_w + spine - FOLD_CLEAR, height - BLEED - SAFE, (0, 220, 0), 1)
    bx1, by0 = panel_w - BARCODE_GAP, BLEED + BARCODE_GAP                                  # barcode
    box(bx1 - BARCODE_W, by0, bx1, by0 + BARCODE_H, (255, 255, 255), 3)
    im.save(png)


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    import pymupdf
    pages = pymupdf.open(os.path.join(BOOK, "interior.pdf")).page_count
    info = build(argv[0], pages, argv[1] if len(argv) > 1 else None)
    w, h = info["size"]
    print("%d pages: spine %.4f in; cover %.4f x %.3f in; pictures at %d DPI; spine title %.2f in, author %.2f in"
          % (info["pages"], info["spine"], w, h, info["dpi"], info["title_len"], info["author_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
