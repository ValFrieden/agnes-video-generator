"""Agnes / Local clip pipeline — music video for "Беги за солнцем" (96.0 s).
Concept: Вариант A «Жёлтый зонт и город теней» (The Yellow Umbrella).

Style consistency:
  style      — canonical style anchor: begi_za_solntsem_frames/character_ref.jpg
  keyframes  — 12 scenes x 8.0s generated with strict style & palette locks
  contact    — 4x3 contact sheet for review
  videos     — animate each keyframe via image-to-video (8s per clip)
  stitch     — ffmpeg concat + song mux to 96.0s final video
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from core.api.google_flow_errors import FlowPendingError, FlowStoppedError

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

ROOT = Path(__file__).parent
VENV_SITE = ROOT / ".venv" / "Lib" / "site-packages"
if VENV_SITE.exists() and str(VENV_SITE) not in sys.path:
    sys.path.insert(0, str(VENV_SITE))

BIN = ROOT / "bin"
if BIN.exists() and str(BIN) not in os.environ.get("PATH", ""):
    os.environ["PATH"] = str(BIN) + os.pathsep + os.environ.get("PATH", "")

os.environ.setdefault("AGNES_VIDEO_QUEUE_RETRY_SECONDS", "3600")

FRAMES_DIR = ROOT / "begi_za_solntsem_frames"
SONG = FRAMES_DIR / "song.mp3"
SONG_LENGTH_S = 96.0
W, H, FPS = 1280, 720, 24
CLIP_S = 8

# Style block and laws
STYLE_BLOCK = (
    "Vintage hand-painted cel animation style, gouache painted backgrounds, "
    "cinematic wide 16:9, atmospheric film grain, wet reflections, Edward Hopper dramatic lighting, "
    "rich nostalgic textures, deep slate and warm amber gold palette, no text, no watermark"
)

CANON_CHAR = (
    "the same solitary traveler in a dark slate coat holding a vibrant glowing canary-yellow umbrella, "
    "bare face, no eyeglasses"
)

NEGATIVE = (
    "walking, running, leg movement, arm swing, head turning, mouth open, talking, singing, "
    "lip sync, warping, morphing, floating limbs, extra hands, jitter, flicker, low quality, "
    "photorealistic 3D, CGI, text, letters, watermark, logo, captions"
)

SCENES: list[dict] = [
    {
        "name": "01_bench_rain",
        "title": "Интро: Скамья под дождем",
        "prompt": (
            f"{STYLE_BLOCK}. A weathered wooden park bench soaked in rain on a wet city promenade, "
            "a closed vibrant canary-yellow umbrella lying on the bench planks, soft inner glow, "
            "stormy indigo twilight sky, rain puddles reflecting street lamps."
        ),
        "motion": (
            "Rain streaks falling smoothly, droplets splashing on wet bench wood, "
            "soft warm glow pulsing gently on the yellow umbrella fabric, static camera."
        ),
    },
    {
        "name": "02_take_umbrella",
        "title": "Куплет 1: Путник поднимает зонт",
        "prompt": (
            f"{STYLE_BLOCK}. Medium shot from behind: {CANON_CHAR}, standing still by the bench "
            "in misty rainfall, warm amber light radiating from beneath the open umbrella dome onto wet pavement."
        ),
        "motion": (
            "Misty rain drifting, gentle warm amber light pulsing under the umbrella, "
            "slight breathing motion of coat fabric, static traveler stance, no walking."
        ),
    },
    {
        "name": "03_cobblestone_sunbeam",
        "title": "Куплет 1: Первые лучи в лужах",
        "prompt": (
            f"{STYLE_BLOCK}. Low-angle shot of wet cobblestones: deep puddle mirror reflecting a dark stormy "
            "indigo sky, while a single sharp shaft of golden sunbeam cuts through the dark clouds, "
            "hitting the water surface with golden ripples."
        ),
        "motion": (
            "Concentric ripples expanding on the puddle surface, diagonal sunbeam steadily brightening "
            "and piercing deeper through dark water, static low camera."
        ),
    },
    {
        "name": "04_alley_guide",
        "title": "Прехорус: Солнце за луч держи",
        "prompt": (
            f"{STYLE_BLOCK}. Narrow European stone alleyway in cold drifting fog: {CANON_CHAR} stands "
            "facing forward, guided by a thick solid beam of golden sunlight piercing diagonally through the mist."
        ),
        "motion": (
            "Slow subtle cinematic push-in along the golden beam, low mist rolling slowly across wet stones, "
            "traveler stands perfectly still."
        ),
    },
    {
        "name": "05_open_window",
        "title": "Прехорус: Открыто окно",
        "prompt": (
            f"{STYLE_BLOCK}. Old brick town facade enveloped in cool gray rain: third floor round attic window "
            "flung wide open, warm amber golden sunlight and fluttering sheer curtains pouring out into the rain."
        ),
        "motion": (
            "Sheer white curtains gently fluttering in the warm window breeze, soft golden light blooming outward, "
            "rain falling in background."
        ),
    },
    {
        "name": "06_bridge_dawn",
        "title": "Припев 1: Граница тьмы и света",
        "prompt": (
            f"{STYLE_BLOCK}. Grand stone bridge over a misty river: {CANON_CHAR} stands centered at the border "
            "where stormy dark indigo clouds shatter into radiant golden sunrise."
        ),
        "motion": (
            "Golden dawn light expanding across clouds, warm god rays strengthening, slight fabric flutter in wind, "
            "traveler stands completely motionless."
        ),
    },
    {
        "name": "07_face_droplets",
        "title": "Припев 1: Решимость в глазах",
        "prompt": (
            f"{STYLE_BLOCK}. Close-up profile of the traveler's calm face, wet dark hair, warm determined eyes, "
            "rain droplets on cheek glistening like tiny amber jewels in intense golden side-lighting, no eyeglasses, lips closed."
        ),
        "motion": (
            "Subtle natural breathing, a single rain droplet trickles down the cheek, warm sunlight shimmer in eyes, "
            "mouth closed, static head."
        ),
    },
    {
        "name": "08_creeping_shadows",
        "title": "Куплет 2: Преследование тени",
        "prompt": (
            f"{STYLE_BLOCK}. Ancient stone arched colonnade: {CANON_CHAR} stands motionless, while behind on the "
            "wet stone pillars, massive creeping ink-like shadows stretch upward into the twilight."
        ),
        "motion": (
            "Dark ink shadows slowly creeping and stretching up stone pillars, cold fog swirling at ground level, "
            "traveler stands completely frozen."
        ),
    },
    {
        "name": "09_umbrella_shield",
        "title": "Куплет 2: Зонт-щит",
        "prompt": (
            f"{STYLE_BLOCK}. Medium shot: the traveler holds the glowing canary-yellow umbrella behind like a radiant "
            "shield, ink-black shadow mist slams against the glowing umbrella surface and shatters into thousands of glowing golden sparks."
        ),
        "motion": (
            "Pulsing radial burst of glowing golden sparks scattering outward from umbrella, dark mist vaporizing into light, "
            "motionless body."
        ),
    },
    {
        "name": "10_sun_through_umbrella",
        "title": "Припев 2: Солнце сквозь ткань",
        "prompt": (
            f"{STYLE_BLOCK}. Looking directly up through the translucent canary-yellow fabric of the open umbrella, "
            "the blazing white-gold sun glowing intensely right through the center of the dome, golden lens flare."
        ),
        "motion": (
            "Intense warm solar pulsing through yellow cloth, golden bokeh dust particles floating gently downward, "
            "subtle lens flare breathing."
        ),
    },
    {
        "name": "11_rooftop_conquest",
        "title": "Припев 2: Торжество золота",
        "prompt": (
            f"{STYLE_BLOCK}. High rooftop panoramic view: the sweeping front of warm golden sunlight rolling across "
            "wet slate rooftops, melting the last dark clouds, sparkling rain gutters, clear ultramarine sky opening up."
        ),
        "motion": (
            "Smooth slow pan across rooftops as warm golden sunlight sweeps forward, evaporating wet surfaces with sparkling highlights."
        ),
    },
    {
        "name": "12_sunny_bench",
        "title": "Финал / Кода: Вечное лето",
        "prompt": (
            f"{STYLE_BLOCK}. The same park bench from scene 01, now completely dry and drenched in brilliant warm midday "
            "summer sun, soft greenery and wildflowers blooming nearby, gentle sunny breeze, quiet triumphant peace."
        ),
        "motion": (
            "Warm summer breeze gently swaying nearby wildflower stems, shimmering golden sunlight on dry wood, serene stillness."
        ),
    },
]


def _log(msg: str) -> None:
    t = time.strftime("%H:%M:%S")
    line = f"[{t}] {msg}"
    print(line, flush=True)
    with open(FRAMES_DIR / "pipeline.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _scene_dir(i: int) -> Path:
    d = FRAMES_DIR / f"scene_{i+1:02d}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_api_key() -> str:
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except Exception:
        pass
    if not os.environ.get("AGNES_API_KEY") and (ROOT / ".env").exists():
        try:
            with open(ROOT / ".env", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("AGNES_API_KEY="):
                        os.environ["AGNES_API_KEY"] = line.split("=", 1)[1].strip()
                        break
        except Exception:
            pass
    return os.environ.get("AGNES_API_KEY", "")


async def stage_keyframes(indices: list[int], provider: str = "agnes") -> None:
    if provider == "flow":
        from core.api.google_flow import GoogleFlowAPI
        api = GoogleFlowAPI()
        _log("Using Google Flow provider for keyframes.")
    else:
        from core.api.agnes_image import AgnesImageAPI
        api_key = get_api_key()
        api = AgnesImageAPI(api_key=api_key)
    ref_path = FRAMES_DIR / "character_ref.jpg"

    for i in indices:
        sdir = _scene_dir(i)
        kf = sdir / "keyframe.png"
        flat_kf = FRAMES_DIR / f"scene_{i+1:02d}.png"
        if kf.exists() or flat_kf.exists():
            _log(f"Keyframe {i+1:02d} exists, skipping.")
            continue

        _log(f"Generating Keyframe {i+1:02d} [{SCENES[i]['name']}]...")
        try:
            ref_list = [str(ref_path)] if ref_path.exists() else []
            img = await api.generate_single_image(
                prompt=SCENES[i]["prompt"],
                reference_image_paths=ref_list,
                size="1280x720",
                negative_prompt=NEGATIVE,
            )
            await img.save(str(kf))
            # Also save flat copy for review
            await img.save(str(flat_kf))
            _log(f"Keyframe {i+1:02d} OK.")
        except Exception as e:
            _log(f"Keyframe {i+1:02d} FAILED: {e}")


def stage_contact() -> None:
    _log("Generating contact sheet...")
    from PIL import Image

    frames = []
    for i in range(len(SCENES)):
        flat_kf = FRAMES_DIR / f"scene_{i+1:02d}.png"
        kf = _scene_dir(i) / "keyframe.png"
        target = flat_kf if flat_kf.exists() else kf
        if target.exists():
            frames.append(target)

    if not frames:
        _log("No keyframes found to create contact sheet.")
        return

    tile_w, tile_h = 426, 240
    padding = 6
    cols, rows = 4, 3
    sheet_w = cols * tile_w + (cols + 1) * padding
    sheet_h = rows * tile_h + (rows + 1) * padding
    sheet = Image.new("RGB", (sheet_w, sheet_h), color=(0, 0, 0))

    for idx, p in enumerate(frames[:12]):
        c = idx % cols
        r = idx // cols
        x = padding + c * (tile_w + padding)
        y = padding + r * (tile_h + padding)
        try:
            with Image.open(p) as im:
                thumb = im.resize((tile_w, tile_h), Image.Resampling.LANCZOS)
                sheet.paste(thumb, (x, y))
        except Exception as e:
            _log(f"Failed to add {p} to contact sheet: {e}")

    out_sheet = FRAMES_DIR / "contact_sheet.png"
    sheet.save(out_sheet)
    _log(f"Contact sheet saved to {out_sheet}")


async def stage_videos(indices: list[int], model: str = "agnes-video-2.5-flash", provider: str = "agnes") -> None:
    if provider == "flow":
        from core.api.google_flow import GoogleFlowAPI
        api = GoogleFlowAPI()
        _log(f"Using Google Flow provider for video generation (Model: {model}).")
    else:
        from core.api.agnes_video import AgnesVideoAPI
        api_key = get_api_key()
        api = AgnesVideoAPI(api_key=api_key, model=model)

    for i in indices:
        sdir = _scene_dir(i)
        video = sdir / "video.mp4"
        flat_video = FRAMES_DIR / f"scene_{i+1:02d}.mp4"
        pending = sdir / "video.flow_pending.json"
        if video.exists() or flat_video.exists():
            _log(f"Video {i+1:02d} exists, skipping.")
            continue

        # Logikcheck Befund 3: Eine frühere Generierung wurde womöglich schon
        # genehmigt und bezahlt. Nicht erneut abschicken.
        if pending.exists():
            _log(
                f"Video {i+1:02d} pending in Flow ({pending.name}) — Clip in Flow prüfen, "
                "Marker löschen für einen neuen Versuch. Skipping."
            )
            continue

        kf = sdir / "keyframe.png"
        if not kf.exists():
            kf = FRAMES_DIR / f"scene_{i+1:02d}.png"
        if not kf.exists():
            _log(f"Video {i+1:02d} keyframe missing, skipping.")
            continue

        _log(f"Generating Video {i+1:02d} [{SCENES[i]['name']}] (8s)...")
        vprompt = (
            f"Animate gently: {SCENES[i]['motion']}. "
            f"Maintain {STYLE_BLOCK}. Camera smooth, no warping, mouth closed."
        )

        def on_video_progress(*args, **kwargs):
            if len(args) >= 2 and args[0] == "queue_full":
                info = args[1] if isinstance(args[1], dict) else {}
                waited = info.get("waited_s", 0)
                attempt = info.get("attempt", 0)
                _log(f"Video {i+1:02d} [queue_full]: attempt #{attempt}, waited {waited:.0f}s")
            elif len(args) >= 2:
                status, prog = args[0], args[1]
                _log(f"Video {i+1:02d} [{status}]: {prog}%")
            else:
                _log(f"Video {i+1:02d} progress: {args}")

        try:
            extra_kwargs = {}
            if provider == "flow":
                extra_kwargs["model"] = model
                extra_kwargs["output_folder"] = str(sdir)
            res = await api.generate_single_video(
                prompt=vprompt,
                reference_image_paths=[str(kf)],
                duration=CLIP_S,
                width=W,
                height=H,
                negative_prompt=NEGATIVE,
                progress_callback=on_video_progress,
                **extra_kwargs,
            )
            await res.save(str(video))
            shutil.copy2(video, flat_video)
            dur = 0.0
            try:
                from utils.video import get_video_duration
                dur = get_video_duration(str(video))
            except Exception:
                pass
            _log(f"Video {i+1:02d} OK ({dur:.1f}s, {video.stat().st_size // 1024} KiB).")
        except FlowStoppedError as e:
            # Flow hat nichts gestartet (Limit/Ablehnung/Aktivitätswarnung):
            # Guthaben unberührt, aber weitere Anfragen wären sinnlos oder
            # riskant → ganzen Stapel abbrechen.
            _log(f"Video {i+1:02d} STOPPED by Flow (status={e.status}): {e}")
            _log("Aborting remaining scenes — in Flow nachsehen.")
            return
        except FlowPendingError as e:
            # Genehmigt/unklar: Marker schreiben, nicht neu abschicken.
            _log(f"Video {i+1:02d} PENDING in Flow (status={e.status}): {e}")
            try:
                pending.write_text(
                    json.dumps(
                        {"status": e.status, "detail": str(e)[:500], "scene": i + 1},
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            except OSError as werr:
                _log(f"Could not write pending marker {pending}: {werr}")
            if video.exists():
                try:
                    video.unlink()
                except OSError:
                    pass
        except Exception as e:
            _log(f"Video {i+1:02d} FAILED: {type(e).__name__}: {e}")
            if video.exists():
                try:
                    video.unlink()
                except OSError:
                    pass


def stage_stitch() -> None:
    _log("Stitching 12 scenes into final clip with song.mp3...")
    concat_list = FRAMES_DIR / "concat_list.txt"
    entries = []
    for i in range(len(SCENES)):
        flat_v = FRAMES_DIR / f"scene_{i+1:02d}.mp4"
        s_v = _scene_dir(i) / "video.mp4"
        v = flat_v if flat_v.exists() else s_v
        if v.exists():
            entries.append(f"file '{v.resolve().as_posix()}'")
        else:
            _log(f"Warning: Scene {i+1:02d} video missing!")

    if len(entries) < len(SCENES):
        _log(f"Only {len(entries)}/{len(SCENES)} scenes available. Proceeding with available.")

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
        _log(f"Final clip successfully assembled: {final_out}")
        root_out = ROOT / "Беги_за_солнцем_клип_Желтый_зонт.mp4"
        shutil.copy2(final_out, root_out)
        _log(f"Copied final clip to: {root_out}")
    except subprocess.CalledProcessError as e:
        _log(f"Stitch failed: {e.stderr.decode('utf-8', errors='ignore')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline for 'Беги за солнцем' (Жёлтый зонт)")
    parser.add_argument("--stage", choices=["keyframes", "contact", "videos", "stitch", "all"], default="all")
    parser.add_argument("--scene", type=int, default=-1, help="Specific scene index 0..11")
    parser.add_argument("--provider", choices=["agnes", "flow"], default="agnes", help="Provider: 'agnes' or 'flow' (Google Flow Veo)")
    parser.add_argument("--model", type=str, default="", help="Model name (e.g. 'Veo 3.1 - Fast' for flow or 'agnes-video-2.5-flash')")
    args = parser.parse_args()

    default_model = "Veo 3.1 - Fast" if args.provider == "flow" else "agnes-video-2.5-flash"
    chosen_model = args.model or default_model

    indices = list(range(len(SCENES))) if args.scene < 0 else [args.scene]

    _log(f"=== Begi Clip Pipeline started | Stage: {args.stage} | Scenes: {indices} | Provider: {args.provider} | Model: {chosen_model} ===")
    if args.stage in ("keyframes", "all"):
        asyncio.run(stage_keyframes(indices, provider=args.provider))
    if args.stage in ("contact", "all"):
        stage_contact()
    if args.stage in ("videos", "all"):
        asyncio.run(stage_videos(indices, model=chosen_model, provider=args.provider))
    if args.stage in ("stitch", "all"):
        stage_stitch()
    _log("=== Begi Clip Pipeline finished ===")


if __name__ == "__main__":
    main()
