import asyncio
import json
import urllib.request
import websockets
import os
import base64

async def upload_sandstorm_and_prepare():
    target_file = os.path.abspath('nikogda_ne_boyus_frames/sandstorm_hero_back_1280x720.png')
    print("Target file to upload:", target_file)
    assert os.path.exists(target_file), f"File not found: {target_file}"

    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    print("Tab URL:", t["url"])

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Step 1: Check if editor or image detail is open; click Fertig or arrow_back
        close_view = """
        (() => {
            const fertig = Array.from(document.querySelectorAll('button, span')).find(b => (b.innerText || '').trim() === 'Fertig');
            if (fertig) {
                (fertig.closest('button') || fertig).click();
                return 'CLICKED_FERTIG';
            }
            const back = document.querySelector('button[aria-label*="Zurück"], button[aria-label*="Back"]');
            if (back) {
                back.click();
                return 'CLICKED_BACK';
            }
            return 'NO_OVERLAY';
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': close_view, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Close overlay result:", res['result']['result']['value'])
        await asyncio.sleep(1)

        # Step 2: Enable Page and file chooser interception
        await ws.send(json.dumps({'id': 2, 'method': 'Page.enable'}))
        await ws.recv()
        await ws.send(json.dumps({'id': 3, 'method': 'Page.setInterceptFileChooserDialog', 'params': {'enabled': True}}))
        await ws.recv()

        # Step 3: Trigger upload menu
        trigger_upload = """
        (() => {
            let btns = Array.from(document.querySelectorAll('button[role="menuitem"], .mat-mdc-menu-item, span'));
            let uploadBtn = btns.find(b => (b.innerText || '').trim() === 'Hochladen' || (b.innerText || '').includes('Hochladen'));
            if (!uploadBtn) {
                const menuBtn = document.querySelector('button[aria-label*="Medien hinzufügen"]');
                if (menuBtn) {
                    menuBtn.click();
                    return 'CLICKED_ADD_MEDIA_BUTTON';
                }
            } else {
                uploadBtn.click();
                return 'CLICKED_HOCHLADEN_DIRECTLY';
            }
            return 'CHECKING';
        })()
        """
        await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': trigger_upload, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Trigger upload step 1:", res['result']['result']['value'])
        await asyncio.sleep(0.5)

        # If we clicked the menu button, now click "Hochladen" in the popup menu
        click_h = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button[role="menuitem"], .mat-mdc-menu-item, span'));
            const uploadBtn = btns.find(b => (b.innerText || '').trim() === 'Hochladen' || (b.innerText || '').includes('Hochladen'));
            if (uploadBtn) {
                (uploadBtn.closest('button') || uploadBtn).click();
                return 'CLICKED_HOCHLADEN_MENUITEM';
            }
            return 'HOCHLADEN_NOT_FOUND';
        })()
        """
        await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': click_h, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print("Click Hochladen step 2:", res['result']['result']['value'])

        # Intercept file chooser
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
                            'files': [target_file]
                        }
                    }))
                    await ws.recv()
                    file_set = True
                    print("File successfully delivered to file chooser!")
                    break
            except asyncio.TimeoutError:
                pass

        await asyncio.sleep(3)
        # Take screenshot to verify upload
        await ws.send(json.dumps({'id': 200, 'method': 'Page.captureScreenshot'}))
        s_res = json.loads(await ws.recv())
        with open('after_sandstorm_upload.png', 'wb') as sf:
            sf.write(base64.b64decode(s_res['result']['data']))
        print("Saved after_sandstorm_upload.png, file_set =", file_set)

if __name__ == '__main__':
    asyncio.run(upload_sandstorm_and_prepare())
