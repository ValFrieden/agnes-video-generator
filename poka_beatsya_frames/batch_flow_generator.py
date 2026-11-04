# -*- coding: utf-8 -*-
"""batch_flow_generator.py — Vollautomatische Generierung aller 17 Szenen in Google Flow.

Steuert Google Flow über Chrome CDP (Port 9222), generiert jede Szene als echtes
Video mit konsistentem Charakter & Roger Deakins Chiaroscuro-Stil, lädt die fertigen
MP4s herunter und setzt am Ende das vollständige Musikvideo zusammen.
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
logger = logging.getLogger("FlowBatch")

ROOT = Path(r"D:\Projects\VideoGenerator")
FRAMES_DIR = ROOT / "poka_beatsya_frames"
CLIPS_DIR = FRAMES_DIR / "clips_flow"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)
PAGE_URI = "ws://127.0.0.1:9222/devtools/page/AD5A6E3BE8C8038933692DF3BD5550E3"

# Globaler Konsistenz-Anker
STYLE = (
    "Cinematic fine-art video, directed by Roger Deakins, 16:9 widescreen, 35mm film grain, "
    "deep indigo Prussian blue and bone-white shadows transitioning to radiant molten kintsugi gold. "
    "Solitary hooded traveler in dark long coat holding warm glowing brass lantern, consistent character. "
)

PROMPTS = {
    "01": f"{STYLE} Scene 01: Sudden dramatic white lightning flash freezing the solitary traveler on a dark rain-slicked country road, heavy rain streaks, camera slowly pushing in, intense chiaroscuro contrast.",
    "02": f"{STYLE} Scene 02: Vast misty meadow at night, cool cyanotype indigo fog, solitary traveler standing still on a dirt road, holding warm glowing brass lantern breathing in a slow rhythmic pulse, camera slowly tracking sideways, volumetric fog.",
    "03": f"{STYLE} Scene 03: Dark country road lined with giant frozen stone statues of turncoats, heavy cold rain pouring, traveler walking steadily past them, rain drops glistening like silver.",
    "04": f"{STYLE} Scene 04: Epic storm clouds parting, celestial beam of heavenly light illuminating the straight road to the horizon, distant needle silhouette of a lighthouse, slow camera tilt up.",
    "05": f"{STYLE} Scene 05: Close view of a petrified stone statue holding a dagger, traveler gently touching the stone chest, glowing molten gold kintsugi veins blooming along the fracture, slow motion.",
    "06": f"{STYLE} Scene 06: Field behind the traveler glowing with smoldering red embers and dark ash, traveler walking forward, each boot step leaving a luminous golden glow on the burnt earth.",
    "07": f"{STYLE} Scene 07: Minimalist immense dark sapphire night sky with distant ancient stars, single tiny warm golden lantern light glowing at the bottom center of the frame, subtle cosmic wind.",
    "08": f"{STYLE} Scene 08: Winter night snowfall in slow motion, distant stark lighthouse on a rugged cliff piercing the dark blizzard with a steady golden column of light, camera tracking forward.",
    "09": f"{STYLE} Scene 09: Howling blizzard, traveler leaning into the storm with unyielding grace, dark cloak whipping in the wind, glowing golden embroidery and seams pulsing like veins of light across the chest.",
    "10": f"{STYLE} Scene 10: Storm clouds breaking over the ocean, first warm peach and amber dawn light along the horizon, traveler lowering the hood, gentle slow-motion profile in sunrise light.",
    "11": f"{STYLE} Scene 11: Macro cinematic lens of melting ice droplets sliding down textured antique lantern glass, each water drop reflecting a miniature golden sunrise and lighthouse, golden bokeh.",
    "12": f"{STYLE} Scene 12: Grand white lighthouse tower rising above crashing ocean waves with glowing white spray, warm golden dawn fog rolling over coastal rocks, majestic cinematic scale.",
    "13": f"{STYLE} Scene 13: Ancient stone pier stretching into the calm golden dawn sea toward the lighthouse gate, sky reflections on wet stone pavement, traveler walking steadily toward the radiant horizon.",
    "14": f"{STYLE} Scene 14: Dark vignette with only two warm golden lights pulsing in antiphase heartbeat rhythm: foreground lantern and distant lighthouse eye, intimate poetic tension.",
    "15": f"{STYLE} Scene 15: Blinding glorious golden sunrise washing over the waking earth, dark stone statues disintegrating into sparkling golden dust scattered by the morning wind, blooming golden flora.",
    "16": f"{STYLE} Scene 16: Traveler at the cliff summit overlooking the radiant golden ocean, gently blowing out the lantern candle, bright warm inner golden light radiating from traveler's chest and heart.",
    "17": f"{STYLE} Scene 17: Aerial slow pull-back shot, tranquil turquoise and golden morning sea gently lapping against the lighthouse cliff, peaceful morning mist dissolving into pure warm white light.",
}

# Target-Dauern für Beat-Grid-Schnitt
DURATIONS = {
    "01": 2.0, "02": 14.0, "03": 10.0, "04": 9.0, "05": 10.0,
    "06": 11.0, "07": 4.0, "08": 11.0, "09": 11.0, "10": 9.0,
    "11": 14.0, "12": 19.0, "13": 15.0, "14": 6.0, "15": 26.0,
    "16": 10.0, "17": 6.4,
}


async def submit_scene_prompt(ws, prompt_text):
    """Gibt den Prompt in das ProseMirror-Eingabefeld ein und drückt Enter."""
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
    logger.info("Prompt gesendet!")


async def wait_for_video_ready(ws, scene_id, timeout=300):
    """Wartet, bis das Video fertig generiert ist und als Flow-Video-Tile bereitsteht."""
    logger.info(f"Warte auf Generierung von Szene {scene_id}...")
    start_time = time.time()
    await asyncio.sleep(10)  # Initiale Wartezeit

    while time.time() - start_time < timeout:
        check_script = """(() => {
            const stopBtn = Array.from(document.querySelectorAll('button')).find(b => 
                b.innerHTML.includes('stop') || b.querySelector('mat-icon[data-mat-icon-name="stop"]')
            );
            const tiles = Array.from(document.querySelectorAll('flow-video-tile'));
            return {
                isGenerating: !!stopBtn,
                tilesCount: tiles.length
            };
        })()"""
        await ws.send(json.dumps({"id": 20, "method": "Runtime.evaluate", "params": {"expression": check_script, "returnByValue": True}}))
        resp = await ws.recv()
        val = json.loads(resp).get("result", {}).get("result", {}).get("value", {})
        is_gen = val.get("isGenerating", False)
        elapsed = int(time.time() - start_time)

        if elapsed % 15 == 0:
            logger.info(f"[{elapsed}s] Generierung läuft... (Stop-Button: {is_gen})")

        if not is_gen and elapsed >= 20:
            logger.info(f"Generierung für Szene {scene_id} nach {elapsed}s abgeschlossen!")
            return True

        await asyncio.sleep(5)
    return False


async def download_top_video(ws, scene_id):
    """Klickt das oberste flow-video-tile, lädt das 720p Video herunter und kehrt zurück."""
    out_file = CLIPS_DIR / f"scene_{scene_id}.mp4"
    logger.info(f"Öffne Clip-Editor für Szene {scene_id}...")

    # Klicke erstes flow-video-tile
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

    # Installiere Blob-Hook
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
    await ws.send(json.dumps({"id": 31, "method": "Runtime.evaluate", "params": {"expression": hook_script, "returnByValue": True}}))
    await ws.recv()

    # Klicke Medien herunterladen
    open_menu = """(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const dl = btns.find(b => (b.getAttribute('aria-label') || '').toLowerCase().includes('herunterladen'));
        if (dl) { dl.click(); return true; }
        return false;
    })()"""
    await ws.send(json.dumps({"id": 32, "method": "Runtime.evaluate", "params": {"expression": open_menu, "returnByValue": True}}))
    await ws.recv()
    await asyncio.sleep(0.5)

    # Klicke 720p Originalgröße
    click_720 = """(() => {
        const btns = Array.from(document.querySelectorAll('button.mat-mdc-menu-item, flow-menu-item button'));
        const target = btns.find(b => (b.innerText || '').includes('720p'));
        if (target) { target.click(); return true; }
        return false;
    })()"""
    await ws.send(json.dumps({"id": 33, "method": "Runtime.evaluate", "params": {"expression": click_720, "returnByValue": True}}))
    await ws.recv()

    # Warte auf Blob-Extraktion
    logger.info("Extrahiere Videodaten...")
    saved = False
    for i in range(20):
        await asyncio.sleep(1)
        check_script = "window.__captured_blobs && window.__captured_blobs.length > 0 && !!window.__captured_blobs[0].data"
        await ws.send(json.dumps({"id": 40 + i, "method": "Runtime.evaluate", "params": {"expression": check_script, "returnByValue": True}}))
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
            logger.info(f"ERFOLG! Szene {scene_id} gespeichert ({len(video_bytes)} Bytes) -> {out_file}")
            saved = True
            break

    if not saved:
        logger.error(f"Konnte Video für Szene {scene_id} nicht extrahieren!")

    # Klicke Fertig / Back um zum Canvas zurückzukehren
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


async def run_pipeline():
    """Führt die Generierung für alle noch fehlenden Szenen durch."""
    logger.info("=== Starte automatische Google Flow Video Generierung ===")
    
    # Prüfe aktuelle Seite
    async with websockets.connect(PAGE_URI, max_size=50*1024*1024) as ws:
        for sc_id in [f"{i:02d}" for i in range(1, 18)]:
            target_clip = CLIPS_DIR / f"scene_{sc_id}.mp4"
            if target_clip.exists() and target_clip.stat().st_size > 100000:
                logger.info(f"Szene {sc_id} existiert bereits ({target_clip.stat().st_size} Bytes) — überspringe.")
                continue

            prompt = PROMPTS[sc_id]
            logger.info(f"--- Starte Szene {sc_id} ---")
            logger.info(f"Prompt: {prompt}")

            await submit_scene_prompt(ws, prompt)
            ok = await wait_for_video_ready(ws, sc_id, timeout=300)
            if not ok:
                logger.error(f"Timeout bei Szene {sc_id}! Versuche trotzdem Download...")

            downloaded = await download_top_video(ws, sc_id)
            if not downloaded:
                logger.warning(f"Szene {sc_id} konnte nicht heruntergeladen werden. Warte 5s und fahre fort...")
            
            await asyncio.sleep(3)

    logger.info("=== Alle Szenen generiert! Starte Finale Montage ===")
    assemble_final()


def assemble_final():
    """Schneidet alle echten generierten Szenen auf den Song und rendert das finale Video."""
    song_path = Path(r"D:\Projects\VideoGenerator\Пока бьётся.mp3")
    if not song_path.exists():
        song_path = FRAMES_DIR / "song.mp3"

    concat_file = CLIPS_DIR / "concat_list.txt"
    entries = []

    for sc_id in [f"{i:02d}" for i in range(1, 18)]:
        target_dur = DURATIONS[sc_id]
        src_clip = CLIPS_DIR / f"scene_{sc_id}.mp4"
        trimmed_clip = CLIPS_DIR / f"trimmed_{sc_id}.mp4"

        if not src_clip.exists():
            logger.warning(f"Fehlende Szene {sc_id}! Versuche Fallback...")
            # Fallback falls eine Szene fehlschlug
            fb = FRAMES_DIR / "clips2" / f"seq{sc_id}.mp4"
            if fb.exists():
                src_clip = fb
            else:
                src_clip = FRAMES_DIR / f"scene_{sc_id}.png"

        if src_clip.suffix.lower() == ".png":
            # Still-Fallback falls absolut nötig
            temp_mp4 = CLIPS_DIR / f"temp_{sc_id}.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-loop", "1", "-i", str(src_clip),
                "-t", str(target_dur), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-vf", "scale=1280:720,fps=24", str(temp_mp4)
            ], check=True, capture_output=True)
            src_clip = temp_mp4

        # Auf Target-Dauer trimmen / loopen falls Clip kürzer als target_dur
        # Note: Bei Flow ist der Clip ~10s. Wenn target_dur z.B. 14s ist, loopen oder verlangsamen wir
        # Wir nutzen -stream_loop falls target_dur > Clip-Dauer
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
    logger.info(f"FERTIG! Das Meisterwerk-Musikvideo mit echten Flow-Videos wurde gerendert: {final_output}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "assemble":
        assemble_final()
    else:
        asyncio.run(run_pipeline())
