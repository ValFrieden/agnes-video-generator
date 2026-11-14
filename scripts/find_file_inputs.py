import asyncio
import json
import urllib.request
import websockets

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl']) as ws:
        script = """
        (() => {
            const inputs = Array.from(document.querySelectorAll('input[type="file"]')).map(inp => ({
                id: inp.id,
                name: inp.name,
                accept: inp.accept,
                multiple: inp.multiple,
                className: inp.className,
                parentElement: inp.parentElement ? inp.parentElement.tagName : null
            }));
            return inputs;
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print('File inputs:', res['result']['result']['value'])

if __name__ == '__main__':
    asyncio.run(check())
