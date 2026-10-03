/* Loads a page in Chromium, runs capture.js in test mode, prints the capture JSON.
 * Usage: node run_capture.js <url> <path to capture.js> */
const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const [url, script] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(url);
  await page.evaluate(() => { window.__KDP_CAPTURE_TEST__ = true; });
  await page.addScriptTag({ content: fs.readFileSync(script, 'utf8') });
  await page.waitForFunction(() => window.__KDP_RESULT__, null, { timeout: 20000 });
  const result = await page.evaluate(() => window.__KDP_RESULT__);
  process.stdout.write(JSON.stringify(result));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
