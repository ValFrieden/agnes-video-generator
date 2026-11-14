import asyncio
import json
import urllib.request
import websockets
import base64

async def check():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    print("Found tab:", t["url"])
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        await ws.send(json.dumps({'id': 1, 'method': 'Page.captureScreenshot'}))
        res = json.loads(await ws.recv())
        img_data = base64.b64decode(res['result']['data'])
        with open('live_flow_check.png', 'wb') as f:
            f.write(img_data)
        print('Screenshot saved: live_flow_check.png')
        
        info_script = """
        (() => {
            const promptBox = document.querySelector('textarea, [contenteditable="true"]');
            const chips = Array.from(document.querySelectorAll('.chip, .image-chip, [class*="chip"]')).map(c => c.innerText);
            const cards = Array.from(document.querySelectorAll('div, p, span'))
                .filter(el => el.innerText && el.innerText.trim().length > 0 && el.children.length === 0)
                .map(el => el.innerText.trim())
                .slice(-12);
            return {
                promptVal: promptBox ? (promptBox.value || promptBox.innerText) : null,
                chips,
                lastTexts: cards
            };
        })()
        """
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': info_script, 'returnByValue': True}}))
        info = json.loads(await ws.recv())
        print('Page info:', json.dumps(info['result']['result']['value'], ensure_ascii=False, indent=2))

if __name__ == '__main__':
    asyncio.run(check())
