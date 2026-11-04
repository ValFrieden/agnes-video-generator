import asyncio
import json
import urllib.request
import websockets
import os

async def upload_file(file_path):
    abs_path = os.path.abspath(file_path)
    print("Uploading:", abs_path)
    pages = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    page = next(p for p in pages if 'flow.google.com' in p.get('url', ''))
    ws_url = page['webSocketDebuggerUrl']
    async with websockets.connect(ws_url) as ws:
        # Enable Page domain
        await ws.send(json.dumps({'id': 1, 'method': 'Page.enable'}))
        await ws.recv()

        # Intercept file chooser
        await ws.send(json.dumps({'id': 2, 'method': 'Page.setInterceptFileChooserDialog', 'params': {'enabled': True}}))
        await ws.recv()

        # Click upload button in menu
        click_upload = """(() => {
            const menu = document.querySelector('.mat-mdc-menu-panel, [role="menu"]');
            if (menu) {
                const btn = Array.from(menu.querySelectorAll('button, [role="menuitem"]')).find(b => (b.innerText || '').includes('Hochladen') || (b.innerText || '').includes('Upload'));
                if (btn) {
                    btn.click();
                    return 'Clicked Hochladen in menu';
                }
            }
            return 'Hochladen not found in menu';
        })()"""
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': click_upload, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        print(res['result']['result']['value'])

        # Wait for Page.fileChooserOpened event
        file_set = False
        for _ in range(15):
            msg = json.loads(await ws.recv())
            if msg.get('method') == 'Page.fileChooserOpened':
                print("FileChooser dialog opened! Submitting file via Page.handleFileChooser...")
                await ws.send(json.dumps({
                    'id': 100,
                    'method': 'Page.handleFileChooser',
                    'params': {
                        'action': 'accept',
                        'files': [abs_path]
                    }
                }))
                print(await ws.recv())
                file_set = True
                break

        if file_set:
            print("File accepted! Waiting 3s for upload...")
            await asyncio.sleep(3)
        else:
            print("FileChooser did not trigger.")

if __name__ == '__main__':
    asyncio.run(upload_file('moy_mir_iz_snov_frames/scene_01.png'))
