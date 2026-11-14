import asyncio
import json
import urllib.request
import websockets

async def check_model():
    tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        js = """
        (() => {
            const elements = Array.from(document.querySelectorAll('button, div[role="button"], span, mat-select, .model-selector'))
                .filter(el => {
                    const t = (el.innerText || el.getAttribute('aria-label') || '').toLowerCase();
                    return t.includes('veo') || t.includes('omni') || t.includes('flash') || t.includes('quality') || t.includes('fast');
                })
                .map(el => ({
                    text: el.innerText.trim(),
                    aria: el.getAttribute('aria-label'),
                    className: el.className,
                    tag: el.tagName
                }));

            // Check the settings button next to the prompt box
            const promptBox = document.querySelector('.agent-panel-prompt-box, [class*="prompt-box"]') || document.body;
            const promptControls = Array.from(promptBox.querySelectorAll('button')).map(b => ({
                text: b.innerText.trim(),
                aria: b.getAttribute('aria-label'),
                className: b.className
            }));

            return {
                modelElements: elements,
                promptControls
            };
        })()
        """
        cid = 114
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("Model status in Flow:")
        print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(check_model())
