import asyncio
import json
import urllib.request
import websockets

def get_ws_url():
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    pages = json.loads(req.read().decode())
    flow_page = next((p for p in pages if "flow.google.com" in p.get("url", "")), None)
    return flow_page["webSocketDebuggerUrl"]

async def check_pm():
    ws_url = get_ws_url()
    async with websockets.connect(ws_url) as ws:
        check = """(() => {
            const pm = document.querySelector('div.ProseMirror');
            const btn = document.querySelector('button[aria-label*="Generierung starten"], button.generate-icon-button') || Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('arrow_forward'));
            return {
                pmText: pm ? pm.innerText : null,
                btnDisabled: btn ? btn.disabled : null,
                btnClass: btn ? btn.className : null
            };
        })()"""
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': check, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print(json.dumps(res['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(check_pm())
