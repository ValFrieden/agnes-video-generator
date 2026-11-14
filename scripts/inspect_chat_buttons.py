import asyncio
import json
import urllib.request
import websockets
import base64

async def inspect_chat_buttons():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        expr = """
        (() => {
            const promptBox = document.querySelector('.agent-panel-prompt-box');
            const btns = Array.from(promptBox.querySelectorAll('button')).map(b => {
                const r = b.getBoundingClientRect();
                return {
                    text: b.innerText.trim(),
                    aria: b.getAttribute('aria-label'),
                    disabled: b.disabled,
                    x: r.x + r.width / 2,
                    y: r.y + r.height / 2
                };
            });

            // Chat header buttons (like new chat)
            const header = document.querySelector('.agent-panel-header, [class*="header"]');
            const headerBtns = header ? Array.from(header.querySelectorAll('button, a')).map(b => {
                const r = b.getBoundingClientRect();
                return {
                    text: b.innerText.trim(),
                    aria: b.getAttribute('aria-label'),
                    x: r.x + r.width / 2,
                    y: r.y + r.height / 2
                };
            }) : [];

            return {
                promptBtns: btns,
                headerBtns
            };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Buttons info:", json.dumps(res['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(inspect_chat_buttons())
