import asyncio
import json
import urllib.request
import websockets

def get_ws_url():
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    pages = json.loads(req.read().decode())
    flow_page = next((p for p in pages if "flow.google.com" in p.get("url", "")), None)
    return flow_page["webSocketDebuggerUrl"]

PROMPT = (
    "Generate a 720p 16:9 video from this image using Veo 3.1 - Fast. "
    "The man walks forward calmly down the modern illuminated evening river promenade, natural confident walk. "
    "Steady cinematic camera dolly tracking slowly forward. "
    "Pristine crystal-clear ARRI Alexa LF cinematography, high dynamic range, sharp focus. "
    "Hands kept relaxed inside jacket pockets at all times. "
    "Clean borders, no vintage filter, no film grain, no noise, no watermark."
)

async def submit_image_prompt():
    ws_url = get_ws_url()
    async with websockets.connect(ws_url) as ws:
        # Focus ProseMirror and type text
        focus_script = """(() => {
            const pm = document.querySelector('div.ProseMirror');
            if (!pm) return false;
            pm.focus();
            return true;
        })()"""
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': focus_script, 'returnByValue': True}}))
        print("Focused PM:", json.loads(await ws.recv())['result']['result']['value'])
        await asyncio.sleep(0.3)

        # Type prompt text
        await ws.send(json.dumps({
            'id': 2,
            'method': 'Input.insertText',
            'params': {'text': PROMPT}
        }))
        await ws.recv()
        await asyncio.sleep(0.8)

        # Click arrow_forward button
        click_script = """(() => {
            const btn = document.querySelector('button[aria-label*="Generierung starten"], button.generate-icon-button') || Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('arrow_forward'));
            if (btn && !btn.disabled) {
                btn.click();
                return { success: true, method: 'click' };
            }
            return { success: false, reason: btn ? 'disabled' : 'not_found' };
        })()"""
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': click_script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Send button clicked:", res['result']['result']['value'])

        # Press Enter just in case
        await ws.send(json.dumps({'id': 4, 'method': 'Input.dispatchKeyEvent', 'params': {'type': 'keyDown', 'key': 'Enter', 'code': 'Enter', 'windowsVirtualKeyCode': 13}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 5, 'method': 'Input.dispatchKeyEvent', 'params': {'type': 'keyUp', 'key': 'Enter', 'code': 'Enter', 'windowsVirtualKeyCode': 13}}))
        await ws.recv()
        print("Dispatched to Veo!")

if __name__ == '__main__':
    asyncio.run(submit_image_prompt())
