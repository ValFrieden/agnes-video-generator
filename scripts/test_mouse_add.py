import asyncio
import json
import urllib.request
import websockets
import base64

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Click via mouse dispatch at 1599, 900
        await ws.send(json.dumps({'id': 1, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': 1599, 'y': 900, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 2, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': 1599, 'y': 900, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        
        await asyncio.sleep(1)
        
        # Take screenshot
        await ws.send(json.dumps({'id': 3, 'method': 'Page.captureScreenshot'}))
        res = json.loads(await ws.recv())
        img_data = base64.b64decode(res['result']['data'])
        with open('after_add_click.png', 'wb') as f:
            f.write(img_data)
        print('Saved after_add_click.png')

        # Check DOM overlays
        script = """
        (() => {
            const overlays = Array.from(document.querySelectorAll('.cdk-overlay-container *, .mat-mdc-menu-panel *, [class*="popup"], [class*="dialog"], [class*="menu"]'))
                .filter(el => el.innerText && el.innerText.trim().length > 0 && el.children.length === 0)
                .map(el => ({ tag: el.tagName, text: el.innerText.trim(), class: el.className }));
            return overlays;
        })()
        """
        await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        d_res = json.loads(await ws.recv())
        print("Overlays:", json.dumps(d_res['result']['result']['value'], ensure_ascii=False, indent=2))

if __name__ == '__main__':
    asyncio.run(main())
