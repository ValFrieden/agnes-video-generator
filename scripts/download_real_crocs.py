import urllib.request
import os
import shutil

REF_DIR = r"d:\Projects\VideoGenerator\nikogda_ne_boyus_frames\references_crocodiles"
os.makedirs(REF_DIR, exist_ok=True)
ARTIFACT_DIR = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) WildlifeResearcher/1.0'}

photos = [
    ("https://upload.wikimedia.org/wikipedia/commons/e/ef/A_Nile_Crocodile_Basks_along_The_Banks_of_River_Nile.jpg", "real_nile_croc_bank.jpg"),
    ("https://upload.wikimedia.org/wikipedia/commons/5/5d/Lake_Chamo_-_Large_Nile_crocodile_basking_on_the_shore%2C_Ethiopia.jpg", "real_lake_chamo_croc_shore.jpg"),
    ("https://upload.wikimedia.org/wikipedia/commons/6/65/Nile_Crocodile_%28Crocodylus_niloticus%29_basking_in_the_sun_..._%2852761866417%29.jpg", "real_croc_sun_basking.jpg"),
    ("https://upload.wikimedia.org/wikipedia/commons/2/2c/Nile_Crocodile_basking_%2813869043013%29.jpg", "real_croc_close_basking.jpg")
]

for url, fname in photos:
    dest = os.path.join(REF_DIR, fname)
    print(f"Downloading {fname}...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp, open(dest, "wb") as f:
            f.write(resp.read())
        shutil.copy2(dest, os.path.join(ARTIFACT_DIR, fname))
        print(f"Saved {fname}, size: {os.path.getsize(dest)} bytes")
    except Exception as e:
        print(f"Error downloading {fname}: {e}")

print("Done downloading references!")
