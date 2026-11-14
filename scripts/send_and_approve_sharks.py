import asyncio
import json
import urllib.request
import websockets
import time

async def main():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read())
    flow_tab = next(t for t in tabs if "flow.google.com" in t.get("url", ""))
    print("Connecting to Flow:", flow_tab["webSocketDebuggerUrl"])
    
    async with websockets.connect(flow_tab["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
        # Click the generate-icon-button
        click_script = """
        (() => {
            const btn = document.querySelector('button[aria-label="Generierung starten"], .generate-icon-button');
            if (btn) {
                btn.focus();
                btn.click();
                return { success: true, text: btn.innerText, aria: btn.getAttribute('aria-label') };
            }
            return { success: false, error: 'Button not found' };
        })()
        """
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": click_script, "returnByValue": True}}))
        res = json.loads(await ws.recv())
        print("Click result:", res["result"]["result"]["value"])
        
        # Now watch for Genehmigen button or response
        print("Monitoring for approval / Genehmigen card...")
        for i in range(45):
            await asyncio.sleep(1)
            check_script = """
            (() => {
                const buttons = Array.from(document.querySelectorAll('button, .option-row'));
                const genBtn = buttons.find(b => {
                    const txt = (b.innerText || '').trim();
                    return (txt.includes('Genehmigen') || txt.includes('Сгенерировать')) && !b.classList.contains('read-only') && !b.disabled;
                });
                
                const lastTexts = Array.from(document.querySelectorAll('div, p, span'))
                    .filter(el => el.innerText && el.innerText.trim().length > 0 && el.children.length === 0)
                    .map(el => el.innerText.trim())
                    .slice(-8);
                
                if (genBtn) {
                    genBtn.focus();
                    genBtn.click();
                    return { found_genehmigen: true, clicked: true, text: genBtn.innerText, lastTexts };
                }
                return { found_genehmigen: false, lastTexts };
            })()
            """
            await ws.send(json.dumps({"id": 100 + i, "method": "Runtime.evaluate", "params": {"expression": check_script, "returnByValue": True}}))
            check_res = json.loads(await ws.recv())
            val = check_res["result"]["result"]["value"]
            if val.get("found_genehmigen"):
                print(f"[{i}s] APPROVED! Clicked Genehmigen: {val['text']}")
                # Also click it via mouse event to be 100% sure
                mouse_script = """
                (() => {
                    const buttons = Array.from(document.querySelectorAll('button, .option-row'));
                    const genBtn = buttons.find(b => (b.innerText || '').trim().includes('Genehmigen'));
                    if (genBtn) {
                        const rect = genBtn.getBoundingClientRect();
                        return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
                    }
                    return null;
                })()
                """
                await ws.send(json.dumps({"id": 200, "method": "Runtime.evaluate", "params": {"expression": mouse_script, "returnByValue": True}}))
                m_res = json.loads(await ws.recv())
                coords = m_res["result"]["result"]["value"]
                if coords:
                    await ws.send(json.dumps({"id": 201, "method": "Input.dispatchMouseEvent", "params": {"type": "mousePressed", "x": coords["x"], "y": coords["y"], "button": "left", "clickCount": 1}}))
                    await ws.recv()
                    await ws.send(json.dumps({"id": 202, "method": "Input.dispatchMouseEvent", "params": {"type": "mouseReleased", "x": coords["x"], "y": coords["y"], "button": "left", "clickCount": 1}}))
                    await ws.recv()
                    print(f"Dispatched mouse click at {coords}")
                break
            else:
                if i % 3 == 0:
                    print(f"[{i}s] waiting... latest texts:", val.get("lastTexts")[-3:])

if __name__ == "__main__":
    asyncio.run(main())
