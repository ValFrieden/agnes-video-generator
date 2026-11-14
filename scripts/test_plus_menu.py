import asyncio
import json
import urllib.request
import websockets
import base64

async def test_plus():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Click the + button inside the prompt box at bottom right
        # In the screenshot, the prompt box is at x: 820..980, y: 920..960
        # Let's find the button with '+' or 'add' or aria-label
        find_plus = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button'))
                .filter(b => {
                    const r = b.getBoundingClientRect();
                    return r.y > 800 && r.x > 800 && (b.innerText || '').includes('add') || b.getAttribute('aria-label')?.includes('hinzufügen') || (b.innerText || '').includes('+');
                });
            if (btns.length > 0) {
                const b = btns[0];
                const r = b.getBoundingClientRect();
                b.click();
                return { success: true, text: b.innerText, x: r.x + r.width/2, y: r.y + r.height/2 };
            }
            // fallback by coordinate
            return { success: false, msg: 'button not found by text' };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': find_plus, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Find plus:", res['result']['result']['value'])
        await asyncio.sleep(1)

        await ws.send(json.dumps({'id': 2, 'method': 'Page.captureScreenshot'}))
        s_res = json.loads(await ws.recv())
        with open('after_plus_click.png', 'wb') as f:
            f.write(base64.b64decode(s_res['result']['data']))
        print("Saved after_plus_click.png")

if __name__ == '__main__':
    asyncio.run(test_plus())
