import { chromium } from 'playwright';

console.log('Connecting to CDP...');
const browser = await chromium.connectOverCDP('http://127.0.0.1:9222', { timeout: 5000 });
console.log('Connected! Contexts:', browser.contexts().length);
const pages = browser.contexts()[0].pages();
console.log('Pages count:', pages.length);
for (const p of pages) {
  console.log('Page URL:', p.url());
}
process.exit(0);
