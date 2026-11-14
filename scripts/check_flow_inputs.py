import asyncio
import json
import urllib.request
import websockets

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        script = """
        (() => {
            const inputs = Array.from(document.querySelectorAll('input[type="file"]')).map(i => ({
                id: i.id,
                className: i.className,
                accept: i.accept
            }));
            const dialogs = Array.from(document.querySelectorAll('[role="dialog"], [role="menu"], mat-dialog-container')).map(d => (d.innerText || '').slice(0, 100));
            return { inputs, dialogs };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print(json.dumps(res['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(check())
