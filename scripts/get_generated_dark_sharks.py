import asyncio
import json
import urllib.request
import websockets
import os

async def main():
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    t = next(x for x in tabs if 'flow.google.com' in x.get('url',''))

    async with websockets.connect(t['webSocketDebuggerUrl'], max_size=20*1024*1024) as ws:
        script = """
        (() => {
            const imgs = Array.from(document.querySelectorAll('img')).filter(img => {
                const src = img.src || '';
                return src.includes('flow.google.com/asb') || src.includes('googleusercontent') || src.includes('storage.googleapis.com');
            }).map(img => ({
                src: img.src,
                w: img.naturalWidth || img.width,
                h: img.naturalHeight || img.height,
                class: img.className
            }));
            return imgs.slice(-6);
        })()
        """
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}))
        res = json.loads(await ws.recv())
        imgs = res['result']['result']['value']
        print("Last images:", json.dumps(imgs, indent=2))
        
        # Download each image
        out_dir = r'd:\Projects\VideoGenerator\nikogda_ne_boyus_frames'
        brain_dir = r'C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a'
        
        count = 1
        for im in imgs[-2:]:
            src = im['src']
            if '=s' in src:
                # Get high res
                src = src.split('=s')[0] + '=s2048-rw'
            print(f"Downloading image {count}:", src)
            req = urllib.request.Request(src, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                data = urllib.request.urlopen(req).read()
                fpath = os.path.join(out_dir, f'dark_sharks_option_{count}.png')
                bpath = os.path.join(brain_dir, f'dark_sharks_option_{count}.png')
                with open(fpath, 'wb') as f:
                    f.write(data)
                with open(bpath, 'wb') as f:
                    f.write(data)
                print(f"Saved option {count} to {fpath} ({len(data)} bytes)")
                count += 1
            except Exception as e:
                print(f"Failed to download: {e}")

if __name__ == '__main__':
    asyncio.run(main())
