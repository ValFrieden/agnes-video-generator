import asyncio
import json
import urllib.request
import websockets
import os

async def upload_option_2():
    abs_path = os.path.abspath('nikogda_ne_boyus_frames/anatomical_fin_option_2.png')
    print("Uploading target file:", abs_path)
    assert os.path.exists(abs_path), f"File not found: {abs_path}"
    
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    print("Tab URL:", t["url"])
    
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        await ws.send(json.dumps({'id': 1, 'method': 'Page.enable'}))
        await ws.recv()
        
        await ws.send(json.dumps({'id': 2, 'method': 'Page.setInterceptFileChooserDialog', 'params': {'enabled': True}}))
        await ws.recv()
        
        # Open menu if needed
        ensure_click_hochladen = """
        (() => {
            let btns = Array.from(document.querySelectorAll('button[role="menuitem"], .mat-mdc-menu-item, span'));
            let uploadBtn = btns.find(b => (b.innerText || '').trim() === 'Hochladen' || (b.innerText || '').includes('Hochladen'));
            if (!uploadBtn) {
                const menuBtn = document.querySelector('button[aria-label*="Medien hinzufügen"]');
                if (menuBtn) {
                    menuBtn.click();
                }
            }
            return 'Checked/toggled';
        })()
        """
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': ensure_click_hochladen, 'returnByValue': True}}))
        await ws.recv()
        
        await asyncio.sleep(0.5)
        
        # Click Hochladen
        click_h = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button[role="menuitem"], .mat-mdc-menu-item, span'));
            const uploadBtn = btns.find(b => (b.innerText || '').trim() === 'Hochladen' || (b.innerText || '').includes('Hochladen'));
            if (uploadBtn) {
                uploadBtn.click();
                return 'SUCCESS_CLICKED_HOCHLADEN';
            }
            return 'STILL_NOT_FOUND';
        })()
        """
        await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': click_h, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Click result:", res['result']['result']['value'])
        
        file_set = False
        for _ in range(15):
            try:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=1.5))
                if msg.get('method') == 'Page.fileChooserOpened':
                    print("Intercepted Page.fileChooserOpened! Sending file path...")
                    await ws.send(json.dumps({
                        'id': 100,
                        'method': 'Page.handleFileChooser',
                        'params': {
                            'action': 'accept',
                            'files': [abs_path]
                        }
                    }))
                    print("handleFileChooser sent:", await ws.recv())
                    file_set = True
                    break
            except asyncio.TimeoutError:
                pass
                
        if file_set:
            print("File accepted! Waiting 5s for upload to process in Flow...")
            await asyncio.sleep(5)
            
            # Check attached chips
            check_chips = """
            (() => {
                const chips = Array.from(document.querySelectorAll('.chip, .image-chip, [class*="chip"]')).map(c => c.innerText);
                return chips;
            })()
            """
            await ws.send(json.dumps({'id': 200, 'method': 'Runtime.evaluate', 'params': {'expression': check_chips, 'returnByValue': True}}))
            c_res = json.loads(await ws.recv())
            print("Chips after upload:", c_res['result']['result']['value'])

if __name__ == '__main__':
    asyncio.run(upload_option_2())
