import asyncio
import json
import urllib.request
import websockets

def get_ws_url():
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    pages = json.loads(req.read().decode())
    flow_page = next((p for p in pages if "flow.google.com" in p.get("url", "")), None)
    return flow_page["webSocketDebuggerUrl"]

async def go_back():
    ws_url = get_ws_url()
    async with websockets.connect(ws_url) as ws:
        click_back = """(() => {
            const btn = document.querySelector('button[aria-label*="Zurück"], button[aria-label*="Back"], .back-button') || Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('arrow_back'));
            if (btn) {
                btn.click();
                return 'Clicked back button';
            }
            return 'Back button not found';
        })()"""
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_back, 'returnByValue': True}}))
        print(json.loads(await ws.recv())['result']['result']['value'])

if __name__ == '__main__':
    asyncio.run(go_back())
