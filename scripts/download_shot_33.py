import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.api.google_flow_engine import GoogleFlowEngine

async def main():
    target = Path("output/shot_33_lake_dawn_panorama.mp4")
    brain_dir = Path(r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66")
    engine = GoogleFlowEngine()
    page = await engine.connect()

    print("Current page URL:", page.url)
    print("Checking if editor download button is visible...")
    btn = await page.query_selector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]')
    if not (btn and await btn.is_visible()):
        print("Clicking first tile to open editor...")
        await page.evaluate("""(() => {
            const tiles = document.querySelectorAll('flow-video-tile');
            if (tiles.length > 0) tiles[0].click();
        })()""")
        await asyncio.sleep(3.0)

    print("Triggering download...")
    async with page.expect_download(timeout=60000) as dl_info:
        btn = await page.query_selector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]')
        if btn:
            await btn.click()
            await asyncio.sleep(1.0)

        clicked = await page.evaluate("""(() => {
            const all = Array.from(document.querySelectorAll('*'));
            const opt = all.find(el => el.innerText && el.innerText.includes('720p') && (
                el.getAttribute('role') === 'menuitem' || 
                el.tagName === 'BUTTON' || 
                el.classList.contains('mat-mdc-menu-item') ||
                el.tagName === 'SPAN'
            ));
            if (opt) {
                const clickTarget = opt.closest('button') || opt.closest('[role=\"menuitem\"]') || opt;
                clickTarget.click();
                return true;
            }
            return false;
        })()""")
        print("Clicked 720p:", clicked)

    download = await dl_info.value
    await download.save_as(str(target))
    print(f"Saved: {target} ({target.stat().st_size} bytes)")

    # QC Frames
    qc_25 = target.parent / f"{target.stem}_qc_25.jpg"
    qc_50 = target.parent / f"{target.stem}_qc_50.jpg"
    qc_75 = target.parent / f"{target.stem}_qc_75.jpg"
    qa_contact = target.parent / f"{target.stem}_qa_trio.png"

    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(target)]
    ).decode().strip())

    subprocess.run(["ffmpeg", "-y", "-ss", str(dur*0.25), "-i", str(target), "-vframes", "1", "-q:v", "2", str(qc_25)], check=True)
    subprocess.run(["ffmpeg", "-y", "-ss", str(dur*0.50), "-i", str(target), "-vframes", "1", "-q:v", "2", str(qc_50)], check=True)
    subprocess.run(["ffmpeg", "-y", "-ss", str(dur*0.75), "-i", str(target), "-vframes", "1", "-q:v", "2", str(qc_75)], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", str(qc_25), "-i", str(qc_50), "-i", str(qc_75), "-filter_complex", "hstack=inputs=3", str(qa_contact)], check=True)

    brain_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(target), brain_dir / target.name)
    shutil.copy2(str(qc_25), brain_dir / qc_25.name)
    shutil.copy2(str(qc_50), brain_dir / qc_50.name)
    shutil.copy2(str(qc_75), brain_dir / qc_75.name)
    shutil.copy2(str(qa_contact), brain_dir / qa_contact.name)
    print("Done QC & Brain copy for Shot 33!")

if __name__ == '__main__':
    asyncio.run(main())
