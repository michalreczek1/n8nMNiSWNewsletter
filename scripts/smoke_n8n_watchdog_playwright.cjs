const path = require('path');
const fs = require('fs');
const { createRequire } = require('module');
const { pathToFileURL } = require('url');
const { chromium } = createRequire(path.join(process.cwd(), 'package.json'))('playwright');
const root = path.resolve(__dirname, '..');
const preview = process.argv[2] || path.join(root, '.tmp-twinning-watchdog-report.html');
const output = path.join(root, '.tmp-twinning-watchdog-playwright');

(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true,
    ...(process.env.PLAYWRIGHT_EXECUTABLE_PATH ? { executablePath: process.env.PLAYWRIGHT_EXECUTABLE_PATH } : {}),
  });
  try {
    for (const width of [1280, 390]) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(pathToFileURL(preview).href);
      await page.getByRole('heading', { level: 1, name: /raport wymagający uwagi/ }).waitFor();
      const sections = await page.locator('section').count();
      if (sections < 1) throw new Error('Missing anomaly details');
      await page.getByText('Kontrola co 47 godzin', { exact: false }).waitFor();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      if (overflow > 1) throw new Error(`Horizontal overflow: ${overflow}px at ${width}px`);
      if (errors.length) throw new Error(errors.join('\n'));
      const links = await page.locator('a').all();
      for (const link of links) {
        const href = await link.getAttribute('href');
        if (!href.startsWith('https://n8n.familyos.pl/workflow/')) throw new Error(`Unexpected workflow URL: ${href}`);
      }
      await page.screenshot({ path: path.join(output, `${width}.png`), fullPage: true });
      await page.close();
    }
    console.log(JSON.stringify({ ok: true, screenshots: output }));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
