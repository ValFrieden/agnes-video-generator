import json, asyncio, websockets, os, time

async def trigger_download():
    uri = 'ws://127.0.0.1:9222/devtools/page/0E7BD9B8349EB35B98566144FF51F46A'
    async with websockets.connect(uri) as ws:
        msg_id = 100

        async def send(method, params=None):
            nonlocal msg_id
            msg_id += 1
            payload = {'id': msg_id, 'method': method}
            if params:
                payload['params'] = params
            await ws.send(json.dumps(payload))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get('id') == msg_id:
                    return resp.get('result', {})

        # 1. Allow downloads in Downloads folder
        print('1. Setting download behavior to allow...')
        await send('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': 'C:\\Users\\Valeri\\Downloads'
        })

        # 2. Click download button
        print('2. Clicking Medien herunterladen button...')
        click_btn = """(() => {
            const btn = document.querySelector('button[aria-label="Medien herunterladen"]');
            if (btn) {
                btn.click();
                return { clicked: true };
            }
            return { clicked: false };
        })()"""
        r1 = await send('Runtime.evaluate', {'expression': click_btn, 'returnByValue': True})
        print('Click download button result:', r1.get('result', {}).get('value'))

        await asyncio.sleep(1.2)

        # 3. Click 720p option in menu
        print('3. Finding and clicking 720p menu item...')
        click_720 = """(() => {
            const items = Array.from(document.querySelectorAll('button, [role="menuitem"], flow-menu-item'));
            const item720 = items.find(el => (el.innerText || '').includes('720p'));
            if (item720) {
                // If it's flow-menu-item, find button inside or click directly
                const b = item720.tagName === 'BUTTON' ? item720 : (item720.querySelector('button') || item720);
                b.click();
                return { clicked: true, tag: b.tagName, text: b.innerText };
            }
            return { clicked: false, items: items.map(i => i.innerText.slice(0, 30)) };
        })()"""
        r2 = await send('Runtime.evaluate', {'expression': click_720, 'returnByValue': True})
        print('Click 720p result:', r2.get('result', {}).get('value'))

        # 4. Wait for file in Downloads folder
        downloads_dir = 'C:\\Users\\Valeri\\Downloads'
        initial_files = set(os.listdir(downloads_dir))

        print('4. Monitoring Downloads directory for new mp4...')
        downloaded = None
        for i in range(25):
            await asyncio.sleep(1)
            current = os.listdir(downloads_dir)
            new_mp4s = [f for f in current if f not in initial_files and f.endswith('.mp4') and not f.endswith('.crdownload')]
            if new_mp4s:
                downloaded = os.path.join(downloads_dir, new_mp4s[0])
                print(f'🎉 Found downloaded mp4: {downloaded} ({os.path.getsize(downloaded)} bytes)')
                break
            else:
                cr = [f for f in current if f.endswith('.crdownload')]
                if cr:
                    print(f'Downloading in progress: {cr[0]}')

        if not downloaded:
            print('No downloaded file detected.')

asyncio.run(trigger_download())
