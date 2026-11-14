import urllib.request
import json
import os
import shutil

REF_DIR = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\references_crocodiles"
os.makedirs(REF_DIR, exist_ok=True)
ARTIFACT_DIR = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"

headers = {'User-Agent': 'WildlifeResearcherBot/1.0 (test@example.com)'}

# Search Wikimedia Commons API for real crocodile wildlife photos on riverbanks
search_url = "https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=Crocodylus%20niloticus%20riverbank%20basking&gsrnamespace=6&gsrlimit=10&prop=imageinfo&iiprop=url|size|extmetadata&format=json"

req = urllib.request.Request(search_url, headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    pages = data.get("query", {}).get("pages", {})
    downloaded = 0
    for pid, pdata in pages.items():
        title = pdata.get("title", "")
        imginfo = pdata.get("imageinfo", [{}])[0]
        url = imginfo.get("url")
        desc = imginfo.get("extmetadata", {}).get("ImageDescription", {}).get("value", "")
        if url and (url.endswith('.jpg') or url.endswith('.png')):
            fname = title.replace("File:", "").replace(" ", "_").replace("/", "_")[:40] + ".jpg"
            dest = os.path.join(REF_DIR, fname)
            print(f"Downloading {title} -> {fname}")
            try:
                img_req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(img_req, timeout=15) as img_resp, open(dest, "wb") as f:
                    f.write(img_resp.read())
                shutil.copy2(dest, os.path.join(ARTIFACT_DIR, fname))
                downloaded += 1
                if downloaded >= 4:
                    break
            except Exception as e:
                print(f"Failed {url}: {e}")
except Exception as e:
    print(f"Error querying Wikimedia: {e}")
