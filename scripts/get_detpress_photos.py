import urllib.request
import re
import os
import shutil

url = 'https://www.detpress.com/projects/free-solo/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
out_dir = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames"
art_dir = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"

try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        imgs = re.findall(r'https?://[^\s\"\'<>]+\.(?:jpg|png|webp)', html)
        print("Found image URLs:", len(imgs))
        fs_imgs = [img for img in set(imgs) if 'FreeSolo' in img or 'freesolo' in img.lower()]
        print("FreeSolo images:", len(fs_imgs))
        for i, img in enumerate(fs_imgs[:5]):
            # if thumbnail (-0x300), try to get full resolution
            full_img = re.sub(r'-\d+x\d+\.', '.', img)
            print(f"Downloading: {full_img}")
            out_path = os.path.join(out_dir, f"ref_freesolo_press_{i+1}.jpg")
            try:
                with urllib.request.urlopen(urllib.request.Request(full_img, headers={'User-Agent': 'Mozilla/5.0'})) as r, open(out_path, 'wb') as f:
                    f.write(r.read())
                shutil.copy2(out_path, os.path.join(art_dir, os.path.basename(out_path)))
                print(f"Saved: {out_path} ({os.path.getsize(out_path)} bytes)")
            except Exception as e:
                print(f"Failed full, trying original {img}: {e}")
                try:
                    with urllib.request.urlopen(urllib.request.Request(img, headers={'User-Agent': 'Mozilla/5.0'})) as r, open(out_path, 'wb') as f:
                        f.write(r.read())
                    shutil.copy2(out_path, os.path.join(art_dir, os.path.basename(out_path)))
                    print(f"Saved thumbnail: {out_path} ({os.path.getsize(out_path)} bytes)")
                except Exception as e2:
                    print(f"Failed thumb too: {e2}")
except Exception as e:
    print("Error:", e)
