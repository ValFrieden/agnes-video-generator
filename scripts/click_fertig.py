import asyncio
import json
import urllib.request
import websockets

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Click "Fertig"
        click_fertig = """
        (() => {
            const btn = document.querySelector('button[aria-label="Bearbeitung abgeschlossen"], button.done-button') || Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').trim() === 'Fertig');
            if (btn) {
                btn.click();
                return 'Clicked Fertig';
            }
            return 'Fertig not found';
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_fertig, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print(res['result']['result']['value'])

if __name__ == '__main__':
    asyncio.run(check())
