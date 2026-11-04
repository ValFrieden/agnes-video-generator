"""generate_begi_flow_remaining.py
Autonomer Batch-Generator fuer die verbleibenden Szenen von 'Беги за солнцем' ueber Google Flow:
- Szenen: 03, 05, 06, 07, 08, 09, 10, 11, 12
- Modell: Veo 3.1 - Fast (niedrigste Credit-Kosten)
- Aufloesung: 720p (1280x720)
- Dauer: 8s
- Nach Fertigstellung: Automatischer Schnitt mit song.mp3 zu Беги_за_солнцем_клип_Желтый_зонт.mp4
"""

import json
import asyncio
import websockets
import base64
import os
import subprocess
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).parent
FRAMES_DIR = ROOT / "begi_za_solntsem_frames"
CLIPS_DIR = FRAMES_DIR / "clips_flow"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)
SONG = FRAMES_DIR / "song.mp3"

WS_URI = 'ws://127.0.0.1:9222/devtools/page/AD5A6E3BE8C8038933692DF3BD5550E3'

STYLE_DNA = (
    "Vintage hand-painted cel animation style, gouache painted backgrounds, 16:9 widescreen, "
    "cinematic Edward Hopper lighting, slate blue and glowing warm amber gold palette, "
    "atmospheric film grain, wet reflections. "
    "Solitary traveler in dark slate coat, vibrant glowing canary-yellow umbrella, bare face, no eyeglasses. "
    "Consistent character across all scenes."
)

REMAINING_SCENES = [
    {
        "id": 3,
        "title": "Куплет 1: Первые лучи в лужах",
        "prompt": (
            f"Generate video in 720p resolution using Veo 3.1 - Fast model (lowest credit cost). "
            f"Based on the attached yellow umbrella reference: {STYLE_DNA}. "
            "Scene 03: Low-angle close-up of wet cobblestone pavement with expanding puddle ripples reflecting dark indigo sky. "
            "A sharp diagonal shaft of warm golden morning sunlight pierces the mist, striking the water surface with golden amber ripples. "
            "Smooth water splashes, glistening droplets, static camera."
        )
    },
    {
        "id": 5,
        "title": "Прехорус: Открыто окно",
        "prompt": (
            f"Generate video in 720p resolution using Veo 3.1 - Fast model (lowest credit cost). "
            f"Based on the attached yellow umbrella reference: {STYLE_DNA}. "
            "Scene 05: Historic brick townhouse facade in cool rain: third-floor round attic window swung open, "
            "sheer white curtains fluttering gently in warm window breeze, soft amber golden sunlight spilling outward into misty rain, "
            "atmospheric raindrops, quiet morning."
        )
    },
    {
        "id": 6,
        "title": "Припев 1: Граница тьмы и света",
        "prompt": (
            f"Generate video in 720p resolution using Veo 3.1 - Fast model (lowest credit cost). "
            f"Based on the attached yellow umbrella reference: {STYLE_DNA}. "
            "Scene 06: Grand stone bridge across a misty river at dawn. Solitary traveler centered on the bridge holding the open yellow umbrella, "
            "standing at the exact border where stormy indigo storm clouds break into brilliant golden sunrise rays. "
            "Wind gently ruffling coat hem, glowing light rays spreading across clouds, majestic stillness."
        )
    },
    {
        "id": 7,
        "title": "Припев 1: Тепло на лице",
        "prompt": (
            f"Generate video in 720p resolution using Veo 3.1 - Fast model (lowest credit cost). "
            f"Based on the attached yellow umbrella reference: {STYLE_DNA}. "
            "Scene 07: Emotional close-up profile of the traveler's calm face under the yellow umbrella edge. "
            "Wet dark hair, determined gentle eyes reflecting golden dawn rays, a single rain droplet trickles down cheek, "
            "warm side-lighting illuminating skin, closed lips, subtle natural breathing, cinematic portrait."
        )
    },
    {
        "id": 8,
        "title": "Куплет 2: Преследование теней",
        "prompt": (
            f"Generate video in 720p resolution using Veo 3.1 - Fast model (lowest credit cost). "
            f"Based on the attached yellow umbrella reference: {STYLE_DNA}. "
            "Scene 08: Ancient arched stone colonnade in misty twilight. Traveler stands holding the glowing yellow umbrella, "
            "as deep blue evening shadows stretch across stone pillars. Warm amber light from the umbrella pushes back the cool gloom, "
            "swirling low ground fog, painterly textures."
        )
    },
    {
        "id": 9,
        "title": "Куплет 2: Зонт закрывается",
        "prompt": (
            f"Generate video in 720p resolution using Veo 3.1 - Fast model (lowest credit cost). "
            f"Based on the attached yellow umbrella reference: {STYLE_DNA}. "
            "Scene 09: River overlook promenade. Rain has stopped, only sparkling sun mist remains. "
            "Traveler calmly lowers and folds the bright yellow umbrella, holding it resting against arm. "
            "Golden sunlight breaking over glistening wet balustrade, peaceful breathing motion."
        )
    },
    {
        "id": 10,
        "title": "Припев 2: Золото над крышами",
        "prompt": (
            f"Generate video in 720p resolution using Veo 3.1 - Fast model (lowest credit cost). "
            f"Based on the attached yellow umbrella reference: {STYLE_DNA}. "
            "Scene 10: Low angle looking up toward old cathedral spires and slate rooftops. "
            "Golden morning light breaking through parting clouds, steam rising from wet roof tiles, "
            "warm golden bokeh dust floating through the air, magnificent painterly cel animation."
        )
    },
    {
        "id": 11,
        "title": "Припев 2: Торжество утра",
        "prompt": (
            f"Generate video in 720p resolution using Veo 3.1 - Fast model (lowest credit cost). "
            f"Based on the attached yellow umbrella reference: {STYLE_DNA}. "
            "Scene 11: High panoramic rooftop view across the historic city. Traveler stands on rooftop terrace holding yellow umbrella, "
            "looking out at radiant golden sunrise sweeping across wet slate roofs, blue sky expanding, "
            "sparkling water gutters, gentle breeze."
        )
    },
    {
        "id": 12,
        "title": "Финал: Солнечная скамья",
        "prompt": (
            f"Generate video in 720p resolution using Veo 3.1 - Fast model (lowest credit cost). "
            f"Based on the attached yellow umbrella reference: {STYLE_DNA}. "
            "Scene 12: Returning to the park promenade bench from Scene 01. The wooden bench is now completely dry in warm bright summer sunlight. "
            "Wildflowers blooming in grass around bench, gentle sunny breeze swaying blossoms, serene triumphant peace, no people, purely warm summer light."
        )
    }
]

async def send_prompt(ws, text):
    focus_script = """(() => {
        const pm = document.querySelector('div.ProseMirror');
        if (!pm) return false;
        pm.focus();
        return true;
    })()"""
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': focus_script, 'returnByValue': True}}))
    await ws.recv()

    await ws.send(json.dumps({'id': 2, 'method': 'Input.insertText', 'params': {'text': text}}))
    await ws.recv()
    await asyncio.sleep(0.5)

    click_script = """(() => {
        const sendBtn = Array.from(document.querySelectorAll('button')).find(b => 
            b.innerHTML.includes('arrow_forward') || (b.innerText || '').includes('arrow_forward')
        );
        if (sendBtn && !sendBtn.disabled) {
            sendBtn.click();
            return { success: true };
        }
        return { success: false, disabled: sendBtn ? sendBtn.disabled : null };
    })()"""
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': click_script, 'returnByValue': True}}))
    await ws.recv()

    await ws.send(json.dumps({
        'id': 4,
        'method': 'Input.dispatchKeyEvent',
        'params': {'type': 'keyDown', 'key': 'Enter', 'code': 'Enter', 'windowsVirtualKeyCode': 13}
    }))
    await ws.recv()
    await ws.send(json.dumps({
        'id': 5,
        'method': 'Input.dispatchKeyEvent',
        'params': {'type': 'keyUp', 'key': 'Enter', 'code': 'Enter', 'windowsVirtualKeyCode': 13}
    }))
    await ws.recv()

async def wait_and_download_latest(ws, out_file):
    print(f"Waiting for latest video to finish generating...", flush=True)
    # Poll cards until the latest card (card 0) has a play button
    for attempt in range(60):
        await asyncio.sleep(5)
        check_cards = """(() => {
            const cards = Array.from(document.querySelectorAll('flow-grid-tile-container'));
            if (cards.length === 0) return { ready: false };
            const card0 = cards[0];
            const hasPlay = !!card0.querySelector('mat-icon, [class*="play"]');
            const aria = card0.getAttribute('aria-label') || '';
            const progress = (card0.innerText || '').match(/\\d+\\s*%/);
            return { ready: hasPlay, aria: aria, progress: progress ? progress[0] : null };
        })()"""
        await ws.send(json.dumps({'id': 10, 'method': 'Runtime.evaluate', 'params': {'expression': check_cards, 'returnByValue': True}}))
        resp = await ws.recv()
        info = json.loads(resp).get('result', {}).get('result', {}).get('value', {})
        prog = info.get('progress') or 'generating'
        print(f"  [{attempt*5}s] Tile status: {prog} (ready={info.get('ready')})", flush=True)
        if info.get('ready'):
            print(f"Video ready! Downloading 720p to {out_file}...", flush=True)
            break
    else:
        print("Timeout waiting for video to finish generating.", flush=True)
        return False

    # Click card 0
    click_card = """(() => {
        const cards = Array.from(document.querySelectorAll('flow-grid-tile-container'));
        if (cards.length > 0) {
            cards[0].scrollIntoView({ block: 'center' });
            cards[0].click();
            return true;
        }
        return false;
    })()"""
    await ws.send(json.dumps({'id': 20, 'method': 'Runtime.evaluate', 'params': {'expression': click_card, 'returnByValue': True}}))
    await ws.recv()
    await asyncio.sleep(2)

    # Intercept blob URL
    hook_script = """(() => {
        window.__captured_blobs = [];
        const origCreate = URL.createObjectURL;
        URL.createObjectURL = function(obj) {
            const url = origCreate.call(URL, obj);
            if (obj instanceof Blob) {
                const reader = new FileReader();
                reader.onload = () => {
                    window.__captured_blobs.push({
                        url: url, size: obj.size, type: obj.type, data: reader.result
                    });
                };
                reader.readAsDataURL(obj);
            }
            return url;
        };
        return true;
    })()"""
    await ws.send(json.dumps({'id': 30, 'method': 'Runtime.evaluate', 'params': {'expression': hook_script, 'returnByValue': True}}))
    await ws.recv()

    # Open download menu
    open_menu = """(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const dl = btns.find(b => (b.getAttribute('aria-label') || '').toLowerCase().includes('herunterladen'));
        if (dl) { dl.click(); return true; }
        return false;
    })()"""
    await ws.send(json.dumps({'id': 40, 'method': 'Runtime.evaluate', 'params': {'expression': open_menu, 'returnByValue': True}}))
    await ws.recv()
    await asyncio.sleep(0.5)

    # Click 720p
    click_720 = """(() => {
        const btns = Array.from(document.querySelectorAll('button.mat-mdc-menu-item, flow-menu-item button'));
        const target = btns.find(b => (b.innerText || '').includes('720p'));
        if (target) { target.click(); return true; }
        return false;
    })()"""
    await ws.send(json.dumps({'id': 50, 'method': 'Runtime.evaluate', 'params': {'expression': click_720, 'returnByValue': True}}))
    await ws.recv()

    # Save video bytes
    saved = False
    for i in range(25):
        await asyncio.sleep(1)
        check_script = "window.__captured_blobs && window.__captured_blobs.length > 0 && !!window.__captured_blobs[0].data"
        await ws.send(json.dumps({'id': 100 + i, 'method': 'Runtime.evaluate', 'params': {'expression': check_script, 'returnByValue': True}}))
        c_resp = await ws.recv()
        has_blob = json.loads(c_resp).get('result', {}).get('result', {}).get('value', False)
        if has_blob:
            extract_script = "window.__captured_blobs[0].data"
            await ws.send(json.dumps({'id': 999, 'method': 'Runtime.evaluate', 'params': {'expression': extract_script, 'returnByValue': True}}))
            ext_resp = await ws.recv()
            data_url = json.loads(ext_resp)['result']['result']['value']
            header, b64data = data_url.split(',', 1)
            video_bytes = base64.b64decode(b64data)
            with open(out_file, 'wb') as f:
                f.write(video_bytes)
            print(f"SUCCESS! {len(video_bytes)} bytes written to {out_file}", flush=True)
            saved = True
            break

    # Return to canvas
    back_script = """(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const fertig = btns.find(b => (b.innerText || '').includes('Fertig'));
        if (fertig) { fertig.click(); return true; }
        const back = btns.find(b => b.innerHTML.includes('arrow_back'));
        if (back) { back.click(); return true; }
        return false;
    })()"""
    await ws.send(json.dumps({'id': 500, 'method': 'Runtime.evaluate', 'params': {'expression': back_script, 'returnByValue': True}}))
    await ws.recv()
    await asyncio.sleep(2)
    return saved


def assemble_final_video():
    print("\n--- Assembling final 96.0s video clip with song.mp3 ---", flush=True)
    concat_list = FRAMES_DIR / "concat_list_flow.txt"
    entries = []
    missing = []
    for i in range(1, 13):
        flat_v = FRAMES_DIR / f"scene_{i:02d}.mp4"
        flow_v = CLIPS_DIR / f"scene_{i:02d}.mp4"
        v = flat_v if flat_v.exists() else flow_v
        if v.exists() and v.stat().st_size > 100000:
            entries.append(f"file '{v.resolve().as_posix()}'")
        else:
            missing.append(i)

    if missing:
        print(f"Warning: Scenes {missing} still missing or invalid!", flush=True)
        if len(entries) < 10:
            print("Not enough scenes to assemble yet.", flush=True)
            return False

    with open(concat_list, "w", encoding="utf-8") as f:
        f.write("\n".join(entries) + "\n")

    final_out = FRAMES_DIR / "Беги_за_солнцем_клип_Желтый_зонт.mp4"
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-i", str(SONG),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        "-c:a", "aac", "-b:a", "256k",
        "-shortest", str(final_out)
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"SUCCESS: Final clip assembled: {final_out}", flush=True)
        root_out = ROOT / "Беги_за_солнцем_клип_Желтый_зонт.mp4"
        shutil.copy2(final_out, root_out)
        print(f"Copied final clip to root: {root_out}", flush=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Stitch error: {e.stderr.decode('utf-8', errors='ignore')}", flush=True)
        return False


async def main():
    async with websockets.connect(WS_URI, max_size=50*1024*1024) as ws:
        for item in REMAINING_SCENES:
            sid = item["id"]
            final_dest = FRAMES_DIR / f"scene_{sid:02d}.mp4"
            flow_dest = CLIPS_DIR / f"scene_{sid:02d}.mp4"

            if final_dest.exists() and final_dest.stat().st_size > 100000:
                print(f"Scene {sid:02d} already exists, skipping.", flush=True)
                continue

            print(f"\n==================================================", flush=True)
            print(f"Generating Scene {sid:02d}: {item['title']} (720p Veo 3.1 Fast)", flush=True)
            print(f"==================================================", flush=True)
            await send_prompt(ws, item["prompt"])
            success = await wait_and_download_latest(ws, str(flow_dest))
            if success and flow_dest.exists():
                shutil.copy2(flow_dest, final_dest)
                print(f"Scene {sid:02d} saved to {final_dest}", flush=True)
            await asyncio.sleep(3)

    assemble_final_video()

if __name__ == '__main__':
    asyncio.run(main())
