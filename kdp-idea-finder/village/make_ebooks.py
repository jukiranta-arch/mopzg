"""Reader copies of the finished book for review services (Booksprout and the like): a PDF and an EPUB.

    python -m village.make_ebooks OUT_DIR

Both start with the front cover and then every interior page exactly as printed. The puzzles depend on page
layout (clues such as "within one page of a Tom Sawyer" and the list-page numbers), so the EPUB is fixed-layout:
each page is one picture of the printed page, never reflowed text.
"""

import datetime
import io
import os
import sys
import uuid
import zipfile

from PIL import Image

from . import story

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "books", "juniper-falls")
INTERIOR = os.path.join(BOOK, "interior.pdf")
FRONT = os.path.join(BOOK, "art", "cover_front.png")

PAGE_W, PAGE_H = 6.0, 9.0            # trim size, inches
EPUB_PX = (1200, 1800)               # 200 pixels per inch: 10 pt list names stay crisp when zoomed
BLEED = 0.125


FRONT_MATTER = ("Juniper Falls", "How This Book Works", "Before You Start")
CASE_WORDS = ("CASE ONE", "CASE TWO", "CASE THREE", "CASE FOUR", "CASE FIVE", "THE FINALE")


def contents(doc):
    """Bookmarks found from the pages themselves: the front matter and each case's opening page, as
    [title, page number in the interior]. The solutions are left out so a reader can't land on them by accident."""
    out = []
    for i, page in enumerate(doc):
        lines = [ln.strip() for ln in page.get_text().split("\n") if ln.strip()]
        if not lines:
            continue
        titles = [t for t, _ in out]
        if lines[0] == "Contents":
            out.append(["Contents", i + 1])
        elif len(lines) > 1 and lines[1] in FRONT_MATTER and lines[1] not in titles:
            out.append([lines[1], i + 1])
        elif lines[0] in CASE_WORDS:
            out.append(["%s: %s" % (lines[0].title(), lines[1]), i + 1])
    return out


def front_cover():
    """The front cover trimmed to 6 x 9 in: the picture's bleed is 1/8 in on the outer edge, top and bottom."""
    im = Image.open(FRONT).convert("RGB")
    dpi = im.height / (PAGE_H + 2 * BLEED)
    w, h = round(PAGE_W * dpi), round(PAGE_H * dpi)
    left = round((im.width - (PAGE_W + BLEED) * dpi) / 2)       # centred as on the printed cover: bleed on the right
    top = round(BLEED * dpi)
    return im.crop((left, top, left + w, top + h))


def page_images(dpi=200):
    import pymupdf
    doc = pymupdf.open(INTERIOR)
    for page in doc:
        pm = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
        yield Image.frombytes("L", (pm.width, pm.height), pm.samples)


def make_pdf(out):
    import pymupdf
    src = pymupdf.open(INTERIOR)
    doc = pymupdf.open()
    w, h = PAGE_W * 72, PAGE_H * 72
    cover = doc.new_page(width=w, height=h)
    buf = io.BytesIO()
    front_cover().save(buf, "JPEG", quality=88)
    cover.insert_image(cover.rect, stream=buf.getvalue())
    doc.insert_pdf(src)
    doc.set_metadata({"title": story.TITLE, "author": story.AUTHOR,
                      "subject": "Reader copy. " + story.SUBTITLE.format(thousands="18,000")})
    doc.set_toc([[1, "Cover", 1]] + [[1, t, p + 1] for t, p in contents(src)])
    doc.save(out, garbage=4, deflate=True)
    return doc.page_count


XHTML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head><meta charset="UTF-8"/><title>{title}</title>
<meta name="viewport" content="width={w}, height={h}"/>
<style>html,body{{margin:0;padding:0;width:{w}px;height:{h}px}}img{{display:block;width:{w}px;height:{h}px}}</style>
</head>
<body><img src="../images/{img}" alt="{alt}"/></body>
</html>
"""


def make_epub(out):
    import pymupdf
    src = pymupdf.open(INTERIOR)
    toc = contents(src)
    w, h = EPUB_PX
    pages = [("cover", front_cover().resize((w, h), Image.LANCZOS).convert("RGB"), "jpg")]
    for i, im in enumerate(page_images(), 1):
        im = im.resize((w, h), Image.LANCZOS)
        # 16 grey levels keep the text and the two-ink art exact and the file small
        pages.append(("p%03d" % i, im.quantize(16), "png"))
    book_id = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "who-sent-the-killers-" + (story.ASIN or "")))
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    manifest, spine, nav = [], [], []
    with zipfile.ZipFile(out, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>""", compress_type=zipfile.ZIP_DEFLATED)
        for n, (name, im, ext) in enumerate(pages):
            buf = io.BytesIO()
            if ext == "jpg":
                im.save(buf, "JPEG", quality=88)
                mt = "image/jpeg"
            else:
                im.save(buf, "PNG", optimize=True)
                mt = "image/png"
            img = "%s.%s" % (name, ext)
            z.writestr("OEBPS/images/" + img, buf.getvalue(), compress_type=zipfile.ZIP_STORED)
            label = "Cover" if name == "cover" else "Page %d" % n
            z.writestr("OEBPS/pages/%s.xhtml" % name,
                       XHTML.format(title=label, w=w, h=h, img=img, alt=label), compress_type=zipfile.ZIP_DEFLATED)
            props = ' properties="cover-image"' if name == "cover" else ""
            manifest.append('<item id="img-%s" href="images/%s" media-type="%s"%s/>' % (name, img, mt, props))
            manifest.append('<item id="%s" href="pages/%s.xhtml" media-type="application/xhtml+xml"/>' % (name, name))
            spine.append('<itemref idref="%s"/>' % name)
        nav.append('<li><a href="pages/cover.xhtml">Cover</a></li>')
        for title, p in toc:
            nav.append('<li><a href="pages/p%03d.xhtml">%s</a></li>' % (p, title.replace("&", "&amp;")))
        z.writestr("OEBPS/nav.xhtml", """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head><meta charset="UTF-8"/><title>Contents</title></head>
<body><nav epub:type="toc" id="toc"><h1>Contents</h1><ol>%s</ol></nav></body>
</html>""" % "".join(nav), compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="en">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">%s</dc:identifier>
<dc:title>%s</dc:title>
<dc:creator>%s</dc:creator>
<dc:language>en</dc:language>
<dc:description>Reader copy. %s</dc:description>
<meta property="dcterms:modified">%s</meta>
<meta property="rendition:layout">pre-paginated</meta>
<meta property="rendition:orientation">portrait</meta>
<meta property="rendition:spread">none</meta>
</metadata>
<manifest>
<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
%s
</manifest>
<spine>%s</spine>
</package>""" % (book_id, story.TITLE, story.AUTHOR, story.SUBTITLE.format(thousands="18,000"), now,
                 "\n".join(manifest), "".join(spine)), compress_type=zipfile.ZIP_DEFLATED)
    return len(pages)


def main(argv):
    out = argv[0] if argv else os.path.join(BOOK, "ebook")
    os.makedirs(out, exist_ok=True)
    pdf = os.path.join(out, "who-sent-the-killers.pdf")
    epub = os.path.join(out, "who-sent-the-killers.epub")
    print("PDF: %d pages, %.1f MB" % (make_pdf(pdf), os.path.getsize(pdf) / 1e6))
    print("EPUB: %d pages, %.1f MB" % (make_epub(epub), os.path.getsize(epub) / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
