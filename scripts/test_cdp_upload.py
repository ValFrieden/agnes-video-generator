import asyncio
import json
import urllib.request
import websockets
import os

target_image = os.path.abspath("d:/Projects/VideoGenerator/nikogda_ne_boyus_frames/snake_valley_option2_1280x720.png")
print("Target image path:", target_image, "Exists:", os.path.exists(target_image))

async def upload_via_cdp():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        # Enable Page events & intercept file chooser
        print("Enabling Page and file chooser interception...")
        await ws.send(json.dumps({'id': 1, 'method': 'Page.enable'}))
        await ws.send(json.dumps({'id': 2, 'method': 'Page.setInterceptFileChooserDialog', 'params': {'enabled': True}}))
        
        while True:
            msg = json.loads(await ws.recv())
            if msg.get('id') == 2: break
        
        # Click the sidebar upload button
        print("Clicking .sidebar-upload-btn...")
        click_js = """
        (() => {
            const btn = document.querySelector('.sidebar-upload-btn');
            if (btn) {
                btn.click();
                return 'Clicked .sidebar-upload-btn';
            }
            return 'Button not found';
        })()
        """
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': click_js, 'returnByValue': True}}))
        
        # Listen for fileChooserOpened event
        file_chooser_handled = False
        for _ in range(50):
            msg = json.loads(await ws.recv())
            method = msg.get('method')
            if method == 'Page.fileChooserOpened':
                print(">>> Caught Page.fileChooserOpened event!", msg)
                await ws.send(json.dumps({
                    'id': 100,
                    'method': 'Page.handleFileChooser',
                    'params': {
                        'action': 'accept',
                        'files': [target_image]
                    }
                }))
                print("Sent Page.handleFileChooser accept with:", target_image)
                file_chooser_handled = True
                break
            elif msg.get('id') == 3:
                print("Click result:", msg.get('result', {}).get('result', {}).get('value'))
        
        if file_chooser_handled:
            print("Successfully submitted file via file chooser! Waiting 5s for upload to complete...")
            await asyncio.sleep(5)
        else:
            print("File chooser was not intercepted.")

asyncio.run(upload_via_cdp())
