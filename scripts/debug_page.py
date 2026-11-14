import asyncio
import json
import sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.api.google_flow_engine import GoogleFlowEngine

async def main():
    engine = GoogleFlowEngine()
    page = await engine.connect()
    res = await page.evaluate("""() => {
        const tiles = document.querySelectorAll('flow-video-tile').length;
        const body = document.body.innerText;
        const regex = new RegExp('(\\\\d+)\\\\s*%', 'g');
        const matches = [];
        let m;
        while ((m = regex.exec(body)) !== null) {
            matches.push({val: m[0], ctx: body.slice(Math.max(0, m.index - 30), Math.min(body.length, m.index + 30))});
        }
        const editor = !!document.querySelector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]');
        return {url: window.location.href, tiles, matches, editor};
    }""")
    print(json.dumps(res, indent=2))

if __name__ == '__main__':
    asyncio.run(main())
