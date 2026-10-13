// Screenshot del template renderizzato (mobile + desktop).
// Uso: PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers NODE_PATH=$(npm root -g) node tools/screenshot.cjs
// (eseguire da site/ dopo `python3 tools/build_preview.py`)
const path = require("path");
const { chromium } = require("playwright");

(async () => {
  const site = path.resolve(__dirname, "..");
  const url = "file://" + path.join(site, "preview", "product.html");
  const browser = await chromium.launch();
  const shots = [
    { file: "preview-mobile.png", viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
    { file: "preview-desktop.png", viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 },
  ];
  for (const s of shots) {
    const ctx = await browser.newContext({ viewport: s.viewport, deviceScaleFactor: s.deviceScaleFactor, isMobile: !!s.isMobile, hasTouch: !!s.hasTouch, locale: "it-IT" });
    const page = await ctx.newPage();
    await page.goto(url, { waitUntil: "load" });
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(site, s.file), fullPage: true });
    console.log("scritto", s.file);
    await ctx.close();
  }
  // home: solo desktop, utile per revisione
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: "it-IT" });
  const page = await ctx.newPage();
  await page.goto("file://" + path.join(site, "preview", "index.html"), { waitUntil: "load" });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(site, "preview", "home-desktop.png"), fullPage: true });
  await browser.close();
})();
