"""Build the KDP Capture bookmarklet and a one-page installer."""

import html
import os
import urllib.parse

SOURCE = os.path.join(os.path.dirname(__file__), "capture.js")


def source():
    with open(SOURCE, encoding="utf-8") as fh:
        return fh.read()


def url():
    return "javascript:" + urllib.parse.quote(source(), safe="")


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
