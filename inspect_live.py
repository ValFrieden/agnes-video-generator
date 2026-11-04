import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp('http://127.0.0.1:9222')
        context = browser.contexts[0]
        page = None
        for pg in context.pages:
            if 'flow.google.com' in pg.url:
                page = pg
                break
        if not page:
            page = context.pages[0]

        await page.screenshot(path='d:/Projects/VideoGenerator/moy_mir_iz_snov_frames/debug_python_live.png')
        print('Saved screenshot to debug_python_live.png')

        # Check for retry button or generating state
        text = await page.content()
        has_retry = 'Noch einmal versuchen' in text or 'Try again' in text
        has_spinner = 'mat-spinner' in text
        print(f'has_retry: {has_retry}, has_spinner: {has_spinner}')

asyncio.run(main())
