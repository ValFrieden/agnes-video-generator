import asyncio
import json
import urllib.request
import websockets

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl']) as ws:
        click_model = """
        (() => {
            const btn = document.querySelector('button[aria-label="Zu den Einstellungen"]');
            if (btn) {
                btn.click();
                return 'Clicked model button';
            }
            return 'Not found';
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_model, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print(res['result']['result']['value'])
        await asyncio.sleep(0.5)

        script = """
        (() => {
            const items = Array.from(document.querySelectorAll('.mat-mdc-menu-panel *, [role="menu"] *, [role="listbox"] *, [class*="option"], [class*="item"]'))
                .filter(el => el.innerText && el.innerText.trim().length > 0 && el.children.length === 0)
                .map(el => el.innerText.trim());
            return Array.from(new Set(items));
        })()
        """
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res2 = json.loads(await ws.recv())
        print("Model options:", json.dumps(res2['result']['result']['value'], ensure_ascii=False, indent=2))

if __name__ == '__main__':
    asyncio.run(check())
