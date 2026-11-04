import asyncio
import json
import urllib.request
import websockets

async def check_tune():
    pages = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    page = next(p for p in pages if 'flow.google.com' in p.get('url', ''))
    ws_url = page['webSocketDebuggerUrl']
    async with websockets.connect(ws_url) as ws:
        click_tune = """(() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const tune = btns.find(b => (b.getAttribute('aria-label') || '').includes('Einstellungen') || b.innerText.includes('tune'));
            if (tune) {
                tune.click();
                return 'Clicked tune';
            }
            return 'Tune not found';
        })()"""
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_tune, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print(res['result']['result']['value'])
        await asyncio.sleep(1)

        inspect_menu = """(() => {
            const items = Array.from(document.querySelectorAll('.mat-mdc-menu-panel, [role="menu"], [role="dialog"], button, span'));
            const texts = items.map(el => (el.innerText || '').trim().replace(/\\n+/g, ' | ')).filter(t => t.length > 0 && t.length < 80);
            return Array.from(new Set(texts)).slice(0, 35);
        })()"""
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': inspect_menu, 'returnByValue': True}}))
        res2 = json.loads(await ws.recv())
        print('Menu items:', json.dumps(res2['result']['result']['value'], indent=2, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(check_tune())
