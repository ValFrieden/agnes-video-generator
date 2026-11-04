import { chromium } from 'playwright';
import fs from 'fs';

async function main() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
  const context = browser.contexts()[0];
  const page = context.pages().find(p => p.url().includes('flow.google.com')) || context.pages()[0];
  console.log('Page URL:', page.url());
  console.log('Page Title:', await page.title());
  
  // Wait for network idle or 3 seconds
  await page.waitForTimeout(3000);
  
  const client = await page.context().newCDPSession(page);
  const { data } = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('door_frames/flow_live_state.png', Buffer.from(data, 'base64'));
  console.log('Saved door_frames/flow_live_state.png');
  
  // Let's check text content of buttons and links
  const texts = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('button, a, h1, h2, span'))
      .map(el => el.innerText?.trim())
      .filter(t => t && t.length > 2 && t.length < 50)
      .slice(0, 30);
  });
  console.log('Page elements sample:', texts);
  
  await browser.close();
}

main().catch(console.error);
