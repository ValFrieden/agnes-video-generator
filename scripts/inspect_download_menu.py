import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from core.api.google_flow_engine import GoogleFlowEngine

async def inspect():
    e = GoogleFlowEngine()
    p = await e.connect()
    print("Current URL:", p.url)
    await p.screenshot(path="output/shot27_editor_state.png")

    items = await p.query_selector_all("button, [role='menuitem'], flow-menu-item, [role='button'], div, span")
    seen = set()
    for item in items:
        try:
            t = (await item.text_content() or "").strip()
            aria = await item.get_attribute("aria-label") or ""
            comb = (t + " " + aria).lower()
            if any(w in comb for w in ["720", "1080", "herunterladen", "download", "mp4"]):
                val = f"text={t!r}, aria={aria!r}"
                if val not in seen and len(t) < 50:
                    seen.add(val)
                    print("Found element:", val)
        except Exception:
            pass

    # Also inspect video src
    vids = await p.query_selector_all("video")
    print(f"Total videos on page: {len(vids)}")
    for i, v in enumerate(vids):
        src = await v.get_attribute("src")
        print(f"Video {i} src: {src[:120] if src else 'None'}")

if __name__ == '__main__':
    asyncio.run(inspect())
