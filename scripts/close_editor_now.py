import asyncio
import sys
from pathlib import Path

# Fix Windows stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.google_flow_engine import GoogleFlowEngine


async def main():
    engine = GoogleFlowEngine()
    page = await engine.connect()
    print("URL before close:", page.url)

    res = await page.evaluate("""() => {
        // Ищем кнопку 'Fertig' или 'arrow_back'
        const btns = Array.from(document.querySelectorAll('button'));
        const fertig = btns.find(b => (b.innerText || '').trim() === 'Fertig' || (b.innerText || '').trim() === 'Done');
        if (fertig) {
            fertig.click();
            return 'CLICKED_FERTIG';
        }
        const back = btns.find(b => (b.innerText || '').includes('arrow_back') || b.getAttribute('aria-label') === 'arrow_back');
        if (back) {
            back.click();
            return 'CLICKED_BACK';
        }
        return 'BUTTON_NOT_FOUND';
    }""")
    print("Action result:", res)
    await asyncio.sleep(2.0)
    print("URL after close:", page.url)
    await page.screenshot(path="output/screen_after_close.png")


if __name__ == "__main__":
    asyncio.run(main())
