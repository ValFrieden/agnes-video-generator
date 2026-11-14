import urllib.request
import json
import os
import shutil

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

out_dir = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames"
art_dir = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"

queries = [
    "jamming climbing",
    "crack climbing",
    "climbing chalk bag",
    "granite crack climbing"
]

found = []

for q in queries:
    url = f"https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrsearch={urllib.parse.quote(q)}&gsrnamespace=6&gsrlimit=10&prop=imageinfo&iiprop=url|size|thumburl&iiurlwidth=1280"
    req = urllib.request.Request(url, headers={'User-Agent': 'VideoGeneratorBot/1.0 (contact: valeri@example.com)'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            pages = data.get('query', {}).get('pages', {})
            for pid, p in pages.items():
                title = p.get('title', '')
                ii = p.get('imageinfo', [{}])[0]
                img_url = ii.get('thumburl') or ii.get('url')
                w = ii.get('width', 0)
                h = ii.get('height', 0)
                if img_url and any(img_url.lower().endswith(ext) or ext + '/' in img_url.lower() for ext in ['.jpg', '.png', '.jpeg', '.webp']):
                    found.append((title, img_url, w, h))
    except Exception as e:
        print(f"Error for {q}: {e}")

seen = set()
count = 5
for title, url, w, h in found:
    if title not in seen:
        seen.add(title)
        safe_title = "".join(c for c in title if c.isalnum() or c in " ._-")[:40]
        out_file = os.path.join(out_dir, f"ref_climb_{count}_{safe_title}.jpg")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp, open(out_file, 'wb') as f:
                f.write(resp.read())
            print(f"Saved: {out_file} ({os.path.getsize(out_file)} bytes)")
            art_file = os.path.join(art_dir, os.path.basename(out_file))
            shutil.copy2(out_file, art_file)
            count += 1
            if count >= 8:
                break
        except Exception as e:
            print(f"Failed {title}: {e}")
