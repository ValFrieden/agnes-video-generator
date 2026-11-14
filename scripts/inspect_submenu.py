import asyncio
import json
import urllib.request
import websockets

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl']) as ws:
        click_h = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button[role="menuitem"], .mat-mdc-menu-item, span'));
            const uploadBtn = btns.find(b => (b.innerText || '').trim() === 'Hochladen' || (b.innerText || '').includes('Hochladen'));
            if (uploadBtn) {
                uploadBtn.click();
                return 'Clicked Hochladen';
            }
            return 'Not found';
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_h, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Click:", res['result']['result']['value'])
        await asyncio.sleep(0.5)

        script = """
        (() => {
            const items = Array.from(document.querySelectorAll('.mat-mdc-menu-panel, [role="menu"], [role="menuitem"], .mat-mdc-menu-item'))
                .map(el => ({ tag: el.tagName, role: el.getAttribute('role'), text: (el.innerText || '').trim() }))
                .filter(x => x.text.length > 0);
            return items;
        })()
        """
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res2 = json.loads(await ws.recv())
        print("New menu items:", json.dumps(res2['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(check())
