import asyncio
import json
import urllib.request
import websockets

def get_ws_url():
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    pages = json.loads(req.read().decode())
    flow_page = next((p for p in pages if "flow.google.com" in p.get("url", "")), None)
    return flow_page["webSocketDebuggerUrl"]

async def check_plus():
    ws_url = get_ws_url()
    async with websockets.connect(ws_url) as ws:
        click_plus = """(() => {
            const btn = document.querySelector('button[aria-label*="Bildelemente"], button.add-menu-trigger');
            if (btn) {
                btn.click();
                return 'Clicked plus button';
            }
            return 'Plus button not found';
        })()"""
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_plus, 'returnByValue': True}}))
        print(json.loads(await ws.recv())['result']['result']['value'])
        await asyncio.sleep(0.8)

        get_menu = """(() => {
            const items = Array.from(document.querySelectorAll('.mat-mdc-menu-panel, [role="menu"], [role="menuitem"], .mat-mdc-menu-item')).map(el => (el.innerText || '').trim().replace(/\\n+/g, ' '));
            return items.filter(t => t.length > 0);
        })()"""
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': get_menu, 'returnByValue': True}}))
        print('Menu items:', json.loads(await ws.recv())['result']['result']['value'])

if __name__ == '__main__':
    asyncio.run(check_plus())
