import asyncio
import json
import urllib.request
import websockets

async def click_deep():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"]) as ws:
        js = """
        (() => {
            const elements = Array.from(document.querySelectorAll('*'));
            const targets = elements.filter(el => {
                const t = (el.innerText || '').trim();
                return (t.includes('Veo 3.1 - Lite') || t.includes('10 credits')) && el.children.length === 0;
            });
            if (targets.length > 0) {
                const target = targets[0];
                const clickable = target.closest('button') || target.closest('[role="button"]') || target.closest('.option-row') || target.parentElement;
                (clickable || target).click();
                return {
                    clicked: true,
                    targetText: target.innerText,
                    clickableTag: clickable ? clickable.tagName : null,
                    clickableClass: clickable ? clickable.className : null
                };
            }
            return { clicked: false, foundCount: targets.length };
        })()
        """
        cid = 123
        await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        res = json.loads(raw).get("result", {}).get("result", {}).get("value")
        print("Deep click result:", json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(click_deep())
