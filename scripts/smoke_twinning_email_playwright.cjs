const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const { pathToFileURL } = require('url');

const fixturePath = path.resolve(process.argv[2] || path.join(__dirname, '..', '.tmp-twinning-email.html'));
const screenshotDir = path.resolve(process.argv[3] || path.join(__dirname, '..', '.tmp-twinning-playwright'));
if (!fs.existsSync(fixturePath)) throw new Error(`Missing preview: ${fixturePath}`);
fs.mkdirSync(screenshotDir, { recursive: true });

const projectRequire = createRequire(path.join(process.cwd(), 'package.json'));
const { chromium } = projectRequire('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const cases = [
      { name: 'desktop', width: 1280, height: 900 },
      { name: 'mobile', width: 390, height: 844 },
    ];
    for (const item of cases) {
      const page = await browser.newPage({ viewport: { width: item.width, height: item.height } });
      await page.goto(pathToFileURL(fixturePath).href, { waitUntil: 'load' });
      await page.getByText('Nowa fiszka Twinning', { exact: false }).waitFor();
      await page.getByText('Wymagania obowiązkowe', { exact: true }).waitFor();
      await page.getByText('Ważne: jak można dołączyć', { exact: true }).waitFor();
      const links = await page.locator('a').count();
      if (links !== 2) throw new Error(`Expected 2 CTA links, got ${links}`);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      if (overflow > 1) throw new Error(`Horizontal overflow ${overflow}px for ${item.name}`);
      await page.screenshot({ path: path.join(screenshotDir, `${item.name}.png`), fullPage: true });
      await page.close();
    }
    process.stdout.write(JSON.stringify({ ok: true, screenshots: screenshotDir }));
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error);
  process.exit(1);
});

