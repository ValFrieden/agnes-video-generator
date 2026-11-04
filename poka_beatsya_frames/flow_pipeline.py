# -*- coding: utf-8 -*-
"""poka_flow_pipeline.py — Google Flow / Veo Video Pipeline für «Пока бьётся» (187.4 s).

Verwaltet die 17 Szenen des Meisterwerk-Drehbuchs, überwacht die Generierung
in Google Flow (über Chrome CDP Port 9222) und führt alle Clips am Ende
mit ffmpeg und song.mp3 (Пока бьётся.mp3) zu einem nahtlosen Musikvideo zusammen.
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("PokaFlowPipeline")

ROOT = Path(__file__).resolve().parent.parent
FRAMES_DIR = ROOT / "poka_beatsya_frames"
CLIPS_DIR = FRAMES_DIR / "clips_flow"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)

SONG = Path(r"D:\Projects\VideoGenerator\Пока бьётся.mp3")
if not SONG.exists():
    SONG = FRAMES_DIR / "song.mp3"

TOTAL_DURATION = 187.4

# Globaler Stil- und Charakter-Anker für absolute Konsistenz in Google Veo
STYLE_CANON = (
    "Cinematic fine-art film still, directed by Roger Deakins and Andrei Tarkovsky, "
    "anamorphic 2.39:1 widescreen, deep indigo Prussian blue and bone-white shadows "
    "transitioning to radiant molten kintsugi gold, natural volumetric lighting, 35mm grain. "
    "Consistent canonical traveler: solitary hooded traveler in a long dark traveling coat "
    "holding an antique warm brass lantern, identical silhouette as reference."
)

SCENES = [
    {
        "id": "01",
        "dur": 2.0,
        "name": "Initial-Schlag (Der Schock)",
        "prompt": f"{STYLE_CANON} Scene 01: Sudden dramatic white lightning flash freezing the solitary traveler on a dark rain-slicked country road, diagonal rain streaks, intense chiaroscuro contrast.",
    },
    {
        "id": "02",
        "dur": 14.0,
        "name": "Nebelmeer (Die Einsamkeit)",
        "prompt": f"{STYLE_CANON} Scene 02: Vast misty meadow at night, cool cyanotype indigo fog, solitary traveler standing still on a dirt road, holding warm glowing brass lantern breathing in a slow rhythmic 90 BPM pulse.",
    },
    {
        "id": "03",
        "dur": 10.0,
        "name": "Statuen des Verrats",
        "prompt": f"{STYLE_CANON} Scene 03: Dark country road lined with giant frozen stone statues of turncoats turned away, heavy cold rain pouring, traveler walking steadily through them, rain drops glistening like silver.",
    },
    {
        "id": "04",
        "dur": 9.0,
        "name": "Aufreißender Himmel (Der Wille)",
        "prompt": f"{STYLE_CANON} Scene 04: Epic storm clouds parting, celestial beam of heavenly light illuminating the straight road to the horizon, distant needle silhouette of a lighthouse, low-angle perspective.",
    },
    {
        "id": "05",
        "dur": 10.0,
        "name": "Kintsugi der Klinge (Vergebung)",
        "prompt": f"{STYLE_CANON} Scene 05: Close view of a petrified stone statue holding a dagger with a deceitful smile, the traveler gently touching the statue, molten gold kintsugi veins blooming along the fracture.",
    },
    {
        "id": "06",
        "dur": 11.0,
        "name": "Glühende Asche (Überstandene Hölle)",
        "prompt": f"{STYLE_CANON} Scene 06: Field behind the traveler glowing with smoldering red embers and dark ash, traveler walking forward, each footprint leaving a luminous golden glow on the burnt earth.",
    },
    {
        "id": "07",
        "dur": 4.0,
        "name": "Kosmische Stille (Der Atemzug)",
        "prompt": f"{STYLE_CANON} Scene 07: Minimalist immense dark sapphire night sky with distant ancient stars, single tiny warm golden lantern light glowing at the bottom center of the frame, perfect silence.",
    },
    {
        "id": "08",
        "dur": 11.0,
        "name": "Schneesturm & Leuchtturm (Das Ziel)",
        "prompt": f"{STYLE_CANON} Scene 08: Winter night snowfall in slow motion, distant stark lighthouse on a rugged cliff piercing the dark blizzard with a steady, fixed golden column of light.",
    },
    {
        "id": "09",
        "dur": 11.0,
        "name": "Goldene Narben (In jedem Schmerz Liebe)",
        "prompt": f"{STYLE_CANON} Scene 09: Howling blizzard, traveler leaning into the storm with unyielding grace, dark cloak whipping in the wind, glowing golden embroidery and seams pulsing like veins of light across the chest.",
    },
    {
        "id": "10",
        "dur": 9.0,
        "name": "Dämmerung am Meer (Die Schwelle)",
        "prompt": f"{STYLE_CANON} Scene 10: Storm clouds breaking over the ocean, first warm peach and amber dawn light along the horizon, traveler removing the hood, gentle slow-motion profile in sunrise light.",
    },
    {
        "id": "11",
        "dur": 14.0,
        "name": "Makro Laternenglas (Gitarrensolo)",
        "prompt": f"{STYLE_CANON} Scene 11: Macro cinematic lens of melting ice droplets sliding down textured antique lantern glass, each water drop reflecting a miniature golden sunrise and lighthouse, golden bokeh.",
    },
    {
        "id": "12",
        "dur": 19.0,
        "name": "Monumentaler Leuchtturm (Ich will leben!)",
        "prompt": f"{STYLE_CANON} Scene 12: Grand white lighthouse tower rising above crashing ocean waves with glowing white spray, warm golden dawn fog rolling over coastal rocks, majestic triumph.",
    },
    {
        "id": "13",
        "dur": 15.0,
        "name": "Steinpier im Morgenlicht",
        "prompt": f"{STYLE_CANON} Scene 13: Ancient stone pier stretching into the calm golden dawn sea toward the lighthouse gate, sky reflections on wet stone pavement, traveler walking toward the radiant horizon.",
    },
    {
        "id": "14",
        "dur": 6.0,
        "name": "Puls der zwei Lichter (Breakdown)",
        "prompt": f"{STYLE_CANON} Scene 14: Dark vignette with only two warm golden lights pulsing in antiphase heartbeat rhythm: the foreground lantern and the distant lighthouse eye, intimate poetic tension.",
    },
    {
        "id": "15",
        "dur": 26.0,
        "name": "Die goldene Flut (Katharsis)",
        "prompt": f"{STYLE_CANON} Scene 15: Blinding glorious golden sunrise washing over the waking earth, dark stone statues disintegrating into sparkling golden dust scattered by the morning wind, blooming golden flora.",
    },
    {
        "id": "16",
        "dur": 10.0,
        "name": "Das innere Licht (Ich gebe nicht auf)",
        "prompt": f"{STYLE_CANON} Scene 16: Traveler at the cliff summit overlooking the radiant golden ocean, gently blowing out the lantern candle, bright warm inner golden light radiating from traveler's chest and heart.",
    },
    {
        "id": "17",
        "dur": 6.4,
        "name": "Ewiger Puls & Coda",
        "prompt": f"{STYLE_CANON} Scene 17: Aerial slow pull-back shot, tranquil turquoise and golden morning sea gently lapping against the lighthouse cliff, peaceful morning mist dissolving into pure warm white light.",
    },
]


def assemble_final_video():
    """Führt alle 17 Clips nach der exakten Beat-Grid-Tabelle mit ffmpeg zusammen."""
    logger.info("=== Starte finale Montage des Musikvideos ===")
    concat_list_file = CLIPS_DIR / "concat_list.txt"
    entries = []

    for sc in SCENES:
        sc_id = sc["id"]
        target_dur = sc["dur"]
        clip_path = CLIPS_DIR / f"scene_{sc_id}.mp4"

        # Falls Clip noch nicht vorhanden, Fallback auf vorgerenderte Clips oder animierte Frames
        if not clip_path.exists():
            fb_candidates = [
                FRAMES_DIR / "clips2" / f"seq{sc_id}.mp4",
                FRAMES_DIR / "clips_ph" / "norm" / f"seq{sc_id}.mp4",
                FRAMES_DIR / "clips_d" / "norm" / f"seq{sc_id}.mp4",
                FRAMES_DIR / f"scene_{sc_id}.png",
            ]
            for c in fb_candidates:
                if c.exists():
                    clip_path = c
                    break

        if clip_path.suffix.lower() == ".png":
            # Wandle Standbild für die Dauer in ein MP4 um
            temp_mp4 = CLIPS_DIR / f"temp_{sc_id}.mp4"
            cmd_img = [
                "ffmpeg", "-y", "-loop", "1", "-i", str(clip_path),
                "-t", str(target_dur), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-vf", "scale=1280:720,fps=24", str(temp_mp4)
            ]
            subprocess.run(cmd_img, check=True, capture_output=True)
            clip_path = temp_mp4

        # Auf Ziel-Dauer trimmen
        trimmed_mp4 = CLIPS_DIR / f"trimmed_{sc_id}.mp4"
        cmd_trim = [
            "ffmpeg", "-y", "-i", str(clip_path),
            "-t", str(target_dur),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24",
            "-an", str(trimmed_mp4)
        ]
        subprocess.run(cmd_trim, check=True, capture_output=True)
        entries.append(f"file '{trimmed_mp4.resolve().as_posix()}'")
        logger.info(f"Szene {sc_id} [{sc['name']}]: {target_dur}s vorbereitet.")

    with open(concat_list_file, "w", encoding="utf-8") as f:
        f.write("\n".join(entries) + "\n")

    final_video_out = FRAMES_DIR / "Пока_бьётся_клип_Google_Flow.mp4"
    logger.info(f"Führe zusammen nach: {final_video_out}")

    cmd_stitch = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list_file),
        "-i", str(SONG),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest", str(final_video_out)
    ]
    subprocess.run(cmd_stitch, check=True, capture_output=True)
    logger.info(f"FERTIG! Meisterwerk erfolgreich assembliert: {final_video_out}")
    return final_video_out


if __name__ == "__main__":
    assemble_final_video()
