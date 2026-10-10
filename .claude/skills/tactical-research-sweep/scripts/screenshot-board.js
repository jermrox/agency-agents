// Screenshot the published board so the owner can SEE it.
//   NODE_PATH=$(npm root -g) node screenshot-board.js OUT_DIR
// Writes desktop-top.png, desktop-full.png, mobile.png. Chromium is pre-installed at
// /opt/pw-browsers/chromium; never run "playwright install".
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const out = process.argv[2];
  const page = 'file://' + path.resolve(__dirname, '../../../../healthcare/dashboards/h2f-scout-board.html');
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  for (const [name, w, h, full] of [['desktop-top', 1280, 1500, false], ['desktop-full', 1280, 900, true], ['mobile', 390, 844, false]]) {
    const p = await b.newPage({ viewport: { width: w, height: h } });
    await p.goto(page);
    await p.waitForTimeout(500);
    await p.screenshot({ path: `${out}/${name}.png`, fullPage: full });
    await p.close();
  }
  await b.close();
})();
