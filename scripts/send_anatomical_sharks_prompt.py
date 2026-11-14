import asyncio
import json
import urllib.request
import websockets

anatomical_prompt = (
    "Authentic 35mm documentary photograph, raw unedited National Geographic maritime photojournalism, shot on ARRI Alexa Mini LF, 35mm prime lens, natural overcast maritime light. "
    "A lone male swimmer in the vast, deep, dark open sea, photographed strictly from behind (Back-to-Camera, back of head with wet hair, bare wet shoulders, absolutely no face visible). "
    "Ahead of him in the cold, deep dark ocean water, widely separated from each other, are EXACTLY TWO real adult sharks swimming near the surface. "
    "CRITICAL BIOLOGY: ONLY the sharp triangular dorsal fins break the water surface, slicing through the sea with clean V-shaped surface wakes. "
    "Their entire shark bodies are 100% submerged deep beneath the water line, visible only as subtle dark murky silhouettes swimming under the waves. "
    "Absolutely NO shark torso above water, NO exposed shark backs. "
    "One dorsal fin is far on the left side cruising away; the other dorsal fin is far on the right side cruising away. "
    "There is a huge, wide empty expanse of open dark ocean between them with zero overlap. "
    "The ocean horizon is a clear, sharp, distant straight line with natural atmospheric perspective under a moody overcast sky. "
    "Utterly realistic, gritty documentary suspense, zero CGI, zero digital gloss, non-synthetic, natural optical depth of field."
)

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Clear chip
        clear_chip = """
        (() => {
            const cancelBtn = document.querySelector('button[aria-label="Bildelement"] mat-icon, .chip-container mat-icon');
            if (cancelBtn) { cancelBtn.closest('button').click(); return 'Removed chip'; }
            return 'No chip';
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': clear_chip, 'returnByValue': True}}))
        await ws.recv()

        # Set prompt text
        set_text = f"""
        (() => {{
            const box = document.querySelector('textarea, [contenteditable="true"]');
            if (!box) return {{ success: false }};
            box.focus();
            if (box.tagName === 'TEXTAREA') {{
                box.value = {json.dumps(anatomical_prompt)};
                box.dispatchEvent(new Event('input', {{ bubbles: true }}));
                box.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }} else {{
                box.innerText = {json.dumps(anatomical_prompt)};
                box.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
            return {{ success: true }};
        }})()
        """
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': set_text, 'returnByValue': True}}))
        await ws.recv()
        await asyncio.sleep(0.5)

        # Click submit
        click_submit = """
        (() => {
            const btn = document.querySelector('button[aria-label="Generierung starten"], button.generate-icon-button');
            if (btn) {
                const r = btn.getBoundingClientRect();
                return { found: true, x: r.x + r.width / 2, y: r.y + r.height / 2 };
            }
            return { found: false };
        })()
        """
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': click_submit, 'returnByValue': True}}))
        res3 = json.loads(await ws.recv())
        btn = res3['result']['result']['value']
        if btn.get('found'):
            await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': btn['x'], 'y': btn['y'], 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': btn['x'], 'y': btn['y'], 'button': 'left', 'clickCount': 1}}))
            await ws.recv()
            print("Submitted anatomically correct prompt!")

if __name__ == '__main__':
    asyncio.run(main())
