import sys
import os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from core.api.google_flow_engine import GoogleFlowEngine

async def check():
    engine = GoogleFlowEngine()
    page = await engine.connect()
    print('Connected. URL:', page.url)
    await page.screenshot(path='output/flow_shot26_generation_check.png')
    
    buttons = await page.query_selector_all('button, [role="button"], [role="radio"], .option-row')
    for b in buttons:
        txt = (await b.text_content() or '').strip()
        aria = await b.get_attribute('aria-label') or ''
        combined = (txt + ' ' + aria).lower()
        if any(w in combined for w in ['genehmigen', 'approve', 'run', 'create', 'abbrechen', 'submit', 'generier']):
            vis = await b.is_visible()
            print(f"Element: text={txt!r}, aria={aria!r}, visible={vis}")

if __name__ == '__main__':
    asyncio.run(check())
