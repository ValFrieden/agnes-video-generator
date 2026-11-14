import os
import subprocess
import requests
import json
import urllib.request
import urllib.parse
import uuid
import time
import ssl
import urllib3

urllib3.disable_warnings()
ssl._create_default_https_context = ssl._create_unverified_context

creds_path = r'C:\Users\Valeri\.claude\.credentials.json'

def get_token():
    creds = json.load(open(creds_path, 'r', encoding='utf-8'))
    oauth = creds['mcpOAuth']['klingai|8433fcbd6f022acd']
    if oauth.get('expiresAt', 0) - time.time() * 1000 < 60000:
        print('Refreshing token...')
        post_data = urllib.parse.urlencode({
            'grant_type': 'refresh_token',
            'client_id': oauth['clientId'],
            'refresh_token': oauth['refreshToken']
        }).encode('utf-8')
        req = urllib.request.Request('https://kling.ai/auth/token', data=post_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        res = json.loads(urllib.request.urlopen(req, timeout=10).read().decode('utf-8'))
        oauth['accessToken'] = res['access_token']
        if 'refresh_token' in res:
            oauth['refreshToken'] = res['refresh_token']
        oauth['expiresAt'] = int(time.time() * 1000) + res.get('expires_in', 3600) * 1000
        json.dump(creds, open(creds_path, 'w', encoding='utf-8'), indent=2)
    return oauth['accessToken']

token = get_token()

src_img = r'd:\Projects\VideoGenerator\references\storyboard_06_grid.png'
out_dir = r'd:\Projects\VideoGenerator\references\panels_storyboard_06'
os.makedirs(out_dir, exist_ok=True)

cmd_probe = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=s=x:p=0', src_img]
res_str = subprocess.check_output(cmd_probe).decode().strip()
w, h = map(int, res_str.split('x'))
print(f'Storyboard 06 resolution: {w}x{h}')
half_w, half_h = w // 2, h // 2

crops = [
    ('panel_01_TL.png', 0, 0),
    ('panel_02_TR.png', half_w, 0),
    ('panel_03_BL.png', 0, half_h),
    ('panel_04_BR.png', half_w, half_h),
]

for name, x, y in crops:
    out_p = os.path.join(out_dir, name)
    subprocess.run(['ffmpeg', '-y', '-i', src_img, '-filter:v', f'crop={half_w}:{half_h}:{x}:{y}', out_p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f'Cropped {name} ({os.path.getsize(out_p)} bytes)')

uploaded_urls = {}
for name, _, _ in crops:
    file_path = os.path.join(out_dir, name)
    file_size = os.path.getsize(file_path)
    payload = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'tools/call',
        'params': {
            'name': 'file_upload',
            'arguments': {
                'filename': name,
                'contentType': 'image/png',
                'size': file_size,
                'taskTraceId': str(uuid.uuid4())
            }
        }
    }
    res = requests.post(
        'https://kling.ai/mcp',
        json=payload,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'},
        verify=False,
        timeout=15
    ).json()
    ticket_data = json.loads(res['result']['content'][0]['text'])
    upload_url = ticket_data['uploadUrl']
    ticket = ticket_data['ticket']

    with open(file_path, 'rb') as f:
        up_res = requests.post(
            upload_url,
            data={'ticket': ticket},
            files={'file': (name, f, 'image/png')},
            headers={'Authorization': f'Bearer {token}'},
            verify=False,
            timeout=30
        )
        url = up_res.json()['data']['url']
        uploaded_urls[name] = url
        print(f'{name} -> {url}')

urls_path = os.path.join(out_dir, 'uploaded_urls.json')
with open(urls_path, 'w', encoding='utf-8') as f:
    json.dump(uploaded_urls, f, indent=2)
print('Saved all panel URLs to:', urls_path)
