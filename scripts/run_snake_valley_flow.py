import asyncio
import json
import urllib.request
import websockets
import sys
import os
import shutil
from PIL import Image

BRAIN_DIR = "C:/Users/Valeri/.gemini/antigravity/brain/5206faf6-a4af-482f-ad2b-3902d5efa61a"
CLIPS_DIR = "d:/Projects/VideoGenerator/nikogda_ne_boyus_frames/clips"
os.makedirs(CLIPS_DIR, exist_ok=True)

prompt_text = (
    "Generate an 8-second realistic video with Veo 3.1 - Fast using the attached image as the starting keyframe reference. "
    "CRITICAL PHYSICAL AND BIOLOGICAL REALISM (SNAKE LOCOMOTION & CANYON DYNAMICS): "
    "A solitary man seen strictly from behind (Back-to-Camera, dark graphite tactical overshirt, dark cargo pants, distressed boots, brown textured hair, absolutely NO visible face) walks calmly and steadily forward into a deep red sandstone desert canyon. "
    "SNAKE BIOMECHANICS & KINEMATICS: "
    "The wild desert rattlesnakes and vipers on the stony canyon floor move with authentic lateral undulation (serpentine locomotion). S-shaped muscle contraction waves travel smoothly from head to tail, pushing naturally against pebbles and rock edges. 100% of the snakes' bodies stay in continuous physical contact with the rough terrain, hugging the contours of the ground. No floating, no sliding like ice, no plastic gloss, completely matte keeled scales with fine desert dust. "
    "STRICT ORGANIC ASYMMETRY: "
    "The snakes are distributed in completely irregular, non-mirrored positions across different depths and angles. They slither away from the man's walking path at different speeds and asynchronous phases toward rock crevices and shadowed canyon walls. "
    "ATMOSPHERE & CINEMATOGRAPHY: "
    "Low-angle cinematic tracking shot moving smoothly forward behind the man at waist level. Warm golden hour sunlight slicing through canyon walls, casting long soft shadows. Subtle airborne dust motes raised by his boots. Photorealistic 35mm film texture, ARRI Alexa optical rendering, anti-slop, zero rubbery CGI distortion."
)

async def main():
    print("Connecting to Chrome on port 9222...", flush=True)
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Step 1: Start fresh chat
        print("1. Starting fresh chat session...", flush=True)
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
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': click_new_chat, 'returnByValue': True}}))
        for _ in range(10):
            msg = json.loads(await ws.recv())
            if msg.get('id') == 1:
                print("New chat result:", msg.get('result', {}).get('result', {}).get('value'), flush=True)
                break
        
        await asyncio.sleep(2)

        # Step 2: Open add menu
        print("2. Opening + menu in prompt box...", flush=True)
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
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': click_plus, 'returnByValue': True}}))
        for _ in range(10):
            msg = json.loads(await ws.recv())
            if msg.get('id') == 2:
                print("Plus click result:", msg.get('result', {}).get('result', {}).get('value'), flush=True)
                break
        
        await asyncio.sleep(1.5)

        # Step 3: Search and select snake_valley_option2
        print("3. Filtering popover for snake_valley_option2...", flush=True)
        filter_search = """
        (() => {
            const input = document.querySelector('.add-menu-popover-container input.search-input');
            if (!input) return { error: 'search input not found' };
            input.focus();
            input.value = 'snake_valley';
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            return { success: true };
        })()
        """
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': filter_search, 'returnByValue': True}}))
        for _ in range(10):
            msg = json.loads(await ws.recv())
            if msg.get('id') == 3:
                print("Search filter result:", msg.get('result', {}).get('result', {}).get('value'), flush=True)
                break
        
        await asyncio.sleep(1.5)

        # Step 4: Click first filtered item and then 'Zum Prompt hinzufügen'
        print("4. Selecting asset and clicking 'Zum Prompt hinzufügen'...", flush=True)
        select_and_add = """
        (() => {
            const popover = document.querySelector('.add-menu-popover-container');
            if (!popover) return { error: 'No popover' };
            
            // Find item with snake_valley
            const items = Array.from(popover.querySelectorAll('.asset-list-item, [class*="asset-item"], .media-item, [role="option"], .asset-card'));
            const target = items.find(el => (el.innerText || '').includes('snake_valley')) || items[0];
            if (target) {
                target.click();
            }
            
            // Find 'Zum Prompt hinzufügen' button
            const addBtn = Array.from(popover.querySelectorAll('button')).find(b => (b.innerText || '').includes('Zum Prompt hinzuf') || (b.innerText || '').includes('hinzufügen') || (b.innerText || '').includes('Add'));
            if (addBtn) {
                addBtn.click();
                return { success: true, targetText: target ? target.innerText.slice(0, 30) : 'none' };
            }
            return { error: 'Add button not found', targetFound: !!target };
        })()
        """
        await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': select_and_add, 'returnByValue': True}}))
        for _ in range(10):
            msg = json.loads(await ws.recv())
            if msg.get('id') == 4:
                print("Asset add result:", msg.get('result', {}).get('result', {}).get('value'), flush=True)
                break
        
        await asyncio.sleep(1.5)

        # Step 5: Insert prompt text
        print("5. Inserting prompt text...", flush=True)
        insert_prompt_js = f"""
        (() => {{
            const editor = document.querySelector('div[contenteditable="true"]');
            if (!editor) return {{ error: 'contenteditable editor not found' }};
            editor.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('insertText', false, {json.dumps(prompt_text)});
            return {{
                success: true,
                textLength: editor.innerText.length,
                preview: editor.innerText.slice(0, 50)
            }};
        }})()
        """
        await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': insert_prompt_js, 'returnByValue': True}}))
        for _ in range(10):
            msg = json.loads(await ws.recv())
            if msg.get('id') == 5:
                print("Insert prompt result:", msg.get('result', {}).get('result', {}).get('value'), flush=True)
                break
        
        await asyncio.sleep(1.5)

        # Step 6: Click submit button (Generierung starten)
        print("6. Clicking Generierung starten...", flush=True)
        click_submit = """
        (() => {
            const btn = document.querySelector('button[aria-label="Generierung starten"], button[aria-label="Prompt senden"], button[aria-label="Generate"]');
            if (btn) {
                btn.click();
                return 'Clicked submit button by aria';
            }
            // fallback: find send/arrow icon button
            const icons = Array.from(document.querySelectorAll('.agent-panel-prompt-box mat-icon'));
            const sendIcon = icons.find(i => ['arrow_upward', 'send', 'arrow_forward'].includes((i.innerText || '').trim()));
            if (sendIcon) {
                sendIcon.closest('button').click();
                return 'Clicked sendIcon button';
            }
            return 'Submit button not found';
        })()
        """
        await ws.send(json.dumps({'id': 6, 'method': 'Runtime.evaluate', 'params': {'expression': click_submit, 'returnByValue': True}}))
        for _ in range(10):
            msg = json.loads(await ws.recv())
            if msg.get('id') == 6:
                print("Submit result:", msg.get('result', {}).get('result', {}).get('value'), flush=True)
                break

        # Step 7: Intercept and immediately click Genehmigen (Iron Rule 6)
        print("7. Polling for cost confirmation card and clicking Genehmigen...", flush=True)
        approved = False
        click_approve_js = """
        (() => {
            const allElements = Array.from(document.querySelectorAll('button, div.option-row, div[role="button"], span'));
            const target = allElements.find(el => {
                const txt = (el.innerText || '').trim();
                return txt === 'Genehmigen' || txt === 'Сгенерировать' || txt.startsWith('Genehmigen') || txt.startsWith('Bestätigen') || txt === 'Approve';
            });
            if (target) {
                (target.closest('button') || target.closest('div.option-row') || target).click();
                return { success: true, text: target.innerText };
            }
            return { waiting: true };
        })()
        """
        for second in range(30):
            await asyncio.sleep(1)
            await ws.send(json.dumps({'id': 700 + second, 'method': 'Runtime.evaluate', 'params': {'expression': click_approve_js, 'returnByValue': True}}))
            for _ in range(10):
                msg = json.loads(await ws.recv())
                if msg.get('id') == 700 + second:
                    val = msg.get('result', {}).get('result', {}).get('value', {})
                    if val.get('success'):
                        print(f">>> APPROVED at second {second+1}! Clicked: {val.get('text')}", flush=True)
                        approved = True
                        break
            if approved:
                break
        
        if not approved:
            print("Warning: Genehmigen button did not appear within 30s or already started!", flush=True)

        print("8. Video generation initiated! Now waiting for completion...", flush=True)

asyncio.run(main())
