/* Runs Autopilot on a mock Amazon front page: discover, capture (hits a captcha),
 * then click KDP Capture again and continue. Prints what happened as JSON.
 * Usage: node run_autopilot.js <base url> <path to capture.js> */
const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const [base, script] = process.argv.slice(2);
  const code = fs.readFileSync(script, 'utf8');
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(base + '/');
  await page.evaluate((b) => {
    window.__KDP_CAPTURE_TEST__ = true;
    window.__KDP_AUTOPILOT__ = true;
    window.KDP_AC_URL = b + '/api/2017/suggestions';
  }, base);
  await page.addScriptTag({ content: code });
  await page.fill('#kdp-roots', 'gift for');
  await page.fill('#kdp-howmany', '2');
  await page.click('text=1. Find what people search');
  await page.waitForFunction(() => /searches found/.test(document.getElementById('kdp-status').textContent));
  const ticked = await page.$$eval('#kdp-list input:checked', (els) => els.map((e) => e.value));
  await page.click('text=2. Capture ticked searches');
  await page.waitForFunction(() => window.__KDP_DONE__, null, { timeout: 30000 });
  const first = await page.evaluate(() => ({
    downloads: window.__KDP_DOWNLOADS__.splice(0),
    state: JSON.parse(localStorage.getItem('kdp-autopilot-state')),
    status: document.getElementById('kdp-status').textContent,
  }));

  /* Click the bookmarklet again: the panel offers to continue. */
  await page.evaluate(() => { window.__KDP_DONE__ = false; });
  await page.addScriptTag({ content: code });
  const resumeText = await page.textContent('#kdp-resume');
  await page.click('#kdp-continue');
  await page.waitForFunction(() => window.__KDP_DONE__, null, { timeout: 30000 });
  const second = await page.evaluate(() => ({
    downloads: window.__KDP_DOWNLOADS__.splice(0),
    state: localStorage.getItem('kdp-autopilot-state'),
  }));
  await page.click('#kdp-save');
  const saveAgain = await page.evaluate(() => window.__KDP_DOWNLOADS__.length);
  process.stdout.write(JSON.stringify({ ticked, first, resumeText, second, saveAgain }));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
