import urllib.request
import json
import re
import os
import shutil

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
out_dir = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames"
art_dir = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"

url = "https://unsplash.com/napi/search/photos?query=rock+climbing+back&per_page=10"
req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        results = data.get('results', [])
        print(f"Unsplash results: {len(results)}")
        count = 1
        for photo in results[:4]:
            img_url = photo.get('urls', {}).get('regular')
            desc = photo.get('alt_description') or f"unsplash_climber_{count}"
            safe_desc = "".join(c for c in desc if c.isalnum() or c in " ._-")[:40]
            out_file = os.path.join(out_dir, f"ref_real_climber_{count}_{safe_desc}.jpg")
            print(f"Downloading: {img_url} -> {out_file}")
            r = urllib.request.Request(img_url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(r) as r_resp, open(out_file, 'wb') as f:
                f.write(r_resp.read())
            shutil.copy2(out_file, os.path.join(art_dir, os.path.basename(out_file)))
            print(f"Saved {out_file} ({os.path.getsize(out_file)} bytes)")
            count += 1
except Exception as e:
    print(f"Error fetching Unsplash: {e}")
