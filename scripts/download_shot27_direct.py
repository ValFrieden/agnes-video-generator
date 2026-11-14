import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from pathlib import Path
from core.api.google_flow_engine import GoogleFlowEngine

async def do_download():
    engine = GoogleFlowEngine(downloads_dir=r"d:\Projects\VideoGenerator\output")
    page = await engine.connect()
    target_mp4 = Path(r"d:\Projects\VideoGenerator\output\shot_27_mirror_reflections.mp4")

    # If menu is already open, click the 720p option
    print("Clicking download option...")
    
    # Let's intercept download
    async with page.expect_download(timeout=60000) as dl_info:
        clicked = await page.evaluate("""(() => {
            // Find any element containing 720p
            const all = Array.from(document.querySelectorAll('*'));
            const opt = all.find(el => el.innerText && el.innerText.includes('720p') && (el.getAttribute('role') === 'menuitem' || el.tagName === 'BUTTON' || el.classList.contains('mat-mdc-menu-item')));
            if (opt) {
                opt.click();
                return true;
            }
            // fallback: find any element with text '720p'
            const simple = all.find(el => el.innerText && el.innerText.trim().startsWith('720p'));
            if (simple) {
                simple.click();
                return true;
            }
            return false;
        })()""")
        print("Clicked 720p element:", clicked)
        if not clicked:
            # Maybe download button needs to be re-clicked
            btn = await page.query_selector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]')
            if btn:
                await btn.click()
                await asyncio.sleep(1.0)
                await page.evaluate("""(() => {
                    const all = Array.from(document.querySelectorAll('*'));
                    const opt = all.find(el => el.innerText && el.innerText.includes('720p'));
                    if (opt) opt.click();
                })()""")

    download = await dl_info.value
    await download.save_as(str(target_mp4))
    print(f"Successfully saved to {target_mp4} ({target_mp4.stat().st_size} bytes)")

if __name__ == '__main__':
    asyncio.run(do_download())
