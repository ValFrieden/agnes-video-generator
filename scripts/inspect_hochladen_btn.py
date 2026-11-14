import asyncio
import json
import urllib.request
import websockets

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl']) as ws:
        # Open menu first
        open_menu = """
        (() => {
            const menuBtn = document.querySelector('button[aria-label*="Medien hinzufügen"]');
            if (menuBtn) menuBtn.click();
            return 'toggled';
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': open_menu, 'returnByValue': True}}))
        await ws.recv()
        await asyncio.sleep(0.5)

        script = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button[role="menuitem"], .mat-mdc-menu-item, span'));
            const uploadBtn = btns.find(b => (b.innerText || '').trim() === 'Hochladen' || (b.innerText || '').includes('Hochladen'));
            if (!uploadBtn) return { error: 'Not found' };
            const rect = uploadBtn.getBoundingClientRect();
            return {
                tag: uploadBtn.tagName,
                outerHTML: uploadBtn.outerHTML.substring(0, 300),
                rect: { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2, w: rect.width, h: rect.height }
            };
        })()
        """
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print(json.dumps(res['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(check())
