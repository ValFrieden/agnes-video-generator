import asyncio
import json
import urllib.request
import websockets
import base64
from pathlib import Path

async def main():
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    pages = json.loads(req.read().decode())
    flow_page = next((p for p in pages if "flow.google.com" in p.get("url", "")), None)
    if not flow_page:
        print("Flow page not found!")
        return

    ws_url = flow_page["webSocketDebuggerUrl"]
    print("Connecting to Flow CDP:", ws_url)

    async with websockets.connect(ws_url, max_size=100*1024*1024) as ws:
        # Take fast screenshot
        await ws.send(json.dumps({"id": 1, "method": "Page.captureScreenshot", "params": {"format": "png"}}))
        resp = json.loads(await ws.recv())
        img_data = base64.b64decode(resp["result"]["data"])
        out_png = Path("C:/Users/Valeri/.gemini/antigravity-ide/brain/a184086b-b003-494b-a42d-1bb6fbd2a207/.tempmediaStorage/flow_direct_cdp.png")
        out_png.write_bytes(img_data)
        print("Direct screenshot saved successfully, size:", len(img_data))

        # Check DOM info
        eval_expr = """
        (() => {
            const tiles = Array.from(document.querySelectorAll('flow-video-tile')).map((t, i) => {
                const r = t.getBoundingClientRect();
                const img = t.querySelector('img');
                const v = t.querySelector('video');
                return {
                    index: i,
                    rect: { x: r.x, y: r.y, w: r.width, h: r.height },
                    text: t.innerText.trim(),
                    imgSrc: img ? img.src : null,
                    videoSrc: v ? (v.currentSrc || v.src) : null
                };
            });
            const editor = document.querySelector('.ProseMirror');
            return {
                tilesCount: tiles.length,
                tiles,
                hasEditor: !!editor
            };
        })()
        """
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": eval_expr, "returnByValue": True}}))
        eval_resp = json.loads(await ws.recv())
        val = eval_resp.get("result", {}).get("result", {}).get("value", {})
        print("Flow Status:", json.dumps(val, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
