"""Build the KDP Capture bookmarklet and a one-page installer."""

import html
import os
import re
import urllib.parse

SOURCE = os.path.join(os.path.dirname(__file__), "capture.js")

# Firefox refuses to store a bookmark longer than 65,536 characters.
FIREFOX_URL_LIMIT = 65536
# Characters left as they are in the javascript: URL. Everything else is
# percent-encoded: %, quotes, <, >, &, # (a fragment), spaces, newlines, backslashes.
URL_SAFE = "!$'()*+,-./:;=?@[]^_`{|}~"


def source():
    with open(SOURCE, encoding="utf-8") as fh:
        return fh.read()


_REGEX_AFTER = set("(,=:[!&|?{};+-*%<>~^")


def minify(js):
    """Drop comments and indentation. Line breaks stay, so automatic semicolon
    insertion works as in the source. Strings and regex literals are copied as-is."""
    out, i, n, last = [], 0, len(js), ""
    while i < n:
        c = js[i]
        if c in "'\"`":
            j = i + 1
            while js[j] != c:
                j += 2 if js[j] == "\\" else 1
            out.append(js[i:j + 1])
            last, i = c, j + 1
            continue
        if js.startswith("/*", i):
            j = js.index("*/", i + 2)
            out.append("\n" if "\n" in js[i:j] else " ")
            i = j + 2
            continue
        if js.startswith("//", i):
            j = js.find("\n", i)
            i = n if j < 0 else j
            continue
        if c == "/" and (last == "" or last in _REGEX_AFTER or
                         re.search(r"\b(?:return|typeof|case)\s*$", "".join(out[-12:]))):
            j, in_class = i + 1, False
            while True:
                ch = js[j]
                if ch == "\\":
                    j += 2
                    continue
                if ch == "\n":
                    raise ValueError("unterminated regex literal at %d" % i)
                if ch == "[":
                    in_class = True
                elif ch == "]":
                    in_class = False
                elif ch == "/" and not in_class:
                    break
                j += 1
            j += 1
            while j < n and js[j].isalpha():
                j += 1
            out.append(js[i:j])
            last, i = "/", j
            continue
        out.append(c)
        if not c.isspace():
            last = c
        i += 1
    lines = (re.sub(r"[ \t]+$", "", ln).lstrip() for ln in "".join(out).split("\n"))
    return "\n".join(ln for ln in lines if ln)


def url():
    return "javascript:" + urllib.parse.quote(minify(source()), safe=URL_SAFE)


def install_page(path):
    page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>KDP Capture</title>
<style>
body{font:16px/1.55 system-ui,sans-serif;max-width:640px;margin:40px auto;padding:0 16px;color:#1b1b1b;background:#fafaf7}
a.bm{display:inline-block;padding:10px 18px;background:#ff9900;color:#111;border-radius:6px;font-weight:600;text-decoration:none}
code{background:#eee;padding:1px 5px;border-radius:4px}
</style></head><body>
<h1>KDP Capture</h1>
<p>Drag this button to your bookmarks bar:</p>
<p><a class="bm" href="%s">KDP Capture</a></p>
<ol>
<li>Open an Amazon search for a niche, e.g. <code>gratitude journal for men</code> (Books department).</li>
<li>Click <b>KDP Capture</b>. It reads the top organic results one by one, slowly on purpose (about a minute), and downloads a <code>kdp_capture_*.json</code> file.</li>
<li>Also works on a single product page and on Best Sellers, Movers &amp; Shakers and New Releases pages.</li>
<li>Run <code>kdp import ~/Downloads/kdp_capture_*.json</code>, then <code>kdp next</code>.</li>
</ol>
<p>If Amazon shows a captcha, the capture stops and saves what it has. Wait a while before the next one.</p>
</body></html>
""" % html.escape(url(), quote=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return path
