import asyncio
import json
import urllib.request
import websockets
import base64

async def check_chat_bottom():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        scroll_script = """
        (() => {
            const chatContainers = Array.from(document.querySelectorAll('.chat-history, .message-list, [class*="chat-panel"], [class*="history"], [class*="thread"]'));
            chatContainers.forEach(c => {
                c.scrollTop = c.scrollHeight;
            });
            // Also window/body scroll
            window.scrollTo(0, document.body.scrollHeight);
            
            const messages = Array.from(document.querySelectorAll('.message, [class*="message"], .chat-bubble, [class*="bubble"]'))
                .map(m => (m.innerText || '').trim())
                .filter(t => t.length > 0);
            
            return {
                messagesCount: messages.length,
                lastMessages: messages.slice(-4)
            };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': scroll_script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Chat bottom:", json.dumps(res['result']['result']['value'], indent=2))

        await asyncio.sleep(1)
        await ws.send(json.dumps({'id': 2, 'method': 'Page.captureScreenshot'}))
        s_res = json.loads(await ws.recv())
        with open('chat_bottom_snap.png', 'wb') as sf:
            sf.write(base64.b64decode(s_res['result']['data']))
        print("Saved chat_bottom_snap.png")

if __name__ == '__main__':
    asyncio.run(check_chat_bottom())
