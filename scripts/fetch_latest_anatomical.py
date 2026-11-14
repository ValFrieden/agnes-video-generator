import asyncio
import json
import urllib.request
import websockets
import base64
import os

async def fetch_latest():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))
    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        get_srcs = """
        (() => {
            const imgs = Array.from(document.querySelectorAll('img[src*="flow.google.com/asb"]'));
            return imgs.map((i, idx) => ({idx, src: i.src, w: i.naturalWidth, h: i.naturalHeight}));
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': get_srcs, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        imgs = res['result']['result']['value']
        print(f"Total asb imgs found: {len(imgs)}")
        for item in imgs[-6:]:
            print(item['idx'], item['w'], item['h'], item['src'][:80])

        last_two = [item['src'] for item in imgs[-2:]]
        out_dir = r'd:\Projects\VideoGenerator\nikogda_ne_boyus_frames'
        brain_dir = r'C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a'

        for i, src in enumerate(last_two, 1):
            fetch_script = f"""
            (async () => {{
                const res = await fetch({json.dumps(src)}, {{ credentials: 'include' }});
                const blob = await res.blob();
                return new Promise((resolve) => {{
                    const reader = new FileReader();
                    reader.onloadend = () => resolve(reader.result);
                    reader.readAsDataURL(blob);
                }});
            }})()
            """
            await ws.send(json.dumps({'id': 100+i, 'method': 'Runtime.evaluate', 'params': {'expression': fetch_script, 'awaitPromise': True, 'returnByValue': True}}))
            f_res = json.loads(await ws.recv())
            data_url = f_res['result']['result']['value']
            b64 = data_url.split(',', 1)[1]
            raw = base64.b64decode(b64)
            
            fpath = os.path.join(out_dir, f'anatomical_fin_option_{i}.png')
            bpath = os.path.join(brain_dir, f'anatomical_fin_option_{i}.png')
            with open(fpath, 'wb') as f:
                f.write(raw)
            with open(bpath, 'wb') as f:
                f.write(raw)
            print(f"Saved option {i}: {len(raw)} bytes -> {fpath}")

if __name__ == '__main__':
    asyncio.run(fetch_latest())
