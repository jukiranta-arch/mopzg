/* Runs Autopilot on a mock Amazon front page and prints the files it would download.
 * Usage: node run_autopilot.js <base url> <path to capture.js> */
const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const [base, script] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(base + '/');
  await page.evaluate((b) => {
    window.__KDP_CAPTURE_TEST__ = true;
    window.__KDP_AUTOPILOT__ = true;
    window.KDP_AC_URL = b + '/api/2017/suggestions';
  }, base);
  await page.addScriptTag({ content: fs.readFileSync(script, 'utf8') });
  await page.fill('#kdp-roots', 'gift for');
  await page.fill('#kdp-howmany', '2');
  await page.click('text=1. Find what people search');
  await page.waitForFunction(() => /searches found/.test(document.getElementById('kdp-status').textContent));
  const ticked = await page.$$eval('#kdp-list input:checked', (els) => els.map((e) => e.value));
  await page.click('text=2. Capture ticked searches');
  await page.waitForFunction(() => window.__KDP_DONE__, null, { timeout: 30000 });
  const downloads = await page.evaluate(() => window.__KDP_DOWNLOADS__);
  process.stdout.write(JSON.stringify({ ticked, downloads }));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
