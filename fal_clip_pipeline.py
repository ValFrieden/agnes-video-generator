"""
fal.ai clip pipeline — "keyframe-first" with a consistent character.

Stages (each idempotent, skips existing outputs):
  sheet      — turn the real reference photo into an anime character sheet
               (portrait + full body) with Nano Banana 2
  keyframes  — generate one 16:9 keyframe per scene, always referencing the
               anime portrait so the character and style stay locked
  videos     — Vidu Q2 reference-to-video per scene (character ref + keyframe)
  stitch     — ffmpeg concat + song mux, trimmed to the song length

Usage:
  python fal_clip_pipeline.py --stage sheet
  python fal_clip_pipeline.py --stage keyframes --scene 0
  python fal_clip_pipeline.py --stage videos --scene 0        # smoke test
  python fal_clip_pipeline.py --stage all
  python fal_clip_pipeline.py --stage stitch

Cost (approx): sheet $0.16, keyframes $0.08 each, videos $0.30 each (720p).
Reads FAL_KEY from .env or the environment.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import subprocess
import sys
import time
import traceback
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
_RUN_LOG = ROOT / "pipeline_run.log"


def _logline(msg: str) -> None:
    with open(_RUN_LOG, "a", encoding="utf-8") as f:
        f.write(msg.rstrip() + "\n")


sys.excepthook = lambda t, v, tb: _logline(  # noqa: E731
    "FATAL " + "".join(traceback.format_exception(t, v, tb))
)

try:
    from dotenv import load_dotenv
except Exception:
    _logline("FATAL dotenv import:\n" + traceback.format_exc())
    raise

try:
    import fal_client
except ImportError:
    _logline("FATAL fal_client import:\n" + traceback.format_exc())
    sys.exit("fal_client is not installed: pip install fal-client")

load_dotenv(ROOT / ".env")
if not os.environ.get("FAL_KEY"):
    _logline("FATAL: FAL_KEY is not set in .env or environment")
    sys.exit("FAL_KEY is not set. Add FAL_KEY=<your-key> to .env or the environment.")
OUT = ROOT / "fal_out"
SONG = Path(r"C:\Users\Valeri\Downloads\Хочу навеки.mp3")
PHOTO = Path(r"D:\FotosVideos\Ich\682205f4ffa959531331ced2a9d0b148_b2cf1c80-ac61-4115-8d2b-309a757a7614.jpg")
REAL_PHOTO = Path(r"D:\FotosVideos\Pass\ValeriFriedland.jpg")
SONG_LENGTH_S = 173.2

NB2_EDIT = "fal-ai/nano-banana-2/edit"
H3_MAX_I2V = "minimax/h3-max/image-to-video"
H3_REF2V = "minimax/h3-max/reference-to-video"
KLING_O3_I2V = "fal-ai/kling-video/o3/standard/image-to-video"
VEO31_FLF = "fal-ai/veo3.1/fast/first-last-frame-to-video"
WAN_ANIMATE_REPLACE = "fal-ai/wan/v2.2-14b/animate/replace"

STYLE = (
    "vintage hand-drawn cel animation in a classic mid-century cartoon style, whimsical "
    "retro-futuristic space-age aesthetics: hand-painted gouache backgrounds, flat cel-shaded "
    "characters with clean dark outlines, warm nostalgic palette, gentle exaggerated cartoon "
    "motion, painted planets and rockets"
)
NO_SYMBOLS = (
    "No state symbols of any kind: no flags, no emblems, no coats of arms, no red stars, "
    "no CCCP/USSR lettering, no insignia. All clothing, suits and rockets are completely "
    "plain and unmarked: no patches, no badges, no medals, no ribbons."
)

# The recurring character anchor, referenced verbatim in every scene prompt.
CHARACTER = (
    "the same man: early 40s, short dark brown hair, slight stubble, warm hazel eyes, "
    "olive-green collared shirt; he does NOT wear glasses - never draw eyeglasses on him, "
    "his bare eyes are always clearly visible"
)

SHEET_PROMPT = (
    "The attached sheet is a multi-angle photographic reference of the SAME man (front view, "
    "profile view, close-ups of eye and ear). Transform him into a hand-painted cel-animated "
    f"cartoon character ({STYLE}), keeping his face clearly recognizable: early 40s, short "
    "brown hair, light stubble, warm hazel eyes (NO GLASSES - eyes always bare), "
    "olive-green collared shirt. Portrait, chest-up, "
    "facing the camera, soft warm light, plain muted background. Ignore any caption text printed "
    f"on the reference sheet. {NO_SYMBOLS} One image."
)

# Music-snapped storyboard: scene boundaries were measured from the actual
# audio (energy jumps): chorus chant at 42 s, echo-pause 58-63 s, chorus 2 at
# 64 s, peak 129 s, bridge 146-150 s, final chorus explosion at 150 s, end 173 s.
# Durations vary (4-15 s allowed by H3 Max) so cuts land ON the music.
# WARDROBE LAW: olive-green shirt in scenes 0-1; in scene 2 he puts on the plain
# white space suit ONCE and wears it for the rest of the clip (never removes it);
# the round helmet appears only in scene 20 (match in open space), under his arm.
# MOUTH LAW: the hero NEVER speaks: mouth gently closed in every scene, no
# lip-sync, no singing. The "Пожалуй, лучше помолчу" beat (scene 10) is a
# SILENT gesture: finger to lips, closed mouth, warm smile.
SCENES: list[dict] = [
    # 0-10 INTRO: transformation — чудо и лёгкая грусть расставания с «настоящестью»
    {"dur": 10, "key": "The real photograph comes alive: it takes a soft breath - a moment of quiet melancholy, as if the photo itself is saying goodbye to being just paper - then warm color washes and fine ink lines bloom outward from the heart by themselves; his face lights up with shy wonder as it becomes a hand-painted cartoon; stars and planets ignite one by one around him like small hopes; slow tender push-in; no hands, no brushes.", "move": "small"},
    # 10-18 VERSE 1 — уют, одиночество, мечта
    {"dur": 8, "key": "Cozy but lonely hand-painted spaceship cabin, medium shot from behind his shoulder: the hero in his OLIVE-GREEN SHIRT sits at the wooden desk sketching a dancing couple under stars - the dream he is too shy to live yet; a single warm lamp against the big dark porthole full of stars; Saturn and a small clean rocket drift outside; his shoulders slightly hunched, tender concentration, a faint wistful smile; the camera drifts slowly sideways like a quiet thought.", "move": "small"},
    # 18-26 VERSE 1 — прощание с котом. Без люка в кадре (модель его
    # «оживляла» и отрывала) и камера со спины: рта нет, спина гладкая.
    {"dur": 8, "cut": True, "key": "Seen from BEHIND inside a cozy painted spaceship cabin: the hero in his pristine PLAIN WHITE SPACE SUIT - bare head with visible hair, no helmet - kneels on the floor and waves goodbye to the orange tabby cat sitting on its pillow; we see his back and the smooth flawless back panel of the suit, no folds, no tears; the cat raises a paw toward him; warm amber light; on the wall only a round porthole window with quiet stars, no doors, no hatches.", "move": "small"},
    # 26-34 VERSE 1 end — решимость. Жёсткий монтаж на бите 26 с: прощание
    # кончилось — снаружи ракета на столе. Морфить интерьер→экстерьер нельзя.
    {"dur": 8, "cut": True, "key": "Exterior wide shot, NO people visible anywhere: the retro fin rocket with a clean unmarked hull lifts off from a gouache-painted cosmodrome tower; doodle clouds part like curtains; a soft orange flame trails like a comet; the camera tilts up following the rocket into the immense starry black sky - a tiny brave light rising alone, equal parts fear and hope.", "move": "large"},
    # 34-42 PRE-CHORUS — нежное нарастание. Смена локации (снаружи→внутри)
    # — жёсткий монтаж на бите 34 с, без морфинга.
    {"dur": 8, "cut": True, "key": "Inside the orbital station, zero gravity: the hero in the plain white space suit, BARE-HEADED, floats gently past the big porthole; the painted Earth glows blue and impossibly beautiful below; he presses one glove lightly to the glass; the Earth's soft blue reflection glides across his calm face; childlike wonder mixed with aching tenderness, eyes wide, mouth gently closed; the light slowly warms as the music builds.", "move": "small"},
    # 42-50 CHORUS EXPLODES — встреча ровно на 42-й. Безлицевой крупный
    # план (только руки) + жёсткий монтаж на бите.
    {"dur": 8, "cut": True, "no_refs": True,
     "kf": "Extreme close-up, one single frame: exactly TWO white-gloved hands - only the hands, no arms above the wrist, no faces, no bodies - fingertips just TOUCHING in mid-air, golden sparks bursting softly from the point of contact like tiny fireworks; dark blue space with faint painted stars behind; plain smooth white gloves and sleeves without grey bands; no flags, no emblems, no lettering.",
     "qc": "This keyframe shows ONLY a close-up of two gloved hands touching - no face, no head, no body are visible. Do NOT fail for a missing face, head, hair, helmet or shirt. Grey ribbed cuffs at the wrists are ACCEPTABLE (classic spacesuit detail). FAIL only for: torn or damaged suit fabric, any flag/emblem/red star/medal/inscription/lettering, extra hands (more than two), or a paintbrush.",
     "key": "ON THE BEAT: slow-motion extreme close-up of two gloved hands finally TOUCHING after longing - his and the girl astronaut's - and golden sparks burst from the touch like tiny fireworks; the sparks grow into a swirling ribbon of golden light that gently wraps around both wrists, then fills the whole frame with a warm golden glow - the light itself becomes the transition into the dance. No faces, no bodies, no rockets.", "move": "small"},
    # 50-58 CHORUS — хоровод желаний
    {"dur": 8, "key": "Zero-gravity round dance of desires in full swing: the hero and the girl spin together in the center while a paper star, a heart, a book, a violin and a loaf of bread orbit them on strings of light - every simple wish he ever had, dancing around him at last; confetti-stars drift upward; orbiting camera, big joyful motion, warm golden light.", "move": "medium"},
    # 58-64 ECHO-PAUSE — тихая грусть внутри счастья
    {"dur": 6, "key": "The echo pause: everything slows into a dreamy drift - the dancing pair floats almost motionless in the middle of the bay, forehead resting against forehead, desire-objects hanging weightless around them; star-lamps blink softly in rhythm with the sparse beats; a moment of fragile quiet happiness, held breath, cool blue palette with warm faces.", "move": "small"},
    # 64-72 CHORUS 2 — счастье заразительно
    {"dur": 8, "key": "The mess module bursts into celebration: friends around a floating table laugh with him - he laughs silently too, shoulders shaking, eyes squinting with joy, mouth closed, all the earlier loneliness gone; tea cups, a little samovar and spoons dance in zero gravity; warm lanterns, paper garlands; camera circles the table briskly.", "move": "medium"},
    # 72-80 слёзы радости + беззвучное «помолчу»
    {"dur": 8, "key": "He cries with joy: cartoon fountains of tears lift off his eyes, freeze into glassy beads, and bright flowers bloom in the air wherever the beads drift; he catches one flower and holds it to his chest - then, as the chorus ends, he softly raises one finger to his CLOSED lips in a gentle shh gesture with a warm trembling smile: some feelings are too big for words; tender pink-blue palette.", "move": "medium"},
    # 80-88 VERSE 2 — письмо домой, нежность
    {"dur": 8, "key": "At the porthole desk he writes a letter home with a quill pen, smiling sadly at the page - the ink still wet like tears; the letter is for everyone he loves; warm intimate lamplight, quiet concentration, mouth closed, the Earth shining softly beyond the glass.", "move": "small"},
    # 88-96 VERSE 2 — буквы улетают к звёздам
    {"dur": 8, "key": "The ink letters hop off the page like little black birds and dance around the lamp; one by one they slip out of the porthole into open space and the camera follows them: they fly past painted planets, rings and comets, joining the stars - small messages becoming eternal lights; a wondrous bittersweet journey.", "move": "medium"},
    # 96-104 PRE-CHORUS 2 — она идёт к нему сквозь цветы
    {"dur": 8, "key": "She comes to him: the girl astronaut floats slowly among the zero-gravity flowers toward him, both smiling with closed mouths, her hand stretched out; soft golden light grows as she approaches; tender slow motion - the quiet miracle of being found.", "move": "small"},
    # 104-112 PRE-CHORUS 2 peak — «не отпускать»
    {"dur": 8, "key": "Their gloved hands clasp and hold - never letting go, fingers tightening gently - as a warm EARTHRISE glows behind the porthole; foreheads almost touching, two suited figures silhouetted in gold; around them the carousel of desires quietly begins to spin, gathering speed with the music and with their heartbeat.", "move": "medium"},
    # 112-120 CHORUS chant 2 — все свои
    {"dur": 8, "key": "Zero-gravity round dance of the whole crew: the cat in a tiny bubble helmet, a postman on a mini-rocket, kids in bubble helmets join the hero and the girl circling the bay; everyone dances joyfully, all mouths closed in smiles; nobody is alone anymore; lively wide shot, warm gold.", "move": "medium"},
    # 120-129 кольцо вокруг Луны
    {"dur": 9, "key": "The carousel of desires grows into a great luminous ring around the painted Moon; garlands of paper lanterns string themselves between small satellites; the dance widens into a cosmic celebration under the moonlight; sweeping crane shot, breathless joy.", "move": "large"},
    # 129-138 PEAK — весь город-станция
    {"dur": 9, "key": "The whole station-city joins the dance: windows light up like smiles, silhouettes dance on the hull and rooftops of the painted orbital station, the starry dome rotates above; the biggest, brightest celebration of the clip - joy shared is joy doubled; grand aerial shot, warm gold and blue.", "move": "large"},
    # 138-146 спад — тёплое послесвечение и первая тень грусти
    {"dur": 8, "key": "The carnival gently winds down: dancers slow into soft floating embraces, lanterns dim to amber, confetti-stars settle like snow; the hero holds the girl's hand and watches the last lantern glow - happiness with a shadow of knowing it cannot last forever; slowing camera, afterglow palette.", "move": "small"},
    # 146-150 BRIDGE: внезапная тишина, мир устал
    {"dur": 4, "key": "SUDDEN STILLNESS: the great cosmic machinery stops - giant painted gears squat frozen, smoke halts mid-puff, the star-lamps of the sky go out one by one as if the universe closed its eyes to sleep; deep blue-violet silence, vast and a little lonely; wide quiet shot, almost monochrome.", "move": "small"},
    # 150-158 FINAL CHORUS: спичка на взрыве +17dB — «я не уйду»
    {"dur": 8, "key": "ON THE EXPLOSION OF THE FINAL CHORUS: in the dark stillness the hero floats alone in open space, the round helmet tucked UNDER HIS ARM, and strikes a single match - one small warm flame trembling against the endless black, lighting his determined tender face - and from that flame the stars ignite one after another across the whole sky, warmth racing from star to star like a promise kept: he stayed; triumphant light rising through tears.", "move": "medium"},
    # 158-166 финальный хоровод — слёзы и смех вместе
    {"dur": 8, "key": "The relit universe blooms: pink and golden gouache dawn breaks over the curve of the painted Earth, all the characters return to the final round dance in full color - cosmonauts, the cat, the postman, kids, the couple in the center - dancing and laughing with shining tearful eyes, then turning to wave goodbye straight at the viewer; the warmest, most joyful, most tearful shot of the film.", "move": "large"},
    # 166-173 OUTRO: занавес и настоящее фото — тихий финал
    {"dur": 7, "key": "A heavy velvet theater curtain slowly closes over the cosmos like a mother tucking in a child; below the closed curtain hangs a small oval frame with the REAL photograph of the man - young, alive, real; a soft spotlight warms the photo; one last star twinkles on the curtain, refusing to go out, and everything fades to black.", "move": "small"},
]


def _data_uri(path: Path) -> str:
    mime = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"


def _nb2_edit(prompt: str, image_paths: list[Path], out_path: Path,
              aspect: str = "16:9", resolution: str = "1K") -> Path:
    """One Nano Banana 2 edit call; downloads the first result image."""
    if out_path.exists():
        print(f"  skip (exists): {out_path.name}")
        return out_path
    args = {
        "prompt": prompt,
        "num_images": 1,
        "aspect_ratio": aspect,
        "resolution": resolution,
        "output_format": "png",
    }
    if image_paths:
        args["image_urls"] = [_data_uri(p) for p in image_paths]
    print(f"  NB2 edit -> {out_path.name} ...")
    result = fal_client.subscribe(NB2_EDIT, arguments=args)
    url = result["images"][0]["url"]
    urllib.request.urlretrieve(url, out_path)
    return out_path


def _extract_last_frame(video_path: Path, out_path: Path, duration_s: float) -> None:
    """Grab the final frame of a rendered clip (used to chain the next scene)."""
    if out_path.exists():
        return
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-ss", f"{max(0, duration_s - 0.4):.1f}",
         "-i", str(video_path), "-frames:v", "1", str(out_path)],
        check=True,
    )


def _scene_video(scene_idx: int) -> Path:
    """Render one scene with Kling O3 as a chained first->last frame morph.

    start = last frame of the previous scene (or the real photo for scene 0)
    end   = this scene's approved keyframe

    Anchoring both ends of every scene to consistent stills is what keeps
    the hero's face stable across the whole clip.
    """
    vdir = OUT / f"scene_{scene_idx:02d}"
    vdir.mkdir(parents=True, exist_ok=True)
    video_path = vdir / "video.mp4"
    last_frame = vdir / "last_frame.jpg"
    scene = SCENES[scene_idx]
    if video_path.exists():
        print(f"  skip (exists): {video_path}")
        _extract_last_frame(video_path, last_frame, SCENES[scene_idx]["dur"])
        return video_path

    if scene_idx == 0:
        start = vdir / "start_frame.jpg"
        if not start.exists():
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", str(REAL_PHOTO),
                 "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
                 "-q:v", "2", str(start)],
                check=True,
            )
        action = "The photograph comes alive and transforms into a hand-drawn cartoon."
    elif scene.get("cut"):
        # Жёсткий монтажный переход: сцена стартует с собственного стартового
        # кадра (не с последнего кадра предыдущей) — смена костюма/локации
        # происходит «за кадром», на музыкальном бите. Стартовый кадр
        # генерируется из ТЕКСТА САМОЙ СЦЕНЫ (никаких шаблонных деталей).
        start = vdir / "start_frame.jpg"
        if not start.exists():
            if scene.get("kf"):
                start_desc = (
                    f"Frame from the same painted world, a moment BEFORE this image: "
                    f"{scene['kf']} - but calm and static: everything is a few centimeters "
                    "apart and not yet touching, no sparks yet, no motion, weightless "
                    "stillness."
                )
                style_ref = vdir / "keyframe.png"
                _nb2_edit(
                    f"{start_desc} Style: {STYLE}. {NO_SYMBOLS} No captions, no watermark.",
                    [style_ref],
                    start,
                )
            else:
                _nb2_edit(
                    f"Frame from the same painted scene, a moment BEFORE the main action "
                    f"begins: {scene['key']} - but nothing has started moving yet: the "
                    f"situation is calm and static, no flame, no dust, no motion. "
                    f"{_wardrobe_rule(scene_idx)} Style: {STYLE}. {_mouth_rule(scene_idx)} "
                    f"{NO_SYMBOLS} No captions, no watermark.",
                    [vdir / "keyframe.png", OUT / "character_portrait.png"],
                    start,
                )
        action = "A fresh shot begins on the music beat; continue the motion naturally."
    else:
        prev_last = OUT / f"scene_{scene_idx - 1:02d}" / "last_frame.jpg"
        if not prev_last.exists():
            raise FileNotFoundError(
                f"previous scene last frame missing: {prev_last} (scenes must render in order)"
            )
        start = prev_last
        action = "Continue the motion naturally from this frame."

    prompt = (
        f"IMPORTANT: every space suit in this video is a completely plain, blank white suit - "
        f"absolutely no patches, no badges, no flags, no emblems, no marks; bare smooth white "
        f"fabric only. {_wardrobe_rule(scene_idx)} {_mouth_rule(scene_idx)} "
        f"{action} Scene: {scene['key']} Style: {STYLE}. Main character: {CHARACTER}. "
        "Smooth cinematic camera, consistent character identity, "
        f"{NO_SYMBOLS} no captions, no watermark."
    )
    args: dict
    attempts = 2
    for attempt in range(1, attempts + 1):
        if scene.get("engine") == "veo31":
            args = {
                "prompt": prompt[:2500],
                "first_frame_url": _data_uri(start),
                "last_frame_url": _data_uri(vdir / "keyframe.png"),
                "duration": "8s",
            }
            print(f"  Veo 3.1 Fast first-last scene {scene_idx} ...")
            result = fal_client.subscribe(VEO31_FLF, arguments=args)
        else:
            # MAXIMUM REFERENCE STACK (fal guide: each reference gets a job):
            # Image 1 = identity portrait, Image 2 = costume full body,
            # Image 3 = back view (для спинных ракурсов),
            # Video 1 = предыдущая сцена как motion/appearance reference.
            refs = [
                _data_uri(OUT / "character_portrait.png"),
                _data_uri(OUT / "character_fullbody.png"),
            ]
            back = OUT / "character_back.png"
            ref_jobs = (
                "Use Image 1 as a strict IDENTITY reference: preserve the exact same face, "
                "short dark brown hair, light stubble, warm hazel eyes, NO glasses, and the "
                "olive-green shirt collar. Use Image 2 as the COSTUME reference: the plain "
                "blank white space suit worn over the olive-green shirt."
            )
            if back.exists():
                refs.append(_data_uri(back))
                ref_jobs += (
                    " Use Image 3 as the BACK-VIEW reference: whenever the man is seen from "
                    "behind, his back, hair and suit must match Image 3 exactly."
                )
            if scene_idx > 0 and not scene.get("cut"):
                prev_clip = OUT / f"scene_{scene_idx - 1:02d}" / "video.mp4"
                if prev_clip.exists():
                    refs.append(_data_uri(prev_clip))
                    ref_jobs += (
                        " Use Video 1 as the MOTION and APPEARANCE reference: the hero in "
                        "motion must look and move exactly like the character in Video 1, "
                        "same face in every frame."
                    )
            args = {
                "prompt": (ref_jobs + " " + prompt)[:7000],
                "reference_image_urls": refs[:9],
                "image_url": _data_uri(start),
                "end_image_url": _data_uri(vdir / "keyframe.png"),
                "duration": scene["dur"],
                "resolution": "480P",
                "prompt_expansion_mode": "disabled",
            }
            print(
                f"  MiniMax H3 Max ref2v scene {scene_idx} "
                f"({len(refs)} refs + start->keyframe) ..."
            )
            result = fal_client.subscribe(H3_REF2V, arguments=args)
        urllib.request.urlretrieve(result["video"]["url"], video_path)
        _extract_last_frame(video_path, last_frame, scene["dur"])
        _qa_frames(scene_idx, video_path, scene["dur"])
        if _qc_video(scene_idx, video_path, attempt):
            break
        if attempt == attempts:
            raise SystemExit(
                f"[VQC] scene {scene_idx:02d} video failed identity/quality twice "
                "- manual review required"
            )
        print(f"  [VQC] scene {scene_idx:02d}: regenerating video (attempt {attempt + 1})")
        video_path.unlink(missing_ok=True)
        last_frame.unlink(missing_ok=True)
    return video_path


def _qc_video(scene_idx: int, video_path: Path, attempt: int) -> bool:
    """VIDEO QC GATE: identity + suit integrity + silence + no symbols.

    Runs AFTER a video is generated, BEFORE it is accepted. Agnes vision
    compares QA frames (30/50/70%) against the anchor portrait. A FAIL
    triggers one automatic regeneration with a corrective hint.
    """
    from core.api.agnes_chat import AgnesChatAPI

    api_key = os.environ.get("AGNES_API_KEY", "")
    if not api_key:
        load_dotenv(ROOT / ".env")
        api_key = os.environ.get("AGNES_API_KEY", "")
    if not api_key:
        print("  [VQC] SKIP (no AGNES_API_KEY)")
        return True

    qa = [str(OUT / "preview" / f"qa_s{scene_idx:02d}_{f}.jpg") for f in (30, 50, 70)]
    qa = [p for p in qa if os.path.exists(p)]
    if not qa:
        print("  [VQC] SKIP (no qa frames)")
        return True
    system = (
        "You are a strict continuity supervisor. IMAGE 1 is the canonical character "
        "reference portrait. The following images are frames from one generated video "
        "clip. A shot where the face is not visible at all (hands close-up, back view, "
        "wide shot) is intentional and fine. "
        "Answer ONLY one line: 'PASS - <short>' or 'FAIL - <reason>'. "
        "FAIL if ANY frame shows: a man whose hair, build or silhouette clearly does "
        "not match IMAGE 1 (e.g. much longer or fluffier hair); eyeglasses; an open "
        "mouth as if speaking or singing; a torn, holed, ripped or damaged space suit; "
        "a detached, flying, floating or moving door/hatch/lid; any flag, emblem, red "
        "star, medal, ribbon, badge or lettering; a paintbrush or hand painting over "
        "his face."
    )
    user = "Reference portrait first, then the video frames. Judge now."
    try:
        chat = AgnesChatAPI(api_key=api_key)
        verdict = chat.chat_multimodal(system, user, [str(OUT / "character_portrait.png")] + qa)
    except Exception as e:
        print(f"  [VQC] WARN check failed ({e}); treat as PASS, review manually")
        return True
    verdict = (verdict or "").strip().splitlines()[0] if verdict else ""
    ok = verdict.upper().startswith("PASS")
    print(f"  [VQC] scene {scene_idx:02d} (attempt {attempt}): {verdict[:170]}")
    return ok


def _qa_frames(scene_idx: int, video_path: Path, duration_s: float) -> None:
    """Identity QA: extract frames at 25/50/75% for visual review.

    The hero must look the same (face, hair, stubble, olive collar / blank
    white suit) at every point of every clip; these frames are reviewed
    before a scene is accepted.
    """
    qa_dir = OUT / "preview"
    qa_dir.mkdir(exist_ok=True)
    for frac in (0.1, 0.3, 0.5, 0.7, 0.9):
        t = duration_s * frac
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video_path),
             "-frames:v", "1", str(qa_dir / f"qa_s{scene_idx:02d}_{int(frac * 100)}.jpg")],
            check=True,
        )


def stage_sheet() -> None:
    OUT.mkdir(exist_ok=True)
    print("[sheet] photo -> anime character sheet")
    _nb2_edit(SHEET_PROMPT, [PHOTO], OUT / "character_portrait.png", aspect="3:4")
    _nb2_edit(
        f"Same man as in the reference sheet, same art style, now full body, wearing a plain "
        "white vintage space suit over the olive-green shirt: BARE HEAD with visible hair - "
        "absolutely NO helmet, no glass dome, no neck ring, no collar ring; the suit is "
        "completely smooth plain white WITHOUT grey bands on cuffs or collar; standing in "
        "three-quarter view, same face, plain muted background. "
        f"Ignore any caption text on the reference sheet. {NO_SYMBOLS}",
        [OUT / "character_portrait.png", PHOTO],
        OUT / "character_fullbody.png",
        aspect="3:4",
    )
    _nb2_edit(
        f"Same man as in the reference sheet, same art style, now seen strictly FROM BEHIND "
        "(full back view: back of the head, back of the plain white space suit, smooth "
        "unmarked fabric), standing, same build, plain muted background. "
        f"{NO_SYMBOLS} Ignore any caption text on the reference sheet.",
        [OUT / "character_portrait.png", OUT / "character_fullbody.png"],
        OUT / "character_back.png",
        aspect="3:4",
    )


def _qc_keyframe(i: int, kf: Path) -> bool:
    """QC GATE: verify a keyframe BEFORE any video money is spent.

    Uses the free Agnes multimodal chat to compare the keyframe against the
    character anchor portrait. Checks identity (same face/hair/stubble, NO
    GLASSES), wardrobe correctness for this scene, and absence of state
    symbols. Returns True on PASS. Failures are logged with the reason.
    """
    from core.api.agnes_chat import AgnesChatAPI

    api_key = os.environ.get("AGNES_API_KEY", "")
    if not api_key:
        load_dotenv(ROOT / ".env")
        api_key = os.environ.get("AGNES_API_KEY", "")
    if not api_key:
        print("  [QC] SKIP (no AGNES_API_KEY)")
        return True

    expected_outfit = _wardrobe_rule(i)
    s = SCENES[i]
    if s.get("qc"):
        # Безлицевые планы (руки/дальний) — своё правило вместо проверки костюма.
        system = (
            "You are a strict art director for an animated film. Judge the candidate "
            "keyframe. Answer ONLY with a single line in this format: "
            "PASS - <one short sentence>  or  FAIL - <reason>. "
            f"Rule for this shot: {s['qc']}"
        )
        user = "Candidate keyframe. Judge now."
        qc_images = [str(kf)]
    else:
        system = (
            "You are a strict art director for an animated film. Compare two images: "
            "IMAGE 1 is the canonical character reference portrait; IMAGE 2 is a candidate "
            "keyframe. Answer ONLY with a single line in this format: "
            "PASS - <one short sentence>  or  FAIL - <reason>. "
            "If IMAGE 2 shows NO FACE AT ALL (hands close-up, back view, wide shot where the "
            "character is tiny or absent), that view is INTENTIONAL: PASS if there are no "
            "rule violations. "
            "Otherwise FAIL if: the man is not recognizably the same person as IMAGE 1 "
            "(face shape, hairline, stubble); he wears eyeglasses or sunglasses (he NEVER "
            "wears glasses); his mouth is open or he is speaking/singing; the space suit "
            "shows any tear, hole, rip or damage; his outfit does not match this "
            f"requirement: '{expected_outfit}'; any flag, emblem, red star, medal, ribbon, "
            "badge or lettering appears anywhere; a hand or paintbrush is painting over "
            "his face."
        )
        user = "IMAGE 1 = reference portrait. IMAGE 2 = candidate keyframe. Judge now."
        qc_images = [str(OUT / "character_portrait.png"), str(kf)]
    try:
        chat = AgnesChatAPI(api_key=api_key)
        verdict = chat.chat_multimodal(
            system, user, qc_images
        )
    except Exception as e:  # QC не должен ронять пайплайн — ошибка = ручная проверка
        print(f"  [QC] WARN check failed ({e}); treat as PASS, review manually")
        return True
    verdict = (verdict or "").strip().splitlines()[0] if verdict else ""
    ok = verdict.upper().startswith("PASS")
    print(f"  [QC] scene {i:02d}: {verdict[:160]}")
    if not ok:
        # одна автоперегенерация ключа с корректирующей подсказкой
        print(f"  [QC] scene {i:02d}: FAIL -> regenerating keyframe with corrective hint")
        kf.unlink(missing_ok=True)
        hint = (
            f"CRITICAL FIX: {verdict[:200]}. Redraw the frame following ALL rules strictly. "
            f"{expected_outfit} The man NEVER wears glasses. {NO_SYMBOLS}"
        )
        if s.get("no_refs"):
            _nb2_edit(f"{s['kf']} {hint}", [], kf)
        else:
            _nb2_edit(
                f"{_keyframe_prompt(i)} {hint}",
                [OUT / "character_portrait.png", OUT / "character_fullbody.png"],
                kf,
            )
        try:
            verdict2 = chat.chat_multimodal(system, user, qc_images)
            verdict2 = (verdict2 or "").strip().splitlines()[0] if verdict2 else ""
            ok2 = verdict2.upper().startswith("PASS")
            print(f"  [QC] scene {i:02d} retry: {verdict2[:160]}")
            return ok2
        except Exception:
            return True
    return ok


def stage_keyframes(indices: list[int]) -> None:
    (OUT / "scene_00").mkdir(parents=True, exist_ok=True)
    for i in indices:
        s = SCENES[i]
        kf = OUT / f"scene_{i:02d}" / "keyframe.png"
        kf.parent.mkdir(parents=True, exist_ok=True)
        print(f"[keyframes] scene {i:02d}/{len(SCENES) - 1}")
        if s.get("no_refs"):
            # Безлицевые/безобъектные кадры: якоря героя только вредят.
            # NB2 требует >=1 входную картинку — даём ключ предыдущей сцены
            # как референс стиля (палитры/гуаши), не персонажа.
            style_ref = OUT / f"scene_{i - 1:02d}" / "keyframe.png"
            if not style_ref.exists():
                style_ref = OUT / "character_back.png"
            _nb2_edit(s["kf"], [style_ref], kf)
        else:
            _nb2_edit(
                _keyframe_prompt(i),
                [OUT / "character_portrait.png", OUT / "character_fullbody.png"],
                kf,
            )
        if not _qc_keyframe(i, kf):
            raise SystemExit(
                f"[QC] scene {i:02d} keyframe failed twice - fix manually before video"
            )


def _wardrobe_rule(i: int) -> str:
    if i == 3:
        # Стартовый широкий план: людей в кадре нет вообще.
        return "No people are visible in this shot - only the rocket, the tower and the sky."
    if i <= 1:
        return "He wears his olive-green shirt, no spacesuit."
    suit = "He wears the plain blank white space suit over the olive-green shirt"
    if i == 20:
        suit += ", the round helmet held under his arm (face fully visible)"
    else:
        suit += ", bare-headed, no helmet"
    return suit + ". He put this suit on once and never takes it off - do not change or remove it."


def _mouth_rule(i: int) -> str:
    rule = ("The hero is completely silent: mouth gently closed or softly smiling, "
            "no talking, no lip-sync, no visible speech, no singing, ever.")
    if i == 10:
        rule += (" For the closing beat he raises one finger to his CLOSED lips in a gentle "
                 "shh gesture with a warm smile - still completely silent.")
    return rule


def _keyframe_prompt(i: int) -> str:
    """Prompt for the approved keyframe of scene i (scene 0 is special)."""
    s = SCENES[i]
    if i == 0:
        # End frame of the transformation: fully painted, no hands or brushes
        # (a hand painting over the face reads as "smearing" in motion).
        return (
            f"16:9 cinematic frame: the man fully hand-painted as a cel cartoon character, "
            f"chest-up portrait against a painted deep-space background with stars and planets. "
            f"Main character: {CHARACTER}. Style: {STYLE}. {NO_SYMBOLS} "
            "No hands, no brushes, no canvas edges, no captions."
        )
    return (
        f"Frame from a vintage hand-drawn cel-animated cartoon, {STYLE}. "
        f"Flat cel-shaded characters over a hand-painted gouache background, wide 16:9 frame. "
        f"Main character: {CHARACTER}. {_wardrobe_rule(i)} {_mouth_rule(i)} "
        "No cameras, no filming equipment, no microphones inside the scene. "
        f"Keep his face exactly consistent with the references. Scene: {s['key']} {NO_SYMBOLS}"
    )


def stage_videos(indices: list[int]) -> None:
    for i in indices:
        print(f"[videos] scene {i:02d}/{len(SCENES) - 1}")
        _scene_video(i)


def stage_stitch() -> None:
    videos = [OUT / f"scene_{i:02d}" / "video.mp4" for i in range(len(SCENES))]
    missing = [v for v in videos if not v.exists()]
    if missing:
        sys.exit(f"Missing scene videos: {len(missing)} (e.g. {missing[0]})")

    print("[stitch] normalizing + concat")
    norm_dir = OUT / "normalized"
    norm_dir.mkdir(exist_ok=True)
    norm = []
    for i, v in enumerate(videos):
        nv = norm_dir / f"scene_{i:02d}.mp4"
        if not nv.exists():
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", v,
                 "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                 "-r", "24", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                 "-pix_fmt", "yuv420p", "-an", nv],
                check=True,
            )
        norm.append(nv)

    concat_list = norm_dir / "list.txt"
    concat_list.write_text("".join(f"file '{n.as_posix()}'\n" for n in norm), encoding="utf-8")
    silent = OUT / "concat.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", concat_list,
         "-c", "copy", silent],
        check=True,
    )

    print("[stitch] muxing song")
    final = ROOT / "Хочу навеки — fal clip.mp4"
    fade_start = SONG_LENGTH_S - 3
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-i", silent, "-i", str(SONG),
         "-map", "0:v:0", "-map", "1:a:0",
         "-t", str(SONG_LENGTH_S),
         "-vf", f"fade=t=out:st={fade_start}:d=3",
         "-af", f"afade=t=out:st={fade_start}:d=3",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-c:a", "aac", "-b:a", "192k", "-shortest", final],
        check=True,
    )
    print(f"DONE: {final}")


_ROOT_LOG = ROOT / "pipeline_run.log"
_print = print


def print(*args, **kwargs):  # noqa: A001 - tee every print into a run log file
    _print(*args, **kwargs)
    with open(_ROOT_LOG, "a", encoding="utf-8") as f:
        f.write(" ".join(str(a) for a in args) + "\n")


def stage_repair(indices: list[int]) -> None:
    """Wan Animate Replace: re-render an approved-motion clip with the
    canonical hero taken from the anchor portrait.

    This locks the face to the reference IMAGE (the generator no longer
    invents it) while keeping the original motion, camera and scene.
    Output: scene_NN/replaced.mp4 (+ QA frames qa_r_sNN_*.jpg).
    """
    for i in indices:
        vdir = OUT / f"scene_{i:02d}"
        src = vdir / "video.mp4"
        if not src.exists():
            raise FileNotFoundError(f"no clip to repair: {src}")
        dst = vdir / "replaced.mp4"
        if dst.exists():
            print(f"  skip (exists): {dst}")
            continue
        args = {
            "prompt": (
                f"Replace the character in this video with the man from the reference "
                f"image ({CHARACTER}), keeping his exact face, short dark hair, light "
                "stubble and the plain blank white space suit with the olive-green "
                "collar; preserve the original motion, camera, framing, scene and "
                f"lighting completely. {NO_SYMBOLS} No captions, no watermark."
            )[:2000],
            "video_url": _data_uri(src),
            "image_url": _data_uri(OUT / "character_portrait.png"),
        }
        print(f"  Wan Animate Replace scene {i:02d} ...")
        result = fal_client.subscribe(WAN_ANIMATE_REPLACE, arguments=args)
        urllib.request.urlretrieve(result["video"]["url"], dst)
        qa_dir = OUT / "preview"
        qa_dir.mkdir(exist_ok=True)
        for frac in (0.1, 0.3, 0.5, 0.7, 0.9):
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-ss", f"{8 * frac:.2f}", "-i", str(dst),
                 "-frames:v", "1", str(qa_dir / f"qa_r_s{i:02d}_{int(frac * 100)}.jpg")],
                check=True,
            )
        print(f"  repair done: {dst}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True,
                    choices=["sheet", "keyframes", "videos", "repair", "stitch", "all"])
    ap.add_argument("--scene", type=int, default=None,
                    help="process a single scene index (keyframes/videos)")
    ap.add_argument("--upto", type=int, default=None,
                    help="process scenes 0..upto-1 (keyframes/videos)")
    args = ap.parse_args()

    if args.scene is not None:
        sel = [args.scene]
    elif args.upto is not None:
        sel = list(range(args.upto))
    else:
        sel = list(range(len(SCENES)))

    stages = {
        "sheet": [stage_sheet],
        "keyframes": [lambda: stage_keyframes(sel)],
        "videos": [lambda: stage_videos(sel)],
        "repair": [lambda: stage_repair(sel)],
        "stitch": [stage_stitch],
        "all": [stage_sheet,
                lambda: stage_keyframes(sel),
                lambda: stage_videos(sel),
                lambda: stage_repair(sel),
                stage_stitch],
    }
    for fn in stages[args.stage]:
        fn()


if __name__ == "__main__":
    import traceback

    try:
        main()
    except BaseException as e:  # диагностика всегда остаётся в файле
        with open(_ROOT_LOG, "a", encoding="utf-8") as f:
            f.write(f"EXIT {type(e).__name__}: {e}\n{traceback.format_exc()}\n")
        raise
