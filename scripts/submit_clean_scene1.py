import asyncio
import json
import urllib.request
import websockets
import time

def get_ws_url():
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    pages = json.loads(req.read().decode())
    flow_page = next((p for p in pages if "flow.google.com" in p.get("url", "")), None)
    if not flow_page:
        raise RuntimeError("No Google Flow tab found on port 9222!")
    return flow_page["webSocketDebuggerUrl"]

CLEAN_PROMPT = (
    "Generate video in 720p resolution using Veo 3.1 - Fast model, 16:9 widescreen. "
    "Pristine modern cinematic video, crystal-clear ARRI Alexa LF cinematography, high dynamic range, sharp focus, 16:9 widescreen, clean frame borders, absolutely no vintage filter, no film grain, no noise, no blur. "
    "A 40-year-old handsome Caucasian man named Valeri with short textured dark-brown hair, neat light designer stubble, warm expressive hazel-gray eyes, small mole on cheek, wearing a stylish distressed brown leather jacket with relaxed collar over an olive-green button-up shirt and dark denim trousers, strictly NO glasses, mouth gently closed. "
    "He walks forward calmly down a modern clean illuminated evening city street along a river promenade, confident natural gait. "
    "Both hands are kept relaxed inside his jacket pockets at all times. Both hands completely inside pockets, holding absolutely nothing, no objects, no props, hands never touching face, hands never near head. "
    "Smooth steady cinematic camera dolly tracking forward. Crisp beautiful city light reflections on pavement, warm ambient shop lights. Clean borders, no edge codes, no text, no watermark."
)

async def main():
    ws_url = get_ws_url()
    print(f"Connecting to Flow tab: {ws_url}", flush=True)
    async with websockets.connect(ws_url) as ws:
        # Clear editor and focus
        focus_script = """(() => {
            const pm = document.querySelector('div.ProseMirror');
            if (!pm) return false;
            pm.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('delete', false, null);
            return true;
        })()"""
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': focus_script, 'returnByValue': True}}))
        await ws.recv()
        await asyncio.sleep(0.3)
        
        # Insert clean text
        await ws.send(json.dumps({
            'id': 2,
            'method': 'Input.insertText',
            'params': {'text': CLEAN_PROMPT}
        }))
        await ws.recv()
        await asyncio.sleep(0.8)
        
        # Click send button
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
        print('Send button click attempt:', res['result']['result']['value'])
        
        # Also simulate Enter key press inside ProseMirror
        await ws.send(json.dumps({'id': 4, 'method': 'Input.dispatchKeyEvent', 'params': {'type': 'keyDown', 'key': 'Enter', 'code': 'Enter', 'windowsVirtualKeyCode': 13}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 5, 'method': 'Input.dispatchKeyEvent', 'params': {'type': 'keyUp', 'key': 'Enter', 'code': 'Enter', 'windowsVirtualKeyCode': 13}}))
        await ws.recv()
        print("Prompt successfully dispatched to Google Flow!", flush=True)

if __name__ == '__main__':
    asyncio.run(main())
