import asyncio
import json
import urllib.request
import websockets
import base64
import time

async def main():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
        # Click the top-left tile
        click_script = """
        (() => {
            // Find video tiles or flow-video-tile or first video element container
            const vids = Array.from(document.querySelectorAll('video'));
            if (vids.length > 0) {
                const target = vids[0].closest('flow-video-tile, .asset-tile, .media-tile') || vids[0];
                target.click();
                return { clicked: true, tag: target.tagName, class: target.className };
            }
            return { clicked: false };
        })()
        """
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": click_script, "returnByValue": True}}))
        res = json.loads(await ws.recv())
        print("Click video tile result:", res["result"]["result"]["value"])
        
        await asyncio.sleep(2)
        
        # Take screenshot
        await ws.send(json.dumps({"id": 2, "method": "Page.captureScreenshot", "params": {"format": "png"}}))
        s_res = json.loads(await ws.recv())
        with open("d:/Projects/VideoGenerator/editor_open_snap.png", "wb") as f:
            f.write(base64.b64decode(s_res["result"]["data"]))
        print("Saved d:/Projects/VideoGenerator/editor_open_snap.png")
        
        # Check download buttons
        inspect_btns = """
        (() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            return buttons.map(b => ({
                text: b.innerText,
                aria: b.getAttribute('aria-label'),
                classes: b.className
            })).filter(b => (b.aria && (b.aria.includes('Download') || b.aria.includes('herunterladen') || b.aria.includes('Medien'))) || (b.text && (b.text.includes('Download') || b.text.includes('Herunterladen'))));
        })()
        """
        await ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": inspect_btns, "returnByValue": True}}))
        b_res = json.loads(await ws.recv())
        print("Download buttons found:", b_res["result"]["result"]["value"])

if __name__ == "__main__":
    asyncio.run(main())
