import asyncio
import json
import urllib.request
import websockets
import base64

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
    
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Step 1: Navigate to main project page cleanly
        project_url = 'https://flow.google.com/project/d7aa8d17-a219-4cf4-b840-832427562b58'
        print("1. Navigating to main project URL...")
        req_id = 1
        await ws.send(json.dumps({'id': req_id, 'method': 'Page.navigate', 'params': {'url': project_url}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id: break
        
        await asyncio.sleep(4)

        # Step 2: Click New Chat icon in chat header
        print("2. Starting fresh chat session...")
        click_new_chat = """
        (() => {
            const btn = document.querySelector('button[aria-label*="Neu"], button[aria-label*="New"]');
            if (btn) {
                btn.click();
                return 'Clicked new chat by aria';
            }
            const icons = Array.from(document.querySelectorAll('mat-icon'));
            const editIcon = icons.find(i => (i.innerText || '').trim() === 'edit_square');
            if (editIcon) {
                (editIcon.closest('button') || editIcon).click();
                return 'Clicked edit_square button';
            }
            return 'Not found';
        })()
        """
        req_id = 2
        await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': click_new_chat, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id:
                res_val = msg.get('result', {}).get('result', {}).get('value')
                print("New chat result:", res_val)
                break
        
        await asyncio.sleep(1.5)

        # Step 3: Open media popover by clicking '+' in prompt box
        print("3. Clicking + in prompt box...")
        click_plus = """
        (() => {
            const promptBox = document.querySelector('.agent-panel-prompt-box');
            if (!promptBox) return { error: 'promptBox not found' };
            const addIcon = Array.from(promptBox.querySelectorAll('mat-icon')).find(i => (i.innerText || '').trim() === 'add');
            if (addIcon) {
                addIcon.closest('button').click();
                return { success: true };
            }
            return { error: 'add button not found' };
        })()
        """
        req_id = 3
        await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': click_plus, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id:
                print("Plus click:", msg['result']['result']['value'])
                break
        
        await asyncio.sleep(1)

        # Step 4: Filter by 'Traveler facing'
        print("4. Filtering popover search...")
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
        req_id = 4
        await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': filter_search, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id: break
        
        await asyncio.sleep(1)

        # Step 5: Select item and click 'Zum Prompt hinzufügen'
        print("5. Selecting 'Traveler facing giant sandstorm'...")
        select_and_add = """
        (() => {
            const container = document.querySelector('.add-menu-popover-container');
            if (!container) return { error: 'popover not found' };
            
            const items = Array.from(container.querySelectorAll('mat-list-item, div, span'));
            const target = items.find(el => (el.innerText || '').trim().includes('Traveler facing giant sandstorm'));
            if (!target) return { error: 'Traveler item not found in filtered list' };
            
            (target.closest('mat-list-item') || target).click();

            const addBtn = Array.from(container.querySelectorAll('button, span')).find(b => (b.innerText || '').trim() === 'Zum Prompt hinzufügen');
            if (addBtn) {
                (addBtn.closest('button') || addBtn).click();
                return { success: true, item: target.innerText.trim() };
            }
            return { error: 'Add button not found', item: target.innerText.trim() };
        })()
        """
        req_id = 5
        await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': select_and_add, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id:
                print("Attach result:", msg['result']['result']['value'])
                break
        
        await asyncio.sleep(1)

        # Step 6: Insert prompt text
        print("6. Inserting prompt text...")
        insert_text = f"""
        (() => {{
            const box = document.querySelector('[contenteditable="true"]');
            if (!box) return {{ error: 'box not found' }};
            box.focus();
            document.execCommand('selectAll', false, null);
            const ok = document.execCommand('insertText', false, {json.dumps(prompt_text)});
            return {{ ok, textLen: box.innerText.length }};
        }})()
        """
        req_id = 6
        await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': insert_text, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id:
                print("Insert prompt result:", msg['result']['result']['value'])
                break
        
        await asyncio.sleep(1)

        # Step 7: Click Submit button
        print("7. Clicking Submit button...")
        click_submit = """
        (() => {
            const btn = document.querySelector('button[aria-label="Generierung starten"]');
            if (btn) {
                btn.click();
                return { success: true, disabled: btn.disabled };
            }
            return { success: false };
        })()
        """
        req_id = 7
        await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': click_submit, 'returnByValue': True}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id:
                print("Submit click result:", msg['result']['result']['value'])
                break
        
        # Step 8: Monitor and click Genehmigen (RULE 6)
        print("8. Monitoring for Genehmigen card...")
        approved = False
        for sec in range(45):
            await asyncio.sleep(1)
            
            check_gen = """
            (() => {
                const elements = Array.from(document.querySelectorAll('.option-row, button, span'));
                const gen = elements.find(el => {
                    const txt = (el.innerText || '').trim();
                    return (txt === 'Genehmigen' || txt === '✓ Genehmigen' || txt.includes('Genehmigen')) && 
                           !el.innerText.includes('immer') && 
                           !el.classList.contains('read-only');
                });
                if (gen) {
                    const target = gen.closest('.option-row') || gen.closest('button') || gen;
                    target.click();
                    return { found: true, text: target.innerText.trim() };
                }
                return { found: false };
            })()
            """
            req_id = 100 + sec
            await ws.send(json.dumps({'id': req_id, 'method': 'Runtime.evaluate', 'params': {'expression': check_gen, 'returnByValue': True}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get('id') == req_id:
                    res = msg['result']['result']['value']
                    break
            
            if res.get('found') and not approved:
                print(f"[{sec}s] Genehmigen card found and clicked! Result:", res)
                approved = True
                break
            else:
                if sec % 3 == 0:
                    print(f"[{sec}s] Waiting for Genehmigen...")

        await asyncio.sleep(2)
        # Capture screenshot
        req_id = 999
        await ws.send(json.dumps({'id': req_id, 'method': 'Page.captureScreenshot'}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == req_id:
                with open('clean_run_approved.png', 'wb') as f:
                    f.write(base64.b64decode(msg['result']['data']))
                print("Saved clean_run_approved.png")
                break

if __name__ == '__main__':
    asyncio.run(main())
