import asyncio
import json
import urllib.request
import websockets
import base64

async def clean_prompt():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Step 1: Remove existing chip in prompt box
        remove_script = """
        (() => {
            const promptBox = document.querySelector('.agent-panel-prompt-box');
            if (promptBox) {
                // Find close or remove button
                const closeBtn = promptBox.querySelector('button[aria-label*="Entfernen"], button[aria-label*="löschen"], button[aria-label*="Delete"], button[aria-label*="Remove"]') ||
                                 Array.from(promptBox.querySelectorAll('mat-icon, span, button')).find(el => (el.innerText || '').trim() === 'close' || (el.innerText || '').trim() === 'cancel');
                if (closeBtn) {
                    const b = closeBtn.closest('button') || closeBtn;
                    b.click();
                    return { success: true, method: 'clicked closeBtn' };
                }
            }
            return { success: false, method: 'none' };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': remove_script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Remove chip result:", res['result']['result']['value'])

        # Fallback click coordinate (976, 835) if needed
        if not res['result']['result']['value'].get('success'):
            print("Dispatching mouse click at (976, 835)...")
            await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': 976, 'y': 835, 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': 976, 'y': 835, 'button': 'left', 'clickCount': 1}}))
            await ws.recv()

        await asyncio.sleep(0.5)

        # Close any open top-right menu by clicking neutral area
        await ws.send(json.dumps({'id': 20, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': 500, 'y': 500, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 21, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': 500, 'y': 500, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()

        await asyncio.sleep(0.5)

        # Screenshot
        await ws.send(json.dumps({'id': 30, 'method': 'Page.captureScreenshot'}))
        s_res = json.loads(await ws.recv())
        with open('clean_prompt_check.png', 'wb') as sf:
            sf.write(base64.b64decode(s_res['result']['data']))
        print("Saved clean_prompt_check.png")

if __name__ == '__main__':
    asyncio.run(clean_prompt())
