import asyncio
import json
import urllib.request
import websockets

async def check_chat_input():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        expr = """
        (() => {
            const inputContainer = document.querySelector('.chat-input, .input-container, [class*="prompt-box"], [class*="chat-input"]') ||
                                   document.querySelector('textarea, [contenteditable="true"]').closest('div[class*="container"], form, div');
            
            const chips = inputContainer ? Array.from(inputContainer.querySelectorAll('img, [role="img"], .chip, [class*="chip"]')).map(el => ({
                tag: el.tagName,
                src: el.src,
                text: el.innerText
            })) : [];

            return {
                containerClass: inputContainer ? inputContainer.className : null,
                chips
            };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Chat input container:", json.dumps(res['result']['result']['value'], indent=2))

if __name__ == '__main__':
    asyncio.run(check_chat_input())
