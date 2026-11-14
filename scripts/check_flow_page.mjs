import { chromium } from 'playwright';

async function main() {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
  const context = browser.contexts()[0];
  const pages = context.pages();
  console.log(`Found ${pages.length} open pages:`);
  for (let i = 0; i < pages.length; i++) {
    console.log(`[${i}] Title: "${await pages[i].title()}", URL: ${pages[i].url()}`);
  }
  
  const flowPage = pages.find(p => p.url().includes('flow.google.com')) || pages[0];
  console.log(`\nActive Flow Page URL: ${flowPage.url()}`);
  
  // Screenshot to nikogda_ne_boyus_frames/flow_current_state.png
  await flowPage.screenshot({ path: 'd:/Projects/VideoGenerator/nikogda_ne_boyus_frames/flow_current_state.png' });
  console.log('Saved screenshot to nikogda_ne_boyus_frames/flow_current_state.png');

  // Check text content on page
  const bodyText = await flowPage.innerText('body');
  const creditsMatch = bodyText.match(/(\d+[\d\s,.]*)\s*(Guthaben|Credits|Punkte)/i);
  if (creditsMatch) {
    console.log(`Credits found: ${creditsMatch[0]}`);
  }
  
  process.exit(0);
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
