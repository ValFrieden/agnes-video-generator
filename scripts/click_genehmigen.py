import asyncio
import json
import urllib.request
import websockets

def get_ws_url():
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    pages = json.loads(req.read().decode())
    flow_page = next((p for p in pages if "flow.google.com" in p.get("url", "")), None)
    return flow_page["webSocketDebuggerUrl"]

async def click_confirm():
    ws_url = get_ws_url()
    async with websockets.connect(ws_url) as ws:
        click_script = """(() => {
            const btns = Array.from(document.querySelectorAll('button'));
            // Look for "Immer genehmigen" or "Genehmigen"
            const immer = btns.find(b => (b.innerText || '').includes('Immer genehmigen') || (b.innerText || '').includes('Always approve'));
            if (immer) {
                immer.click();
                return 'Clicked Immer genehmigen!';
            }
            const genehmigen = btns.find(b => (b.innerText || '').includes('Genehmigen') || (b.innerText || '').includes('Approve'));
            if (genehmigen) {
                genehmigen.click();
                return 'Clicked Genehmigen!';
            }
            return 'Button not found';
        })()"""
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print(res['result']['result']['value'])

if __name__ == '__main__':
    asyncio.run(click_confirm())
