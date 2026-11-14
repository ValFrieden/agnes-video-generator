import sys
import json
import uuid
import urllib.request
import urllib.parse
import time
import os
import shutil
import ssl
import urllib3
import requests

urllib3.disable_warnings()
ssl._create_default_https_context = ssl._create_unverified_context
sys.stdout.reconfigure(encoding='utf-8')

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

prompt = '''A cinematic 2x2 grid storyboard, 4 sequential panels continuing the exact photorealistic 35mm optical cinematography, dawn lake morning atmosphere, weathered wet dark wooden dock and water reflections from reference storyboard 4 and 5:

- Panel 1 (Top-Left): Extreme macro slow-motion; golden embers and charcoal ash on the wet dark wooden dock are swept upward by a sudden swirling morning vortex of wind, glowing sparks spiraling into the dawn air.
- Panel 2 (Top-Right): "Tear the veil": The dense cool blue morning mist over the lake is dramatically ripped open and dissolved by piercing, radiant golden sunbeams cutting through the fog, revealing brilliant clear water.
- Panel 3 (Bottom-Left): Epic cinematic wide sunrise; the blazing golden sun crests the horizon, flooding the lake with an intense explosion of warm golden light, water surface burning like liquid gold.
- Panel 4 (Bottom-Right): High-angle aerial crane shot rising high above the glassy lake; breathtaking vast panorama of infinite serene morning nature, calm shoreline, no walls, pure freedom under a clear sky.

Exact same color grading, deep atmospheric contrast, photorealistic 8k macro cinematography, natural dawn daylight, clean seamless 2x2 grid, no borders, no frames, no text, no dividing lines.'''

payload = {
    'jsonrpc': '2.0',
    'id': 601,
    'method': 'tools/call',
    'params': {
        'name': 'text_to_image',
        'arguments': {
            'model': 'gemini-3.1-flash-image',
            'arguments': [
                {'name': 'prompt', 'value': prompt},
                {'name': 'img_resolution', 'value': '2k'},
                {'name': 'aspect_ratio', 'value': '16:9'},
                {'name': 'imageCount', 'value': '1'}
            ],
            'taskTraceId': str(uuid.uuid4()),
            'rationale': 'Generate 2x2 storyboard reference image for Scene 06 (Bridge: Climax, Tearing the Veil) locked to Style 4 and 5'
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
print('Submit res:', res)
gen_info = json.loads(res['result']['content'][0]['text'])
gen_id = gen_info['generationId']
print('Submitted generationId:', gen_id)

for i in range(25):
    time.sleep(3)
    poll_payload = {
        'jsonrpc': '2.0',
        'id': 602,
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
        img_url = task_data['works'][0].get('urlWithoutWatermark') or task_data['works'][0].get('url')
        print('Image ready:', img_url)
        ws_path = r'd:\Projects\VideoGenerator\references\storyboard_06_grid.png'
        urllib.request.urlretrieve(img_url, ws_path)
        art_path = r'C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66\storyboard_06_grid.png'
        shutil.copyfile(ws_path, art_path)
        print('Downloaded to:', ws_path, 'and', art_path)
        break
    elif status in ('FAILED', 'CANCELLED'):
        print('Generation failed:', task_data)
        break
