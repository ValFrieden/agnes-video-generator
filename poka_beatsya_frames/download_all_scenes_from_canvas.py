# -*- coding: utf-8 -*-
"""download_all_scenes_from_canvas.py — Lädt alle 17 fertigen Szenen vom Google Flow Canvas herunter.

Durchsucht die Flow-Video-Tiles nach "Scene 01", "Scene 02", ..., "Scene 17",
wartet bis das Rendering abgeschlossen ist (kein '%'), klickt das Tile an,
lädt das echte 720p Video über den Blob-Hook herunter und assembliert
am Ende das finale Video «Пока_бьётся_клип_Google_Flow.mp4».
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
logger = logging.getLogger("CanvasDownloader")

ROOT = Path(r"D:\Projects\VideoGenerator")
FRAMES_DIR = ROOT / "poka_beatsya_frames"
CLIPS_DIR = FRAMES_DIR / "clips_flow"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)
PAGE_URI = "ws://127.0.0.1:9222/devtools/page/AD5A6E3BE8C8038933692DF3BD5550E3"

DURATIONS = {
    "01": 2.0, "02": 14.0, "03": 10.0, "04": 9.0, "05": 10.0,
    "06": 11.0, "07": 4.0, "08": 11.0, "09": 11.0, "10": 9.0,
    "11": 14.0, "12": 19.0, "13": 15.0, "14": 6.0, "15": 26.0,
    "16": 10.0, "17": 6.4,
}


async def download_tile_for_scene(ws, scene_id, max_wait=300):
    """Findet das Tile für die gegebene Szene, wartet auf Fertigstellung und lädt es herunter."""
    out_file = CLIPS_DIR / f"scene_{scene_id}.mp4"
    if out_file.exists() and out_file.stat().st_size > 100000:
        logger.info(f"Szene {scene_id} bereits vorhanden ({out_file.stat().st_size} Bytes) — überspringe.")
        return True

    logger.info(f"Suche Canvas-Tile für Szene {scene_id}...")
    start_t = time.time()
    
    # 1. Warte bis das Tile auf dem Canvas existiert und fertig gerendert ist (kein %)
    while time.time() - start_t < max_wait:
        # Falls wir im Editor sind, erst zurück zum Canvas
        nav_canvas = """(() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const fertig = btns.find(b => (b.innerText || '').includes('Fertig'));
            if (fertig) { fertig.click(); return 'clicked_fertig'; }
            const back = btns.find(b => b.innerHTML.includes('arrow_back'));
            if (back && window.location.href.includes('/edit/')) { back.click(); return 'clicked_back'; }
            return 'already_on_canvas';
        })()"""
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": nav_canvas, "returnByValue": True}}))
        await ws.recv()
        await asyncio.sleep(1)

        # Suche Tile
        find_script = f"""(() => {{
            const tiles = Array.from(document.querySelectorAll('flow-video-tile'));
            const match = tiles.find(t => (t.innerText || '').includes('Scene {scene_id}:') || (t.innerText || '').includes('Scene {scene_id} '));
            if (!match) return {{ found: false, count: tiles.length }};
            const text = match.innerText || '';
            const isRendering = text.includes('%');
            return {{
                found: true,
                isRendering: isRendering,
                textSnippet: text.substring(0, 80)
            }};
        }})()"""
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": find_script, "returnByValue": True}}))
        resp = await ws.recv()
        info = json.loads(resp).get("result", {}).get("result", {}).get("value", {})
        
        elapsed = int(time.time() - start_t)
        if not info.get("found"):
            if elapsed % 15 == 0:
                logger.info(f"[{elapsed}s] Szene {scene_id} noch nicht auf dem Canvas... ({info.get('count', 0)} Tiles gefunden)")
            await asyncio.sleep(5)
            continue

        if info.get("isRendering"):
            if elapsed % 15 == 0:
                logger.info(f"[{elapsed}s] Szene {scene_id} rendert noch... ({info.get('textSnippet')})")
            await asyncio.sleep(5)
            continue

        # Tile ist da und fertig gerendert!
        logger.info(f"Szene {scene_id} ist bereit! Klicke Tile an...")
        click_script = f"""(() => {{
            const tiles = Array.from(document.querySelectorAll('flow-video-tile'));
            const match = tiles.find(t => (t.innerText || '').includes('Scene {scene_id}:') || (t.innerText || '').includes('Scene {scene_id} '));
            if (match) {{
                match.click();
                return true;
            }}
            return false;
        }})()"""
        await ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": click_script, "returnByValue": True}}))
        await ws.recv()
        await asyncio.sleep(2)
        break
    else:
        logger.error(f"Timeout beim Warten auf Szene {scene_id}!")
        return False

    # 2. Im Clip-Editor: Hook installieren & Download auslösen
    logger.info(f"Lade Video für Szene {scene_id} herunter...")
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
    await ws.send(json.dumps({"id": 10, "method": "Runtime.evaluate", "params": {"expression": hook_script, "returnByValue": True}}))
    await ws.recv()

    # Klicke Medien herunterladen
    open_menu = """(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const dl = btns.find(b => (b.getAttribute('aria-label') || '').toLowerCase().includes('herunterladen'));
        if (dl) { dl.click(); return true; }
        return false;
    })()"""
    await ws.send(json.dumps({"id": 11, "method": "Runtime.evaluate", "params": {"expression": open_menu, "returnByValue": True}}))
    await ws.recv()
    await asyncio.sleep(0.5)

    # Klicke 720p Originalgröße
    click_720 = """(() => {
        const btns = Array.from(document.querySelectorAll('button.mat-mdc-menu-item, flow-menu-item button'));
        const target = btns.find(b => (b.innerText || '').includes('720p'));
        if (target) { target.click(); return true; }
        return false;
    })()"""
    await ws.send(json.dumps({"id": 12, "method": "Runtime.evaluate", "params": {"expression": click_720, "returnByValue": True}}))
    await ws.recv()

    # Extrahiere Blob
    saved = False
    for i in range(25):
        await asyncio.sleep(1)
        check_script = "window.__captured_blobs && window.__captured_blobs.length > 0 && !!window.__captured_blobs[0].data"
        await ws.send(json.dumps({"id": 20 + i, "method": "Runtime.evaluate", "params": {"expression": check_script, "returnByValue": True}}))
        c_resp = await ws.recv()
        has_blob = json.loads(c_resp).get("result", {}).get("result", {}).get("value", False)
        if has_blob:
            extract_script = "window.__captured_blobs[0].data"
            await ws.send(json.dumps({"id": 999, "method": "Runtime.evaluate", "params": {"expression": extract_script, "returnByValue": True}}))
            ext_resp = await ws.recv()
            data_url = json.loads(ext_resp)["result"]["result"]["value"]
            header, b64data = data_url.split(",", 1)
            video_bytes = base64.b64decode(b64data)
            with open(out_file, "wb") as f:
                f.write(video_bytes)
            logger.info(f"ERFOLG! Szene {scene_id} heruntergeladen ({len(video_bytes)} Bytes) -> {out_file}")
            saved = True
            break

    # 3. Zurück zum Canvas
    back_script = """(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const fertig = btns.find(b => (b.innerText || '').includes('Fertig'));
        if (fertig) { fertig.click(); return true; }
        const back = btns.find(b => b.innerHTML.includes('arrow_back'));
        if (back) { back.click(); return true; }
        return false;
    })()"""
    await ws.send(json.dumps({"id": 50, "method": "Runtime.evaluate", "params": {"expression": back_script, "returnByValue": True}}))
    await ws.recv()
    await asyncio.sleep(2)
    return saved


async def main():
    async with websockets.connect(PAGE_URI, max_size=50*1024*1024) as ws:
        for sc_id in [f"{i:02d}" for i in range(1, 18)]:
            await download_tile_for_scene(ws, sc_id)
            await asyncio.sleep(2)

    logger.info("=== Alle Downloads beendet! Starte finale Assemblierung ===")
    from batch_flow_generator import assemble_final
    assemble_final()

if __name__ == "__main__":
    asyncio.run(main())
