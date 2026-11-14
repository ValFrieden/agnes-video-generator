import urllib.request
import os

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
out_dir = 'nikogda_ne_boyus_frames/references_snakes'
brain_dir = 'C:/Users/Valeri/.gemini/antigravity/brain/5206faf6-a4af-482f-ad2b-3902d5efa61a'
os.makedirs(out_dir, exist_ok=True)

urls = [
    # Colorado Desert Sidewinder (Crotalus cerastes) crawling on sand/gravel
    ("sidewinder_desert_crawling.jpg", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Crotalus_cerastes_%28Colorado_Desert_Sidewinder%29_%283583100567%29.jpg/1280px-Crotalus_cerastes_%28Colorado_Desert_Sidewinder%29_%283583100567%29.jpg"),
    # Horned Desert Viper (Cerastes cerastes) on stones/sand
    ("horned_viper_desert.jpg", "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Hornviper_Cerastes_cerastes.jpg/1280px-Hornviper_Cerastes_cerastes.jpg"),
    # Western Diamondback on desert gravel
    ("western_diamondback_gravel.jpg", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Western_Diamondback_Rattlesnake_Crotalus_atrox.jpg/1280px-Western_Diamondback_Rattlesnake_Crotalus_atrox.jpg"),
    # Mojave Rattlesnake
    ("mojave_rattlesnake_rocks.jpg", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Crotalus_scutulatus.jpg/1280px-Crotalus_scutulatus.jpg")
]

for filename, url in urls:
    dst_proj = os.path.join(out_dir, filename)
    dst_brain = os.path.join(brain_dir, filename)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp, open(dst_proj, 'wb') as f:
            f.write(resp.read())
        import shutil
        shutil.copy2(dst_proj, dst_brain)
        print(f"Downloaded {filename}: {os.path.getsize(dst_proj)} bytes")
    except Exception as e:
        print(f"Failed {filename}: {e}")
