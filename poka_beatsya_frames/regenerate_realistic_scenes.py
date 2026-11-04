# -*- coding: utf-8 -*-
"""regenerate_realistic_scenes.py — Regeneriert Szenen 09, 10, 15, 16 mit strengen Regeln:
1. Gesicht NIRGENDWO sichtbar — immer tief im Schatten der Kapuze, nur Kapuze.
2. Keinerlei goldene Risse / kein Kintsugi.
3. Rein realistische, kinoreife Ästhetik (Roger Deakins).
"""

import asyncio
import base64
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
import websockets

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("HoodNoFaceRegen")

ROOT = Path(r"D:\Projects\VideoGenerator")
FRAMES_DIR = ROOT / "poka_beatsya_frames"
CLIPS_DIR = FRAMES_DIR / "clips_flow"
PAGE_URI = "ws://127.0.0.1:9222/devtools/page/AD5A6E3BE8C8038933692DF3BD5550E3"

# Strikt: Gesicht NIEMALS sichtbar, immer tief im Schatten der Kapuze, keine Goldrisse
STYLE_HOOD_NO_FACE = (
    "Cinematic realistic fine-art video, directed by Roger Deakins, 16:9 widescreen, 35mm film grain. "
    "Solitary traveler wearing a long dark heavy traveling coat with a deep pulled-forward dark hood, "
    "face completely concealed in black shadow under the hood, face is never visible, mysterious hooded silhouette, "
    "holding warm antique brass lantern. Atmospheric realism, natural chiaroscuro lighting, "
    "completely realistic textures, no magic effects, no glowing cracks, no golden veins, absolutely no face visible, only hood. "
)

REGEN_SCENES = {
    "09": f"{STYLE_HOOD_NO_FACE} Scene 09: Close tracking shot of the traveler battling a howling winter blizzard, deep dark hood pulled low concealing face in dark shadow, face never visible, heavy dark coat dusted in white snow, holding steady glowing warm brass lantern against the storm, natural winter lighting, completely realistic, no glowing cracks, no magic.",
    "10": f"{STYLE_HOOD_NO_FACE} Scene 10: First warm golden dawn light breaking over calm ocean horizon, traveler standing on rocky shore with deep dark hood pulled forward concealing face completely in shadow, face never visible, quiet stance watching the morning sun over the sea, natural realistic morning lighting, no face visible.",
    "15": f"{STYLE_HOOD_NO_FACE} Scene 15: Breathtaking realistic golden sunrise washing over dramatic coastal ocean cliffs, natural warm morning sunlight illuminating crashing ocean waves and sea spray, coastal wind rustling tall grass on the cliffs, pure realistic landscape cinematography, majestic nature, no statues, no glowing cracks.",
    "16": f"{STYLE_HOOD_NO_FACE} Scene 16: Traveler standing on high cliff edge overlooking radiant golden ocean sunrise, deep dark hood pulled forward with face completely hidden in dark shadow, face never visible, gently blowing out the flame in the antique brass lantern, natural cinematic sunlight, mysterious hooded male figure, no face visible.",
}

DURATIONS = {
    "01": 2.0, "02": 14.0, "03": 10.0, "04": 9.0, "05": 10.0,
    "06": 11.0, "07": 4.0, "08": 11.0, "09": 11.0, "10": 9.0,
    "11": 14.0, "12": 19.0, "13": 15.0, "14": 6.0, "15": 26.0,
    "16": 10.0, "17": 6.4,
}


async def ensure_canvas(ws):
    nav_canvas = """(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const fertig = btns.find(b => (b.innerText || '').includes('Fertig'));
        if (fertig) { fertig.click(); return 'fertig'; }
        const back = btns.find(b => b.innerHTML.includes('arrow_back'));
        if (back && window.location.href.includes('/edit/')) { back.click(); return 'back'; }
        return 'canvas';
    })()"""
    await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": nav_canvas, "returnByValue": True}}))
    await ws.recv()
    await asyncio.sleep(2)


async def generate_and_download_scene(ws, scene_id, prompt_text):
    out_file = CLIPS_DIR / f"scene_{scene_id}.mp4"
    logger.info(f"\n==========================================")
    logger.info(f"START GENERIERUNG SZENE {scene_id} (NUR KAPUZE / KEIN GESICHT)")
    logger.info(f"Prompt: {prompt_text}")
    logger.info(f"==========================================")

    await ensure_canvas(ws)

    # 1. Prompt in ProseMirror einfügen
    focus_script = """(() => {
        const pm = document.querySelector('div.ProseMirror');
        if (!pm) return false;
        pm.focus();
        document.execCommand('selectAll', false, null);
        document.execCommand('delete', false, null);
        return true;
    })()"""
    await ws.send(json.dumps({"id": 10, "method": "Runtime.evaluate", "params": {"expression": focus_script, "returnByValue": True}}))
    await ws.recv()

    await ws.send(json.dumps({"id": 11, "method": "Input.insertText", "params": {"text": prompt_text}}))
    await ws.recv()
    await asyncio.sleep(0.5)

    # Enter drücken
    await ws.send(json.dumps({
        "id": 12, "method": "Input.dispatchKeyEvent",
        "params": {"type": "rawKeyDown", "windowsVirtualKeyCode": 13, "unmodifiedText": "\r", "text": "\r"}
    }))
    await ws.recv()
    await ws.send(json.dumps({
        "id": 13, "method": "Input.dispatchKeyEvent",
        "params": {"type": "keyUp", "windowsVirtualKeyCode": 13}
    }))
    await ws.recv()
    logger.info(f"Prompt für Szene {scene_id} erfolgreich gesendet!")

    # 2. Warten auf Fertigstellung
    logger.info(f"Warte auf Google Flow Generierung für Szene {scene_id}...")
    start_t = time.time()
    await asyncio.sleep(10)

    while time.time() - start_t < 300:
        check_script = """(() => {
            const stopBtn = Array.from(document.querySelectorAll('button')).find(b => 
                b.innerHTML.includes('stop') || b.querySelector('mat-icon[data-mat-icon-name="stop"]')
            );
            const topTile = document.querySelector('flow-video-tile');
            const tileText = topTile ? topTile.innerText : '';
            const isRendering = tileText.includes('%');
            return {
                hasStopBtn: !!stopBtn,
                isRendering: isRendering,
                tileText: tileText.substring(0, 40)
            };
        })()"""
        await ws.send(json.dumps({"id": 20, "method": "Runtime.evaluate", "params": {"expression": check_script, "returnByValue": True}}))
        resp = await ws.recv()
        val = json.loads(resp).get("result", {}).get("result", {}).get("value", {})
        is_rendering = val.get("isRendering", False)
        elapsed = int(time.time() - start_t)

        if elapsed % 15 == 0:
            logger.info(f"[{elapsed}s] Generierung läuft... (Rendering: {is_rendering})")

        if not val.get("hasStopBtn") and not is_rendering and elapsed >= 20:
            logger.info(f"Szene {scene_id} nach {elapsed}s fertig gerendert!")
            break
        await asyncio.sleep(5)

    # 3. Klicke oberstes Video-Tile
    logger.info(f"Öffne neues Video-Tile für Szene {scene_id}...")
    click_tile = """(() => {
        const tiles = Array.from(document.querySelectorAll('flow-video-tile'));
        if (tiles.length > 0) {
            tiles[0].click();
            return true;
        }
        return false;
    })()"""
    await ws.send(json.dumps({"id": 30, "method": "Runtime.evaluate", "params": {"expression": click_tile, "returnByValue": True}}))
    await ws.recv()
    await asyncio.sleep(2)

    # 4. Falls im Editor noch Rendering-Prozent steht, warten
    editor_wait = time.time()
    while time.time() - editor_wait < 60:
        check_editor = """(() => {
            const text = document.body.innerText || '';
            const m = text.match(/(\\d+)\\s*%/);
            return { isRendering: !!m, pct: m ? m[1] : null };
        })()"""
        await ws.send(json.dumps({"id": 31, "method": "Runtime.evaluate", "params": {"expression": check_editor, "returnByValue": True}}))
        ed_resp = await ws.recv()
        ed_val = json.loads(ed_resp).get("result", {}).get("result", {}).get("value", {})
        if ed_val.get("isRendering"):
            logger.info(f"Editor rendert noch {ed_val.get('pct')}%...")
            await asyncio.sleep(4)
        else:
            break

    # 5. Hook installieren
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
    await ws.send(json.dumps({"id": 40, "method": "Runtime.evaluate", "params": {"expression": hook_script, "returnByValue": True}}))
    await ws.recv()

    # 6. Medien herunterladen
    open_menu = """(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const dl = btns.find(b => (b.getAttribute('aria-label') || '').toLowerCase().includes('herunterladen'));
        if (dl) { dl.click(); return true; }
        return false;
    })()"""
    await ws.send(json.dumps({"id": 41, "method": "Runtime.evaluate", "params": {"expression": open_menu, "returnByValue": True}}))
    await ws.recv()
    await asyncio.sleep(0.5)

    # 7. 720p Originalgröße anklicken
    click_720 = """(() => {
        const btns = Array.from(document.querySelectorAll('button.mat-mdc-menu-item, flow-menu-item button'));
        const target = btns.find(b => (b.innerText || '').includes('720p'));
        if (target) { target.click(); return true; }
        return false;
    })()"""
    await ws.send(json.dumps({"id": 42, "method": "Runtime.evaluate", "params": {"expression": click_720, "returnByValue": True}}))
    await ws.recv()

    # 8. Blob abfangen & Datei überschreiben
    saved = False
    for i in range(25):
        await asyncio.sleep(1)
        check_blob = "window.__captured_blobs && window.__captured_blobs.length > 0 && !!window.__captured_blobs[0].data"
        await ws.send(json.dumps({"id": 50 + i, "method": "Runtime.evaluate", "params": {"expression": check_blob, "returnByValue": True}}))
        b_resp = await ws.recv()
        has_blob = json.loads(b_resp).get("result", {}).get("result", {}).get("value", False)
        if has_blob:
            extract_script = "window.__captured_blobs[0].data"
            await ws.send(json.dumps({"id": 999, "method": "Runtime.evaluate", "params": {"expression": extract_script, "returnByValue": True}}))
            ext_resp = await ws.recv()
            data_url = json.loads(ext_resp)["result"]["result"]["value"]
            header, b64data = data_url.split(",", 1)
            video_bytes = base64.b64decode(b64data)
            with open(out_file, "wb") as f:
                f.write(video_bytes)
            logger.info(f"ERFOLG! Szene {scene_id} neu heruntergeladen ({len(video_bytes):,} Bytes) -> {out_file}")
            saved = True
            break

    # 9. Zurück zum Canvas
    await ensure_canvas(ws)
    return saved


async def main():
    logger.info("=== Starte Generierung: Keine Gesichter (nur Kapuze), keine Goldrisse ===")
    async with websockets.connect(PAGE_URI, max_size=50*1024*1024) as ws:
        for sc_id in ["09", "10", "15", "16"]:
            prompt = REGEN_SCENES[sc_id]
            success = await generate_and_download_scene(ws, sc_id, prompt)
            if not success:
                logger.error(f"Fehler bei Szene {sc_id}!")
            await asyncio.sleep(2)

    logger.info("=== Alle Szenen erfolgreich aktualisiert! Starte finale Assemblierung ===")
    assemble_final_realistic()


def assemble_final_realistic():
    """Trimm und re-assembliert das finale Video mit den neuen realistischen Szenen."""
    song_path = Path(r"D:\Projects\VideoGenerator\Пока бьётся.mp3")
    if not song_path.exists():
        song_path = FRAMES_DIR / "song.mp3"

    concat_file = CLIPS_DIR / "concat_list.txt"
    entries = []

    for sc_id in [f"{i:02d}" for i in range(1, 18)]:
        target_dur = DURATIONS[sc_id]
        src_clip = CLIPS_DIR / f"scene_{sc_id}.mp4"
        trimmed_clip = CLIPS_DIR / f"trimmed_{sc_id}.mp4"

        cmd_trim = [
            "ffmpeg", "-y", "-stream_loop", "2", "-i", str(src_clip),
            "-t", str(target_dur),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24",
            "-an", str(trimmed_clip)
        ]
        subprocess.run(cmd_trim, check=True, capture_output=True)
        entries.append(f"file '{trimmed_clip.resolve().as_posix()}'")
        logger.info(f"Szene {sc_id} getrimmt auf {target_dur}s.")

    with open(concat_file, "w", encoding="utf-8") as f:
        f.write("\n".join(entries) + "\n")

    final_output = FRAMES_DIR / "Пока_бьётся_клип_Google_Flow.mp4"
    logger.info(f"Rendere finalen Clip nach: {final_output}")

    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-i", str(song_path),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest", str(final_output)
    ]
    subprocess.run(cmd_concat, check=True, capture_output=True)
    logger.info(f"FERTIG! Vollendeter Clip ohne Gesicht & ohne Goldrisse: {final_output}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "assemble":
        assemble_final_realistic()
    else:
        asyncio.run(main())
