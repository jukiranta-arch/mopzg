/* Runs "Capture reviews of these books" from the Autopilot panel on a mock Amazon page.
 * Usage: node run_reviews.js <base url> <path to capture.js> <text to paste> */
const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const [base, script, pasted] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const dialogs = [];
  page.on('dialog', (d) => { dialogs.push(d.message()); d.dismiss(); });
  await page.goto(base + '/');
  await page.evaluate(() => { window.__KDP_CAPTURE_TEST__ = true; });
  await page.addScriptTag({ content: fs.readFileSync(script, 'utf8') });
  await page.fill('#kdp-review-asins', pasted.replace(/\\n/g, '\n'));
  await page.click('#kdp-review-go');
  await page.waitForFunction(() => window.__KDP_DONE__, null, { timeout: 30000 });
  const out = await page.evaluate(() => ({
    kept: JSON.parse(localStorage.getItem('kdp-autopilot-data')),
    saved: document.getElementById('kdp-saved').textContent,
  }));
  out.dialogs = dialogs;
  process.stdout.write(JSON.stringify(out));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
