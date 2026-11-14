import asyncio
import json
import urllib.request
import websockets
import base64
import os

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        extract_script = """
        (() => {
            const chatImgs = Array.from(document.querySelectorAll('.chat-message img, [class*="message"] img, .image-thumbnail img, img.image-thumbnail'))
                .filter(img => img.naturalWidth > 100);
            
            const results = [];
            for (let i = 0; i < chatImgs.length; i++) {
                const img = chatImgs[i];
                const canvas = document.createElement('canvas');
                canvas.width = img.naturalWidth;
                canvas.height = img.naturalHeight;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                results.push({
                    index: i,
                    w: canvas.width,
                    h: canvas.height,
                    dataUrl: canvas.toDataURL('image/png')
                });
            }
            return results.slice(-2);
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': extract_script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        imgs = res['result']['result']['value']
        print(f"Extracted {len(imgs)} images from canvas.")

        out_dir = r'd:\Projects\VideoGenerator\nikogda_ne_boyus_frames'
        brain_dir = r'C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a'
        
        for idx, item in enumerate(imgs, 1):
            data_url = item['dataUrl']
            b64 = data_url.split(',', 1)[1]
            raw = base64.b64decode(b64)
            fpath = os.path.join(out_dir, f'dark_sharks_option_{idx}.png')
            bpath = os.path.join(brain_dir, f'dark_sharks_option_{idx}.png')
            with open(fpath, 'wb') as f:
                f.write(raw)
            with open(bpath, 'wb') as f:
                f.write(raw)
            print(f"Saved Option {idx} ({item['w']}x{item['h']}): {fpath} ({len(raw)} bytes)")

if __name__ == '__main__':
    asyncio.run(main())
