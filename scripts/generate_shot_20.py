import requests
import json
import time
import os
import shutil
import urllib.request
import urllib.parse
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

urls = json.load(open(r'd:\Projects\VideoGenerator\references\panels_storyboard_05\uploaded_urls.json', 'r', encoding='utf-8'))
p4_url = urls['panel_04_BR.png']

prompt = '''Low-angle cinematic forward tracking shot: the camera glides smoothly just inches above the glassy, calm lake surface at sunrise. Gentle concentric ripples spread outwards from the center of the frame, trailing behind. In the distance, the warm golden dawn sun rises over the horizon, casting a shimmering luminous path of light across the water. Photorealistic, 35mm optical lens, peaceful, majestic nature, no humans.'''

payload = {
    'jsonrpc': '2.0',
    'id': 2801,
    'method': 'tools/call',
    'params': {
        'name': 'image_to_video',
        'arguments': {
            'model': 'kling-video-v2_6',
            'arguments': [
                {'name': 'prompt', 'value': prompt},
                {'name': 'duration', 'value': '5'},
                {'name': 'resolution', 'value': '720p'},
                {'name': 'imageCount', 'value': '1'},
                {'name': 'enable_audio', 'value': 'false'}
            ],
            'inputs': [
                {
                    'name': 'first_image',
                    'inputType': 'URL',
                    'url': p4_url
                }
            ],
            'taskTraceId': 'shot20-low-angle-glide-horizon',
            'rationale': 'Animate Panel 4 of Act 5 showing low-angle glide over sunrise lake water'
        }
    }
}

res = requests.post(
    'https://kling.ai/mcp',
    json=payload,
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'},
    verify=False,
    timeout=20
).json()
print('Submit result:', res)
gen_info = json.loads(res['result']['content'][0]['text'])
gen_id = gen_info['generationId']
print('Submitted gen_id:', gen_id)

for i in range(40):
    time.sleep(5)
    poll_payload = {
        'jsonrpc': '2.0',
        'id': 2802,
        'method': 'tools/call',
        'params': {
            'name': 'query_tasks',
            'arguments': {'generationId': gen_id}
        }
    }
    poll_res = requests.post(
        'https://kling.ai/mcp',
        json=poll_payload,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'},
        verify=False,
        timeout=15
    ).json()
    task_data = json.loads(poll_res['result']['content'][0]['text'])
    status = task_data.get('status')
    print(f'Poll {i+1}: status = {status}')
    if status == 'COMPLETED':
        w = task_data['works'][0]
        vid_url = w.get('urlWithoutWatermark') or w.get('url_without_watermark') or w.get('url')
        print('Video URL:', vid_url)
        out_ws = r'd:\Projects\VideoGenerator\output\shot_20_glide_horizon.mp4'
        urllib.request.urlretrieve(vid_url, out_ws)
        out_art = r'C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66\shot_20_glide_horizon.mp4'
        shutil.copyfile(out_ws, out_art)
        print('Downloaded to:', out_ws)
        break
    elif status in ('FAILED', 'CANCELLED'):
        print('Failed:', task_data)
        break
