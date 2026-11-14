import asyncio
import json
import urllib.request
import websockets
import base64
import os
import time

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    print("Tab URL:", t["url"])

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Step 1: Click submit button
        print("Clicking submit button (x: 1875, y: 900)...")
        await ws.send(json.dumps({'id': 10, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': 1875, 'y': 900, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        await ws.send(json.dumps({'id': 11, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': 1875, 'y': 900, 'button': 'left', 'clickCount': 1}}))
        await ws.recv()
        print("Submit clicked!")

        # Step 2: Loop to watch for Genehmigen / cost card
        approved = False
        print("Waiting for Genehmigen button...")
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
                # Mouse click
                await ws.send(json.dumps({'id': 200, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mousePressed', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1}}))
                await ws.recv()
                await ws.send(json.dumps({'id': 201, 'method': 'Input.dispatchMouseEvent', 'params': {'type': 'mouseReleased', 'x': c['x'], 'y': c['y'], 'button': 'left', 'clickCount': 1}}))
                await ws.recv()
                print("Dispatched click on Genehmigen!")
                approved = True
                
                # Take screenshot
                await asyncio.sleep(1)
                await ws.send(json.dumps({'id': 202, 'method': 'Page.captureScreenshot'}))
                s_res = json.loads(await ws.recv())
                with open('after_approval_sharks.png', 'wb') as sf:
                    sf.write(base64.b64decode(s_res['result']['data']))
                print("Saved after_approval_sharks.png")
                break
            else:
                if i % 3 == 0:
                    print(f"[{i}s] Waiting... Latest texts: {val.get('texts', [])[-3:]}")

        if not approved:
            print("Warning: Genehmigen button was not found within 60s.")
            return

        # Step 3: Monitor generation progress
        print("Monitoring video generation progress...")
        for p in range(120): # up to 4 minutes
            await asyncio.sleep(2)
            progress_script = """
            (() => {
                const textNodes = Array.from(document.querySelectorAll('div, span, p'))
                    .map(el => el.innerText ? el.innerText.trim() : '')
                    .filter(t => t.includes('%') || t.includes('Processing') || t.includes('processing') || t.includes('Generating') || t.includes('ready'));
                
                // Also check if new video is in the list
                const vids = Array.from(document.querySelectorAll('video, [data-media-type="video"], .video-container')).length;
                return { texts: textNodes.slice(-5), vidCount: vids };
            })()
            """
            await ws.send(json.dumps({'id': 300 + p, 'method': 'Runtime.evaluate', 'params': {'expression': progress_script, 'returnByValue': True}}))
            p_res = json.loads(await ws.recv())
            pval = p_res['result']['result']['value']
            
            if p % 5 == 0:
                print(f"[{p*2}s progress] texts: {pval.get('texts')}")
                
            # Check if any text says completed / 100% or generation done
            last_texts = pval.get('texts', [])
            if any('100%' in t for t in last_texts) or (p > 10 and not any('%' in t for t in last_texts)):
                # Take screenshot
                await ws.send(json.dumps({'id': 400, 'method': 'Page.captureScreenshot'}))
                sc_res = json.loads(await ws.recv())
                with open('video_generation_finished.png', 'wb') as vf:
                    vf.write(base64.b64decode(sc_res['result']['data']))
                print("Generation appears complete! Screenshot saved.")
                break

if __name__ == '__main__':
    asyncio.run(main())
