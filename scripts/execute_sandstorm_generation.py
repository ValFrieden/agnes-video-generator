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
        # Step 1: Click + button in prompt box to open media popover
        print("1. Clicking + button in prompt box...")
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
        print("2. Searching for 'Traveler facing' in popover...")
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
        print("Search filter:", res['result']['result']['value'])
        await asyncio.sleep(1)

        # Step 3: Select item and click "Zum Prompt hinzufügen"
        print("3. Selecting 'Traveler facing giant sandstorm' and clicking 'Zum Prompt hinzufügen'...")
        select_and_add = """
        (() => {
            const container = document.querySelector('.add-menu-popover-container');
            if (!container) return { error: 'popover not found' };
            
            const items = Array.from(container.querySelectorAll('mat-list-item, div, span'));
            const target = items.find(el => (el.innerText || '').trim().includes('Traveler facing giant sandstorm'));
            if (!target) return { error: 'Traveler item not found in filtered list' };
            
            const li = target.closest('mat-list-item') || target;
            li.click();

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
        print("Select & Add result:", res['result']['result']['value'])
        await asyncio.sleep(1)

        # Step 4: Insert the complete prompt text into the contenteditable box
        print("4. Inserting prompt text...")
        insert_prompt = f"""
        (() => {{
            const box = document.querySelector('[contenteditable="true"]');
            if (!box) return {{ error: 'box not found' }};
            box.focus();
            document.execCommand('selectAll', false, null);
            const ok = document.execCommand('insertText', false, {json.dumps(prompt_text)});
            return {{ ok, textLen: box.innerText.length }};
        }})()
        """
        await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': insert_prompt, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Insert prompt result:", res['result']['result']['value'])
        await asyncio.sleep(1)

        # Step 5: Check submit button coordinates and disabled state
        print("5. Finding submit button...")
        find_submit = """
        (() => {
            const submitBtn = document.querySelector('button[aria-label="Generierung starten"]');
            if (!submitBtn) return { error: 'submitBtn not found' };
            const r = submitBtn.getBoundingClientRect();
            return {
                disabled: submitBtn.disabled,
                x: r.x + r.width / 2,
                y: r.y + r.height / 2
            };
        })()
        """
        await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': find_submit, 'returnByValue': True}}))
        s_info = (json.loads(await ws.recv()))['result']['result']['value']
        print("Submit button info:", s_info)

        # Dispatch click
        cx, cy = s_info['x'], s_info['y']
        print(f"Clicking submit button at ({cx}, {cy})...")
        await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': cx, 'y': cy, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        print("Submit button clicked!")

        # Step 6: Watch for Genehmigen cost card (RULE 6: IMMEDIATELY CLICK)
        print("6. Monitoring for Genehmigen card (60s budget)...")
        approved = False
        for sec in range(60):
            await asyncio.sleep(1)
            
            check_gen = """
            (() => {
                const buttons = Array.from(document.querySelectorAll('button, .option-row, [role="button"], div, span'));
                const gen = buttons.find(el => {
                    const txt = (el.innerText || '').trim();
                    return (txt === 'Genehmigen' || txt === '✓ Genehmigen' || txt.includes('Genehmigen')) && !el.classList.contains('read-only') && !el.innerText.includes('immer');
                });
                if (gen) {
                    const target = gen.closest('.option-row') || gen.closest('button') || gen;
                    target.scrollIntoView({ block: 'center' });
                    const r = target.getBoundingClientRect();
                    return {
                        found: true,
                        text: target.innerText.trim(),
                        coords: { x: r.x + r.width / 2, y: r.y + r.height / 2 }
                    };
                }
                return { found: false };
            })()
            """
            await ws.send(json.dumps({'id': 100 + sec, 'method': 'Runtime.evaluate', 'params': {'expression': check_gen, 'returnByValue': True}}))
            g_res = json.loads(await ws.recv())
            g_val = g_res['result']['result']['value']
            
            if g_val.get('found') and not approved:
                gc = g_val['coords']
                print(f"[{sec}s] Genehmigen card found! Clicking at ({gc['x']}, {gc['y']})...")
                await ws.send(json.dumps({'id': 200, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': gc['x'], 'y': gc['y'], 'button': 'left', 'clickCount': 1}}))
                await ws.recv()
                await ws.send(json.dumps({'id': 201, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': gc['x'], 'y': gc['y'], 'button': 'left', 'clickCount': 1}}))
                await ws.recv()
                print("Genehmigen clicked successfully!")
                approved = True
                
                await asyncio.sleep(1.5)
                await ws.send(json.dumps({'id': 202, 'method': 'Page.captureScreenshot'}))
                s_res = json.loads(await ws.recv())
                with open('after_sandstorm_gen_approved.png', 'wb') as sf:
                    sf.write(base64.b64decode(s_res['result']['data']))
                print("Saved after_sandstorm_gen_approved.png")
                break
            else:
                if sec % 3 == 0:
                    print(f"[{sec}s] Waiting for Genehmigen card...")

if __name__ == '__main__':
    asyncio.run(main())
