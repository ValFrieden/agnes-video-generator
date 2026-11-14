import asyncio
import json
import urllib.request
import websockets
import base64
import os

prompt_text = (
    "Generate an 8-second realistic video with Veo 3.1 - Fast using the attached image as the starting keyframe reference. "
    "CRITICAL PHYSICAL AND ATMOSPHERIC REALISM (HABOOB DENSITY CURRENT): "
    "A solitary man seen strictly from behind (Back-to-Camera, hooded canvas jacket, backpack, brown hair, absolutely NO visible face) stands firmly on a rocky desert plateau facing a monumental, towering wall of an advancing sandstorm (haboob). "
    "PHYSICAL DYNAMICS: The colossal wall of terracotta and dark ochre dust advances forward across the horizon as a massive turbulent rolling gravity current with billowing vortices and churning microburst clouds. "
    "ORGANIC ASYMMETRY: The dust clouds billow with natural chaotic turbulence, completely non-mirrored and irregular, with asymmetrical density and varying heights across the front. "
    "AERODYNAMICS ON SUBJECT: High-velocity turbulent storm winds whip through the scene. Fine desert sand particles and dust drift horizontally across the foreground. The fabric of the man's jacket, backpack straps, and strands of hair flutter naturally in the gale force gusts, while his body maintains a stoic, grounded stance against the wind. "
    "OPTICS & LIGHTING: Natural overcast atmospheric lighting, moody dark stormy sky above the dust wall, authentic Mie scattering with deep earthy umber and terracotta tones, completely matte dry particulate air, zero digital gloss, zero synthetic CGI plastic smoothing, shot on 35mm anamorphic prime lens, ARRI Alexa Mini LF, slow deliberate cinematic push-in camera movement."
)

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    print("Tab URL:", t["url"])

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Step 1: Click + button in prompt box
        print("Clicking + button in prompt box...")
        click_plus = """
        (() => {
            const promptBox = document.querySelector('.agent-panel-prompt-box');
            if (!promptBox) return { error: 'promptBox not found' };
            const addIcon = Array.from(promptBox.querySelectorAll('mat-icon')).find(i => (i.innerText || '').trim() === 'add');
            if (addIcon) {
                const btn = addIcon.closest('button');
                if (btn) {
                    btn.click();
                    return { success: true };
                }
            }
            return { error: 'add button not found' };
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_plus, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Plus clicked:", res['result']['result']['value'])
        await asyncio.sleep(1)

        # Step 2: Search for 'Traveler facing' in popover
        print("Filtering popover search...")
        filter_search = """
        (() => {
            const input = document.querySelector('.add-menu-popover-container input');
            if (!input) return { error: 'search input not found' };
            input.focus();
            input.value = 'Traveler facing';
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            return { success: true };
        })()
        """
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': filter_search, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Search filter set:", res['result']['result']['value'])
        await asyncio.sleep(1)

        # Step 3: Select item and click "Zum Prompt hinzufügen"
        print("Selecting media item and adding to prompt...")
        select_and_add = """
        (() => {
            const container = document.querySelector('.add-menu-popover-container');
            if (!container) return { error: 'popover not found' };
            
            // Find item with 'Traveler facing'
            const items = Array.from(container.querySelectorAll('mat-list-item, div, span'));
            const target = items.find(el => (el.innerText || '').trim().includes('Traveler facing'));
            if (!target) return { error: 'Traveler item not found in filtered list' };
            
            const li = target.closest('mat-list-item') || target;
            li.click();

            // Find "Zum Prompt hinzufügen"
            const addBtn = Array.from(container.querySelectorAll('button, span')).find(b => (b.innerText || '').trim() === 'Zum Prompt hinzufügen');
            if (addBtn) {
                const b = addBtn.closest('button') || addBtn;
                b.click();
                return { success: true, item: target.innerText.trim() };
            }
            return { error: 'Add button not found', item: target.innerText.trim() };
        })()
        """
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': select_and_add, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Select and add result:", res['result']['result']['value'])
        await asyncio.sleep(1.5)

        # Step 4: Verify chip in prompt box
        check_chip = """
        (() => {
            const promptBox = document.querySelector('.agent-panel-prompt-box');
            const chips = promptBox ? Array.from(promptBox.querySelectorAll('.chip-container, [aria-label*="Bildelement"], img')).length : 0;
            return { promptBoxFound: !!promptBox, chipsCount: chips };
        })()
        """
        await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': check_chip, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Chip check:", res['result']['result']['value'])

        # Step 5: Set prompt text
        print("Setting prompt text...")
        set_text = f"""
        (() => {{
            const box = document.querySelector('textarea, [contenteditable="true"]');
            if (!box) return {{ error: 'box not found' }};
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
        await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': set_text, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Set text:", res['result']['result']['value'])
        await asyncio.sleep(1)

        # Step 6: Find and click submit button
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
        await ws.send(json.dumps({'id': 6, 'method': 'Runtime.evaluate', 'params': {'expression': find_btn, 'returnByValue': True}}))
        b_res = json.loads(await ws.recv())
        btn_info = b_res['result']['result']['value']
        print("Submit button info:", btn_info)
        
        if not btn_info.get('found') or btn_info.get('disabled'):
            print("Submit button disabled or not found! Retrying...")
            await asyncio.sleep(1)

        print(f"Clicking submit at ({btn_info['x']}, {btn_info['y']})...")
        await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': btn_info['x'], 'y': btn_info['y'], 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': btn_info['x'], 'y': btn_info['y'], 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        print("Submit clicked successfully!")

        # Step 7: Watch for Genehmigen cost card (RULE 6: IMMEDIATELY CLICK)
        print("Watching for Genehmigen cost card confirmation...")
        approved = False
        for i in range(45):
            await asyncio.sleep(1)
            check_script = """
            (() => {
                const buttons = Array.from(document.querySelectorAll('button, .option-row, [role="button"]'));
                const genBtn = buttons.find(b => {
                    const txt = (b.innerText || '').trim();
                    return (txt.includes('Genehmigen') || txt.includes('Сгенерировать')) && !b.classList.contains('read-only') && !b.disabled;
                });
                
                if (genBtn) {
                    const rect = genBtn.getBoundingClientRect();
                    return {
                        found: true,
                        text: genBtn.innerText.trim(),
                        coords: { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 }
                    };
                }
                return { found: false };
            })()
            """
            await ws.send(json.dumps({'id': 100 + i, 'method': 'Runtime.evaluate', 'params': {'expression': check_script, 'returnByValue': True}}))
            res = json.loads(await ws.recv())
            val = res['result']['result']['value']
            
            if val.get('found') and not approved:
                print(f"[{i}s] Found Genehmigen button! Clicking at {val['coords']}...")
                c = val['coords']
                await ws.send(json.dumps({'id': 200, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1}}))
                await ws.recv()
                await ws.send(json.dumps({'id': 201, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1}}))
                await ws.recv()
                print("Genehmigen clicked successfully!")
                approved = True
                
                await asyncio.sleep(1)
                await ws.send(json.dumps({'id': 202, 'method': 'Page.captureScreenshot'}))
                s_res = json.loads(await ws.recv())
                with open('after_sandstorm_approval.png', 'wb') as sf:
                    sf.write(base64.b64decode(s_res['result']['data']))
                print("Saved after_sandstorm_approval.png")
                break
            else:
                if i % 3 == 0:
                    print(f"[{i}s] Waiting for Genehmigen card...")

if __name__ == '__main__':
    asyncio.run(main())
