/* Captures a product page for real (no test hooks) and reports: whether a
 * download started by itself (it must not), the one from clicking "Save file",
 * and the "Copy data" text.
 * Usage: node run_download.js <product url> <path to capture.js> */
const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const [url, script] = process.argv.slice(2);
  const browser = await chromium.launch();
  const context = await browser.newContext({ acceptDownloads: true });
  await context.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: new URL(url).origin });
  const page = await context.newPage();
  await page.goto(url);
  const out = {};
  const auto = page.waitForEvent('download', { timeout: 5000 }).then((d) => d.suggestedFilename(), () => null);
  await page.addScriptTag({ content: fs.readFileSync(script, 'utf8') });
  out.auto = await auto;
  const again = page.waitForEvent('download', { timeout: 5000 }).then((d) => d.suggestedFilename(), () => null);
  await page.click('text=Save file');
  out.again = await again;
  await page.click('text=Copy data');
  await page.waitForTimeout(300);
  try { out.copied = JSON.parse(await page.evaluate(() => navigator.clipboard.readText())); } catch (e) { out.copied = null; }
  process.stdout.write(JSON.stringify(out));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
