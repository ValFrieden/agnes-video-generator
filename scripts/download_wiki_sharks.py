import urllib.request
import json
import os

url = "https://commons.wikimedia.org/w/api.php?action=query&format=json&list=search&srsearch=shark%20fin%20water&srnamespace=6&srlimit=10"
req = urllib.request.Request(url, headers={'User-Agent': 'VideoGeneratorBot/1.0 (test@example.com)'})
res = json.loads(urllib.request.urlopen(req).read().decode())
results = res.get('query', {}).get('search', [])

titles = [r['title'] for r in results]
print("Found titles:", titles)

# For each title, get image info
img_urls = []
for title in titles[:5]:
    info_url = f"https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url&titles={urllib.parse.quote(title)}"
    req_info = urllib.request.Request(info_url, headers={'User-Agent': 'VideoGeneratorBot/1.0 (test@example.com)'})
    info_res = json.loads(urllib.request.urlopen(req_info).read().decode())
    pages = info_res.get('query', {}).get('pages', {})
    for pid, pdata in pages.items():
        if 'imageinfo' in pdata:
            img_urls.append((title, pdata['imageinfo'][0]['url']))

out_dir = r"d:\Projects\VideoGenerator\references\shark_surface_references"
brain_dir = r"C:\Users\Valeri\.gemini\antigravity\brain\5206faf6-a4af-482f-ad2b-3902d5efa61a"
os.makedirs(out_dir, exist_ok=True)

for i, (t, u) in enumerate(img_urls):
    print(f"Downloading {t} from {u}")
    try:
        req_dl = urllib.request.Request(u, headers={'User-Agent': 'VideoGeneratorBot/1.0 (test@example.com)'})
        data = urllib.request.urlopen(req_dl).read()
        ext = os.path.splitext(u.split('?')[0])[1] or '.jpg'
        out_path = os.path.join(out_dir, f"shark_fin_ref_{i+1}{ext}")
        brain_path = os.path.join(brain_dir, f"shark_fin_ref_{i+1}{ext}")
        with open(out_path, 'wb') as f:
            f.write(data)
        with open(brain_path, 'wb') as f:
            f.write(data)
        print(f"Saved: {out_path} ({len(data)} bytes)")
    except Exception as e:
        print(f"Error downloading {u}: {e}")
