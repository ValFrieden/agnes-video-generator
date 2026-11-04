import json, asyncio, websockets, base64, os, sys

WS_URL = "ws://127.0.0.1:9222/devtools/page/2821B56C358A533DD1C1D824E58CFE93"
OUT_FILE = "moy_mir_iz_snov_frames/scene_01_clean_raw.mp4"

async def download_tile_0():
    print("Connecting to Flow CDP...", flush=True)
    async with websockets.connect(WS_URL, max_size=100*1024*1024) as ws:
        # 1. Click top tile (tile 0)
        click_script = """(() => {
            const tile = document.querySelector('flow-video-tile');
            if (tile) {
                tile.click();
                return true;
            }
            return false;
        })()"""
        await ws.send(json.dumps({'id': 10, 'method': 'Runtime.evaluate', 'params': {'expression': click_script, 'returnByValue': True}}))
        resp = await ws.recv()
        print('Click tile 0:', json.loads(resp).get('result', {}).get('result', {}).get('value'))
        await asyncio.sleep(2)

        # 2. Install hook
        hook_script = """(() => {
            window.__captured_blobs = [];
            const origCreate = URL.createObjectURL;
            URL.createObjectURL = function(obj) {
                const url = origCreate.call(URL, obj);
                if (obj instanceof Blob) {
                    const reader = new FileReader();
                    reader.onload = () => {
                        window.__captured_blobs.push({
                            url: url, size: obj.size, type: obj.type, data: reader.result
                        });
                    };
                    reader.readAsDataURL(obj);
                }
                return url;
            };
            return true;
        })()"""
        await ws.send(json.dumps({'id': 20, 'method': 'Runtime.evaluate', 'params': {'expression': hook_script, 'returnByValue': True}}))
        await ws.recv()

        # 3. Open download menu
        open_menu = """(() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const dl = btns.find(b => (b.getAttribute('aria-label') || '').toLowerCase().includes('herunterladen') || (b.innerText || '').toLowerCase().includes('download'));
            if (dl) { dl.click(); return true; }
            return false;
        })()"""
        await ws.send(json.dumps({'id': 21, 'method': 'Runtime.evaluate', 'params': {'expression': open_menu, 'returnByValue': True}}))
        resp2 = await ws.recv()
        print('Open download menu:', json.loads(resp2).get('result', {}).get('result', {}).get('value'))
        await asyncio.sleep(1)

        # 4. Click 720p
        click_720 = """(() => {
            const btns = Array.from(document.querySelectorAll('button.mat-mdc-menu-item, flow-menu-item button, [role="menuitem"]'));
            const target = btns.find(b => (b.innerText || '').includes('720p'));
            if (target) { target.click(); return true; }
            return false;
        })()"""
        await ws.send(json.dumps({'id': 22, 'method': 'Runtime.evaluate', 'params': {'expression': click_720, 'returnByValue': True}}))
        resp3 = await ws.recv()
        print('Click 720p:', json.loads(resp3).get('result', {}).get('result', {}).get('value'))

        # 5. Extract blob
        saved = False
        for i in range(25):
            await asyncio.sleep(1)
            check_script = "window.__captured_blobs && window.__captured_blobs.length > 0 && !!window.__captured_blobs[0].data"
            await ws.send(json.dumps({'id': 100 + i, 'method': 'Runtime.evaluate', 'params': {'expression': check_script, 'returnByValue': True}}))
            c_resp = await ws.recv()
            has_blob = json.loads(c_resp).get('result', {}).get('result', {}).get('value', False)
            if has_blob:
                extract_script = "window.__captured_blobs[0].data"
                await ws.send(json.dumps({'id': 999, 'method': 'Runtime.evaluate', 'params': {'expression': extract_script, 'returnByValue': True}}))
                ext_resp = await ws.recv()
                data_url = json.loads(ext_resp)['result']['result']['value']
                header, b64data = data_url.split(',', 1)
                video_bytes = base64.b64decode(b64data)
                with open(OUT_FILE, 'wb') as f:
                    f.write(video_bytes)
                print(f'SUCCESS! Scene 01 Clean -> {len(video_bytes)} bytes saved to {OUT_FILE}', flush=True)
                saved = True
                break

        # 6. Close modal
        close_script = """(() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const close = btns.find(b => (b.innerText || '').includes('Fertig') || b.innerHTML.includes('close') || b.innerHTML.includes('arrow_back'));
            if (close) { close.click(); return true; }
            return false;
        })()"""
        await ws.send(json.dumps({'id': 500, 'method': 'Runtime.evaluate', 'params': {'expression': close_script, 'returnByValue': True}}))
        await ws.recv()
        return saved

if __name__ == '__main__':
    asyncio.run(download_tile_0())
