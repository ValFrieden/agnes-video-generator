import asyncio
import json
import urllib.request
import websockets
import base64
import os
import time

prompt_text = (
    "Generate an 8-second realistic video with Veo 3.1 - Fast using the attached image as the starting keyframe reference. "
    "CRITICAL PHYSICAL AND BIOLOGICAL REALISM: "
    "The camera is positioned directly behind the swimmer in the water, tracking slightly forward with gentle natural ocean swells under a moody overcast sky. "
    "The solitary swimmer is seen strictly from behind (Back-to-Camera, bare wet shoulders, wet hair, absolutely no face). "
    "Ahead of him in the dark ocean water are EXACTLY TWO adult sharks swimming calmly at the surface, widely separated on the left and right flanks. "
    "SURFACE REALITY: ONLY their sharp triangular dorsal fins break the water surface, creating subtle V-shaped wakes. Their entire shark bodies remain 100% submerged deep beneath the waves, visible only as vague dark silhouettes under the water. Absolutely NO shark backs or torsos out of water. "
    "ZERO INTERSECTION: The two sharks swim along parallel or gently diverging trajectories far away from each other. They DO NOT cross paths, they DO NOT overlap, and they DO NOT swim through each other. "
    "Authentic 35mm documentary realism, ARRI Alexa, cold overcast sea lighting, natural distant horizon line, zero CGI gloss, non-synthetic, slow cinematic pacing."
)

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    print("Tab URL:", t["url"])

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Step 1: Set prompt text
        print("Setting prompt text...")
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
        await asyncio.sleep(1)

        # Step 2: Click submit button
        print("Finding submit button...")
        find_btn = """
        (() => {
            const btn = document.querySelector('button[aria-label="Generierung starten"], button.generate-icon-button, button.send-button') ||
                        Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('arrow_forward') || b.getAttribute('aria-label') === 'Generierung starten');
            if (btn) {
                const r = btn.getBoundingClientRect();
                return {
                    found: true,
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
        btn_info = b_res['result']['result']['value']
        print("Submit button info:", btn_info)
        
        if not btn_info.get('found'):
            print("Error: submit button not found!")
            return

        print(f"Clicking submit at ({btn_info['x']}, {btn_info['y']})...")
        await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': btn_info['x'], 'y': btn_info['y'], 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': btn_info['x'], 'y': btn_info['y'], 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        print("Submit clicked successfully!")

        # Step 3: Continuously poll for Genehmigen button
        print("Watching for Genehmigen / cost card confirmation...")
        approved = False
        for i in range(60):
            await asyncio.sleep(1)
            
            check_script = """
            (() => {
                const buttons = Array.from(document.querySelectorAll('button, .option-row, [role="button"]'));
                const genBtn = buttons.find(b => {
                    const txt = (b.innerText || '').trim();
                    return (txt.includes('Genehmigen') || txt.includes('Сгенерировать')) && !b.classList.contains('read-only') && !b.disabled;
                });
                
                const texts = Array.from(document.querySelectorAll('div, p, span'))
                    .filter(el => el.innerText && el.innerText.trim().length > 0 && el.children.length === 0)
                    .map(el => el.innerText.trim())
                    .slice(-8);

                if (genBtn) {
                    const rect = genBtn.getBoundingClientRect();
                    return {
                        found: true,
                        text: genBtn.innerText.trim(),
                        coords: { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 },
                        texts
                    };
                }
                return { found: false, texts };
            })()
            """
            await ws.send(json.dumps({'id': 100 + i, 'method': 'Runtime.evaluate', 'params': {'expression': check_script, 'returnByValue': True}}))
            res = json.loads(await ws.recv())
            val = res['result']['result']['value']
            
            if val.get('found') and not approved:
                print(f"[{i}s] Found Genehmigen button! Clicking at {val['coords']}...")
                c = val['coords']
                # Click Genehmigen
                await ws.send(json.dumps({'id': 200, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1}}))
                await ws.recv()
                await ws.send(json.dumps({'id': 201, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1}}))
                await ws.recv()
                print("Genehmigen clicked!")
                approved = True
                
                # Take screenshot
                await asyncio.sleep(1)
                await ws.send(json.dumps({'id': 202, 'method': 'Page.captureScreenshot'}))
                s_res = json.loads(await ws.recv())
                with open('after_approval_sharks_v2.png', 'wb') as sf:
                    sf.write(base64.b64decode(s_res['result']['data']))
                print("Saved after_approval_sharks_v2.png")
                break
            else:
                if i % 3 == 0:
                    print(f"[{i}s] Waiting for card... texts: {val.get('texts', [])[-3:]}")

        if not approved:
            print("Warning: Genehmigen button was not found within 60s.")
            return

        # Step 4: Monitor generation
        print("Monitoring video generation progress...")
        for p in range(120): # up to 4 minutes
            await asyncio.sleep(2)
            progress_script = """
            (() => {
                const textNodes = Array.from(document.querySelectorAll('div, span, p'))
                    .map(el => el.innerText ? el.innerText.trim() : '')
                    .filter(t => t.includes('%') || t.includes('Processing') || t.includes('processing') || t.includes('Generating') || t.includes('ready'));
                
                return { texts: textNodes.slice(-5) };
            })()
            """
            await ws.send(json.dumps({'id': 300 + p, 'method': 'Runtime.evaluate', 'params': {'expression': progress_script, 'returnByValue': True}}))
            p_res = json.loads(await ws.recv())
            pval = p_res['result']['result']['value']
            
            if p % 5 == 0:
                print(f"[{p*2}s progress] texts: {pval.get('texts')}")
                
            last_texts = pval.get('texts', [])
            if any('100%' in t for t in last_texts) or (p > 15 and not any('%' in t for t in last_texts)):
                await ws.send(json.dumps({'id': 400, 'method': 'Page.captureScreenshot'}))
                sc_res = json.loads(await ws.recv())
                with open('video_generation_finished_v2.png', 'wb') as vf:
                    vf.write(base64.b64decode(sc_res['result']['data']))
                print("Generation complete! Saved video_generation_finished_v2.png")
                break

if __name__ == '__main__':
    asyncio.run(main())
