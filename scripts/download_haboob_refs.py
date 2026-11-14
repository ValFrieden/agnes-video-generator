import urllib.request
import json
import os

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

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
get_wiki_image('Sandstorm_in_Al_Asad,_Iraq.jpg', 'nikogda_ne_boyus_frames/references_sandstorm/haboob_iraq_al_asad.jpg')
get_wiki_image('Approaching_dust_storm_(haboob),_Cimarron_County,_OK.jpg', 'nikogda_ne_boyus_frames/references_sandstorm/haboob_oklahoma.jpg')
get_wiki_image('Haboob_Ransom_Canyon_Texas_2009.jpg', 'nikogda_ne_boyus_frames/references_sandstorm/haboob_texas.jpg')
get_wiki_image('Haboob_(dust_storm)_in_suburbs_of_Phoenix_Arizona.jpg', 'nikogda_ne_boyus_frames/references_sandstorm/haboob_phoenix.jpg')
