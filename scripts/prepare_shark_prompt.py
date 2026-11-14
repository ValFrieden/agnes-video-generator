import asyncio
import json
import urllib.request
import websockets

prompt_text = (
    "Generate an 8-second realistic video with Veo 3.1 - Fast using the attached image as the starting keyframe reference. "
    "SURFACE WATER ONLY. Camera strictly above water surface, high-angle overhead view looking down at the turquoise ocean surface. "
    "Male swimmer floating calmly on top of the water wearing swim trunks, seen strictly from behind (Back-to-Camera, no face). "
    "Four large tiger sharks swimming peacefully in a circle around him on the water surface, their dorsal fins cutting the water surface. "
    "Natural sunlight, crystal transparent water caustics, cinematic documentary realism. "
    "Absolutely NO scuba gear, NO diving suit, NO flippers, NO oxygen tanks, NO underwater camera."
)

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Set text in prompt box
        set_text_script = f"""
        (() => {{
            const box = document.querySelector('textarea, [contenteditable="true"]');
            if (!box) return {{ success: false, error: 'box not found' }};
            box.focus();
            if (box.tagName === 'TEXTAREA') {{
                box.value = {json.dumps(prompt_text)};
                box.dispatchEvent(new Event('input', {{ bubbles: true }}));
                box.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }} else {{
                box.innerText = {json.dumps(prompt_text)};
                box.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
            return {{ success: true, textLen: (box.value || box.innerText).length }};
        }})()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': set_text_script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Set text result:", res['result']['result']['value'])
        await asyncio.sleep(0.5)

        # Find submit button
        find_btn = """
        (() => {
            const btn = document.querySelector('button[aria-label="Generierung starten"], button.generate-icon-button, button.send-button') ||
                        Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('arrow_forward') || b.getAttribute('aria-label') === 'Generierung starten');
            if (btn) {
                const r = btn.getBoundingClientRect();
                return {
                    found: true,
                    aria: btn.getAttribute('aria-label'),
                    class: btn.className,
                    disabled: btn.disabled,
                    x: r.x + r.width / 2,
                    y: r.y + r.height / 2
                };
            }
            return { found: false };
        })()
        """
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': find_btn, 'returnByValue': True}}))
        b_res = json.loads(await ws.recv())
        print("Submit button:", b_res['result']['result']['value'])

if __name__ == '__main__':
    asyncio.run(main())
