import asyncio
import json
import urllib.request
import websockets

async def main():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    print("Flow tab URL:", flow_tab["url"])

    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
        diag_js = """
        (() => {
            const url = window.location.href;
            const modelSelector = document.querySelector('.model-selector, [class*="model-selector"], [aria-label*="Modell"]');
            const modelText = modelSelector ? modelSelector.innerText : 'not found';
            const timeline = document.querySelector('.timeline-container, .timeline, [class*="timeline"]');
            const timelineThumbnails = Array.from(document.querySelectorAll('.timeline img, [class*="timeline"] img, .track img')).map(img => img.src);
            const promptBox = document.querySelector('.prompt-box, textarea, [contenteditable="true"]');
            const promptText = promptBox ? (promptBox.value || promptBox.innerText) : '';
            return {
                url,
                modelText,
                timelineExists: !!timeline,
                thumbnailCount: timelineThumbnails.length,
                promptText: promptText.slice(0, 100)
            };
        })()
        """
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": diag_js, "returnByValue": True}}))
        res = json.loads(await ws.recv())
        print(json.dumps(res["result"]["result"]["value"], indent=2))

if __name__ == "__main__":
    asyncio.run(main())
