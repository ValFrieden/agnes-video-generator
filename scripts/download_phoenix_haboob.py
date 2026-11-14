import urllib.request
import json
import os

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'}

def get_wiki_image(title, filename):
    url = f"https://commons.wikimedia.org/w/api.php?action=query&titles=File:{urllib.parse.quote(title)}&prop=imageinfo&iiprop=url&format=json"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        pages = data['query']['pages']
        for k, v in pages.items():
            if 'imageinfo' in v:
                img_url = v['imageinfo'][0]['url']
                print(f"Downloading {title} from {img_url}...")
                img_req = urllib.request.Request(img_url, headers=headers)
                with urllib.request.urlopen(img_req) as img_resp, open(filename, 'wb') as out_f:
                    out_f.write(img_resp.read())
                print(f"Saved: {filename} ({os.path.getsize(filename)} bytes)")
                return

os.makedirs('nikogda_ne_boyus_frames/references_sandstorm', exist_ok=True)
get_wiki_image('Phoenix_Dust_Storm_1_(7458935098).jpg', 'nikogda_ne_boyus_frames/references_sandstorm/haboob_phoenix_terracotta.jpg')
