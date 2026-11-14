import asyncio
import json
import urllib.request
import websockets

natural_prompt = (
    "Authentic 35mm documentary photograph, raw unedited National Geographic photojournalism, shot on ARRI Alexa Mini LF, 35mm prime lens, f/4.0, natural maritime lighting. "
    "A lone male swimmer in the vast, deep, dark open ocean, photographed strictly from behind (Back-to-Camera, back of head with wet hair, bare wet shoulders, absolutely no face visible). "
    "Ahead of him in the cold, deep navy water, widely spaced apart, are EXACTLY TWO real adult tiger sharks swimming on the surface. "
    "One shark is far on the left side cruising away; the other shark is far on the right side cruising away. "
    "There is a massive wide expanse of empty open ocean between them, with completely separated natural wakes, zero intersection, zero overlapping. "
    "The ocean horizon is distinct, natural, and properly distanced under an overcast stormy maritime sky. "
    "Genuine ocean water physics, cold dark swells, subtle natural sea spray, authentic wet skin texture with water droplets. "
    "Utterly realistic, gritty documentary suspense, zero CGI, zero digital gloss, non-synthetic, authentic wildlife photography, natural optical depth of field, subtle film grain."
)

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Check prompt box and remove any existing chip if present
        clear_chip = """
        (() => {
            const cancelBtn = document.querySelector('button[aria-label="Bildelement"] mat-icon, .chip-container mat-icon');
            if (cancelBtn) {
                cancelBtn.closest('button').click();
                return 'Removed chip';
            }
            return 'No chip';
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': clear_chip, 'returnByValue': True}}))
        await ws.recv()

        # Set text in prompt box
        set_text = f"""
        (() => {{
            const box = document.querySelector('textarea, [contenteditable="true"]');
            if (!box) return {{ success: false, error: 'box not found' }};
            box.focus();
            if (box.tagName === 'TEXTAREA') {{
                box.value = {json.dumps(natural_prompt)};
                box.dispatchEvent(new Event('input', {{ bubbles: true }}));
                box.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }} else {{
                box.innerText = {json.dumps(natural_prompt)};
                box.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
            return {{ success: true, len: (box.value || box.innerText).length }};
        }})()
        """
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': set_text, 'returnByValue': True}}))
        res2 = json.loads(await ws.recv())
        print("Set prompt:", res2['result']['result']['value'])
        await asyncio.sleep(0.5)

        # Click submit button
        click_submit = """
        (() => {
            const btn = document.querySelector('button[aria-label="Generierung starten"], button.generate-icon-button, button.send-button');
            if (btn) {
                const r = btn.getBoundingClientRect();
                return { found: true, x: r.x + r.width / 2, y: r.y + r.height / 2 };
            }
            return { found: false };
        })()
        """
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': click_submit, 'returnByValue': True}}))
        res3 = json.loads(await ws.recv())
        btn_info = res3['result']['result']['value']
        print("Submit btn info:", btn_info)
        
        if btn_info.get('found'):
            cx, cy = btn_info['x'], btn_info['y']
            await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            print("Submitted natural prompt to Flow!")

if __name__ == '__main__':
    asyncio.run(main())
