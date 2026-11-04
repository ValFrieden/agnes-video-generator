import asyncio
import websockets
import json
import urllib.request

async def inspect():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read().decode())
    ws_url = [t for t in tabs if 'flow.google.com' in t.get('url', '')][0]['webSocketDebuggerUrl']
    async with websockets.connect(ws_url) as ws:
        expr = """
        (() => {
            const chatVid = document.querySelector('flow-chat-message video, .chat-message video, flow-chat-item video');
            const mediaTile = document.querySelector('flow-chat-message flow-media-tile, flow-chat-item flow-media-tile, .media-tile');
            const btns = Array.from(document.querySelectorAll('button')).map(b => ({
                text: b.innerText.trim(),
                aria: b.getAttribute('aria-label') || ''
            })).filter(b => b.text || b.aria);
            return {
                hasChatVid: !!chatVid,
                hasMediaTile: !!mediaTile,
                chatVidSrc: chatVid ? chatVid.src : '',
                buttons: btns.slice(0, 15)
            };
        })()
        """
        msg = {'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}
        await ws.send(json.dumps(msg))
        while True:
            r = json.loads(await ws.recv())
            if r.get('id') == 1:
                print('Inspect result:', json.dumps(r['result']['result']['value'], indent=2, ensure_ascii=False))
                break

asyncio.run(inspect())
