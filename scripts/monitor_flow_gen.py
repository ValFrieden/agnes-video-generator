import asyncio
import json
import urllib.request
import websockets

def get_ws_url():
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    pages = json.loads(req.read().decode())
    flow_page = next((p for p in pages if "flow.google.com" in p.get("url", "")), None)
    return flow_page["webSocketDebuggerUrl"]

async def check():
    ws_url = get_ws_url()
    async with websockets.connect(ws_url) as ws:
        inspect = """(() => {
            const tiles = document.querySelectorAll('flow-video-tile, flow-image-tile, [class*="tile"], [class*="media-card"], [class*="asset"]');
            const spinners = document.querySelectorAll('mat-spinner, mat-progress-spinner, [role="progressbar"], .loading');
            const texts = Array.from(document.querySelectorAll('span, div, p')).map(e => (e.innerText || '').trim()).filter(t => t.includes('%') || t.includes('Generier') || t.includes('Wird erstellt') || t.includes('Generating') || t.includes('Wird generiert') || t.includes('Warteschlange'));
            return {
                tileCount: tiles.length,
                spinnerCount: spinners.length,
                statusTexts: Array.from(new Set(texts)).slice(0, 10),
                tilesFound: Array.from(tiles).map(t => ({
                    tag: t.tagName,
                    text: (t.innerText || '').slice(0, 100).replace(/\\n+/g, ' ')
                }))
            };
        })()"""
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': inspect, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print(json.dumps(res['result']['result']['value'], indent=2, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(check())
