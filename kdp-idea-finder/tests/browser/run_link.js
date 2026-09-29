/* Clicks a link whose href is the bookmarklet URL, as a bookmark click does, and prints the capture.
 * Usage: node run_link.js <page url> <file holding the javascript: URL> */
const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const [url, hrefFile] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(url);
  await page.evaluate((href) => {
    window.__KDP_CAPTURE_TEST__ = true;
    const a = document.createElement('a');
    a.id = 'bm-link';
    a.href = href;
    a.textContent = 'KDP Capture';
    document.body.appendChild(a);
  }, fs.readFileSync(hrefFile, 'utf8'));
  await page.click('#bm-link');
  await page.waitForFunction(() => window.__KDP_RESULT__, null, { timeout: 20000 });
  process.stdout.write(JSON.stringify(await page.evaluate(() => window.__KDP_RESULT__)));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
