import asyncio
import json
import urllib.request
import websockets

async def get_popover_titles():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        expr = """
        (() => {
            const container = document.querySelector('.add-menu-popover-container');
            if (!container) return { error: 'popover not found' };
            
            // Find all list elements that have text and are inside the media list
            const rows = Array.from(container.querySelectorAll('mat-list-item, [class*="media"], [class*="asset"]'))
                .map(el => ({
                    text: (el.innerText || '').trim(),
                    y: el.getBoundingClientRect().y,
                    height: el.getBoundingClientRect().height
                }))
                .filter(el => el.text.length > 0 && el.height > 0);
            return rows;
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Rows in popover:", json.dumps(res['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(get_popover_titles())
