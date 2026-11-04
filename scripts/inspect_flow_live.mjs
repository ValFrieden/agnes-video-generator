import { chromium } from 'playwright';

async function main() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
  const context = browser.contexts()[0];
  const page = context.pages().find(p => p.url().includes('flow.google.com'));
  if (!page) {
    console.log('No flow page found!');
    process.exit(1);
  }
  console.log('Current URL:', page.url());
  console.log('Page Title:', await page.title());
  
  await page.screenshot({ path: 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/flow_current_view.png' });
  console.log('Screenshot saved to moy_mir_iz_snov_frames/flow_current_view.png');

  const elements = await page.evaluate(() => {
    const list = [];
    document.querySelectorAll('a, button, div[role="button"], span, h1, h2, h3').forEach(el => {
      const t = (el.innerText || '').trim();
      if (t && t.length > 2 && t.length < 60) {
        list.push({ tag: el.tagName, text: t });
      }
    });
    return list;
  });

  console.log('Total text elements:', elements.length);
  // filter unique texts
  const seen = new Set();
  const unique = [];
  for (const e of elements) {
    if (!seen.has(e.text)) {
      seen.add(e.text);
      unique.push(e);
    }
  }
  console.log('Unique elements sample:', JSON.stringify(unique.slice(0, 40), null, 2));
  process.exit(0);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
