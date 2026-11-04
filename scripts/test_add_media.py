import asyncio
import json
import urllib.request
import websockets

async def check_add_menu():
    pages = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    page = next(p for p in pages if 'flow.google.com' in p.get('url', ''))
    ws_url = page['webSocketDebuggerUrl']
    async with websockets.connect(ws_url) as ws:
        click_add = """(() => {
            const btn = document.querySelector('button[aria-label*="Medien hinzufügen"], button[aria-label*="Add media"]');
            if (btn) {
                btn.click();
                return 'Clicked add media button';
            }
            return 'Not found';
        })()"""
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_add, 'returnByValue': True}}))
        print(json.loads(await ws.recv())['result']['result']['value'])
        await asyncio.sleep(0.8)

        get_menu = """(() => {
            const menu = document.querySelector('.mat-mdc-menu-panel, [role="menu"]');
            if (!menu) return 'No menu';
            const items = Array.from(menu.querySelectorAll('button, [role="menuitem"]')).map(b => (b.innerText || '').trim().replace(/\\n+/g, ' '));
            return items;
        })()"""
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': get_menu, 'returnByValue': True}}))
        print('Menu items:', json.loads(await ws.recv())['result']['result']['value'])

if __name__ == '__main__':
    asyncio.run(check_add_menu())
