import asyncio
import json
import urllib.request
import websockets

async def search_media():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        expr = """
        (() => {
            const input = document.querySelector('.add-menu-popover-container input');
            if (!input) return { error: 'input not found' };
            input.focus();
            input.value = 'storm';
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            return { success: true };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Search input set:", res['result']['result']['value'])
        await asyncio.sleep(1)

        # Check results
        expr2 = """
        (() => {
            const container = document.querySelector('.add-menu-popover-container');
            const items = Array.from(container.querySelectorAll('.mat-mdc-list-item-title, [class*="title"], [class*="name"]'))
                .map(el => (el.innerText || '').trim())
                .filter(t => t.length > 0);
            return items;
        })()
        """
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr2, 'returnByValue': True}}))
        res2 = json.loads(await ws.recv())
        print("Search results for 'storm':", res2['result']['result']['value'])

if __name__ == '__main__':
    asyncio.run(search_media())
