import asyncio
import json
import urllib.request
import websockets
import base64

async def main():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
        # Click on 'Videos' tab
        click_tab = """
        (() => {
            const items = Array.from(document.querySelectorAll('button, div, span'));
            const vTab = items.find(el => el.innerText && el.innerText.trim() === 'Videos' && el.closest('button, [role="tab"], .mat-mdc-list-item'));
            if (vTab) {
                const target = vTab.closest('button, [role="tab"], .mat-mdc-list-item') || vTab;
                target.click();
                return { clicked: true, text: vTab.innerText };
            }
            return { clicked: false };
        })()
        """
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": click_tab, "returnByValue": True}}))
        res = json.loads(await ws.recv())
        print("Tab click:", res["result"]["result"]["value"])
        await asyncio.sleep(2)
        
        # Capture screenshot
        await ws.send(json.dumps({"id": 2, "method": "Page.captureScreenshot", "params": {"format": "png"}}))
        s_res = json.loads(await ws.recv())
        with open("d:/Projects/VideoGenerator/shark_video_generating.png", "wb") as f:
            f.write(base64.b64decode(s_res["result"]["data"]))
        print("Saved d:/Projects/VideoGenerator/shark_video_generating.png")
        
        # Check active rendering / percent / video tiles
        inspect = """
        (() => {
            const allElements = Array.from(document.querySelectorAll('*'));
            const percentTexts = allElements
                .filter(el => el.children.length === 0 && /\\d+%/i.test(el.innerText || ''))
                .map(el => el.innerText.trim());
            const videoCards = Array.from(document.querySelectorAll('video, [data-asset-id], .asset-tile, .media-tile'))
                .map(el => ({ tag: el.tagName, text: el.innerText, class: el.className }));
            return { percentTexts, videoCardsCount: videoCards.length, videoCards: videoCards.slice(0, 5) };
        })()
        """
        await ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": inspect, "returnByValue": True}}))
        i_res = json.loads(await ws.recv())
        print("Inspection:", json.dumps(i_res["result"]["result"]["value"], indent=2))

if __name__ == "__main__":
    asyncio.run(main())
