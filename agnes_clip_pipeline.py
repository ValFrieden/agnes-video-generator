"""Agnes clip pipeline — free music video for "Хочу навеки" (173.2 s).

Concept «Одна любовь на все времена»: ONE love story lived across
lifetimes. A MAN and a WOMAN are reborn in different eras; in every
scene they LOOK different (different era, hair, clothes), but it is
always the two of them and the pieces assemble into one story ending in
"навеки".

Style consistency strategy (KEYFRAME-FIRST):
  style      — generate ONE canonical style anchor image (free Agnes
               Image API): the signature look of the whole film
  keyframes  — per-scene keyframe illustration rendered as i2i FROM the
               anchor (style and palette are inherited from the picture,
               not re-interpreted from text) + free vision QC gate
  videos     — animate each keyframe via image-to-video (the video can
               not drift in style: it starts from the approved still)
  preview    — refresh dense QA frames (every 10 % of each clip)
  stitch     — normalize + concat + song mux with freeze-tail and fades

Motion laws to avoid generation artifacts: NO spinning, NO twirling, NO
lifting, NO jumping, NO animals flying/jumping; every movement is calm
and linear; camera motions are slow and straight.

Usage:
  .venv/Scripts/python.exe agnes_clip_pipeline.py --stage style
  .venv/Scripts/python.exe agnes_clip_pipeline.py --stage keyframes [--scene N]
  .venv/Scripts/python.exe agnes_clip_pipeline.py --stage videos [--scene N]
  .venv/Scripts/python.exe agnes_clip_pipeline.py --stage preview
  .venv/Scripts/python.exe agnes_clip_pipeline.py --stage stitch

Reads AGNES_API_KEY from .env or the environment. No paid APIs involved.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "agnes_out"
SONG = Path(r"C:\Users\Valeri\Downloads\Хочу навеки.mp3")
SONG_LENGTH_S = 173.2
W, H, FPS = 1280, 720, 24
# 409 кадров @ 24 fps — максимум API для 720p-тира (см. _FRAME_LIMITS)
CLIP_S = 17

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except Exception:
    pass

STYLE = (
    "Every frame of this film is hand-painted 2D storybook illustration "
    "in ONE consistent style: gouache and watercolor textures, soft "
    "rounded shapes, clean simple beautiful faces, visible warm paper "
    "grain. Absolutely no photorealism, no live-action look, no 3D "
    "render look."
)
PALETTE = (
    "ONE shared palette for the whole film: everything bathed in warm "
    "golden-hour light; amber, honey-gold, soft rose and cream colors; "
    "shadows in muted teal; the same sunset warmth in every image."
)
COUPLE_KF = (
    "Exactly TWO people - one loving couple: ONE adult MAN (short hair, "
    "strong jaw, a THIN DARK MUSTACHE, clearly masculine) and ONE adult "
    "WOMAN (long hair, soft gentle features, wearing a dress or long "
    "skirt, clearly feminine). They are the only people in the image."
)
COUPLE_VID = (
    "Exactly two people - the same loving couple as in the reference "
    "image: ONE adult MAN (short hair, thin dark mustache) and ONE adult "
    "WOMAN (long hair, dress); they are the only people in the scene, "
    "and their faces stay clean, stable and identical from the first to "
    "the last frame: no face morphing, no melting, no distorted anatomy."
)
MOTION_LAW = (
    "All movement is calm, smooth and linear: NO spinning, NO twirling, "
    "NO lifting, NO jumping, NO flying animals, NO fish or birds leaping; "
    "the camera moves slowly and steadily in one direction only."
)
MOUTH_RULE = (
    "People never sing and never speak: lips gently closed or softly "
    "smiling, emotions shown only through eyes, gestures and movement."
)
NO_SYMBOLS = (
    "No flags, no emblems, no logos, no badges, no medals, no letters, "
    "no words, no captions, no subtitles, no watermark, no text of any "
    "kind anywhere."
)

# Сетка монтажа: 10 кусков × 17 с = 170 с, хвост 3.2 с — стоп-кадр финала.
# Музыкальные биты: припев взрывается на 42 с (сцена 2), пик 129 (сцена 7),
# бридж 146–150 и финальный припев 150 (сцена 8), конец 173.
SCENES: list[dict] = [
    # 0–17 INTRO — встреча в лавандовом поле
    {"name": "lavender", "prompt": (
        "An endless lavender field in Provence at golden hour, purple rows "
        "flowing to the horizon under a honey-gold sky. The man, a young "
        "farmer with a straw hat in his hands, and the woman with long "
        "chestnut hair in a light cream dress meet between the rows for "
        "the very first time: they stand facing each other at arm's "
        "length, shy glances and warm closed-lip smiles; a gentle wind "
        "carries lavender petals and golden pollen between them."
    ), "motion": (
        "The two lovers stand facing each other and slowly lean a little "
        "closer; the wind gently moves lavender petals, golden pollen, "
        "her long hair and her dress; he carefully offers her one "
        "lavender stem; the camera dollies in very slowly toward their "
        "smiling faces. First meeting, tender and shy."
    )},
    # 17–34 VERSE 1 — Япония, мост и сакура
    {"name": "japan", "prompt": (
        "An old wooden bridge over a quiet river in Japan, cherry trees "
        "in full bloom, warm sunset light. The same couple reborn in "
        "another life: the man is a young Japanese fisherman in simple "
        "indigo clothes with short black hair and a thin mustache; the "
        "woman is a graceful Japanese lady in a soft pink kimono with "
        "long black hair, holding a paper parasol. They stand in the "
        "middle of the bridge facing each other; pink petals swirl in "
        "the golden air; she holds out a single cherry branch to him."
    ), "motion": (
        "Pink petals drift slowly through the air; the woman tilts her "
        "parasol and offers him the cherry branch with both hands; he "
        "bows gently to her; their sleeves flutter softly in the breeze; "
        "the camera drifts slowly sideways along the bridge. Tender and "
        "poetic."
    )},
    # 34–51 VERSE→CHORUS (взрыв припева на 42 внутри сцены) — Париж
    {"name": "paris", "prompt": (
        "Paris in the 1920s at golden hour, a cozy cobblestone street "
        "cafe under glowing paper lanterns. The same couple reborn "
        "again: the man in a brown vintage suit and fedora with a thin "
        "mustache; the woman in a champagne drop-waist dress with short "
        "wavy dark hair, long pearls and a cream shawl. They stand "
        "close together in dancing position on the cobblestones in "
        "front of the cafe, gazing into each other's eyes; warm "
        "lanterns glow; a few pigeons rest on the street nearby, calm."
    ), "motion": (
        "The couple slowly and calmly dances a simple gentle waltz "
        "together: small side steps, soft swaying back and forth, "
        "holding each other, always facing one another - absolutely NO "
        "spinning and NO twirling; lanterns flicker warmly, pigeon "
        "feathers drift; the camera glides very slowly in a straight "
        "line around the pair. Joyful, serene, romantic."
    )},
    # 51–68 — море, лодка
    {"name": "sea", "prompt": (
        "A small wooden fishing boat on a calm turquoise Mediterranean "
        "sea at sunset. The same couple in another life: the man is a "
        "sun-tanned young sailor with curly black hair and a thin "
        "mustache in a white shirt with rolled sleeves; the woman wears "
        "a light blue summer dress and a golden headscarf, her long "
        "dark hair flying. She stands at the bow with her arms spread "
        "wide into the wind; he holds the rudder at the stern, looking "
        "at her with love; the sea glitters gold and rose."
    ), "motion": (
        "The boat glides smoothly and steadily forward over calm "
        "water; the woman's dress and hair flutter in the steady wind; "
        "sun glitter dances on the waves; the man steers gently, "
        "smiling; the camera tracks alongside the boat at constant "
        "speed, keeping it in frame. Absolutely no dolphins, no fish "
        "jumping, no birds diving. Free and warm."
    )},
    # 68–85 CHORUS 2 — осень, велосипед
    {"name": "autumn", "prompt": (
        "An autumn park with golden and rust-colored trees, leaves "
        "falling like warm rain in the sunset light. The same couple in "
        "another life: the man rides a vintage bicycle in a warm honey "
        "sweater, thin mustache, clearly masculine; the woman sits "
        "sideways on the rear rack in a long mustard skirt, a small "
        "beret and a cream scarf, her long braided hair streaming, arms "
        "spread wide like wings, laughing silently."
    ), "motion": (
        "The bicycle rolls slowly and strictly STRAIGHT along the alley "
        "- never sideways, never turning, wheels turning evenly; "
        "golden leaves fall and drift past; her scarf and hair flutter; "
        "the camera tracks alongside the bicycle at constant speed. "
        "Pure carefree joy."
    )},
    # 85–102 VERSE 2 — первый дом, уют
    {"name": "home", "prompt": (
        "A cozy attic home in the evening, warm lamplight, soft rain "
        "streaking a round window with a teal-blue city beyond. The "
        "same couple in another life share their first home: the man "
        "sits holding an old guitar with messy dark hair and a thin "
        "mustache, in a warm sweater; the woman paints at a wooden "
        "easel by the window - on her canvas the two of them in a "
        "lavender field - her hair in a loose bun, a cream dress. She "
        "looks back over her shoulder at him; candle flames tremble."
    ), "motion": (
        "The man softly strums the guitar, his hand moving gently; the "
        "woman turns her head from the easel and looks at him over her "
        "shoulder; he meets her eyes and smiles; candle flames tremble "
        "tenderly; rain streaks run down the window glass; the camera "
        "pushes in very slowly. Quiet, intimate, deeply tender."
    )},
    # 102–119 PRE-CHORUS — шторм и разлука
    {"name": "storm", "prompt": (
        "A stormy sea at dusk, dramatic wind, rose clouds fighting dark "
        "teal ones - still in the film's warm palette. The couple is "
        "being separated: the man stands on the deck of a great sailing "
        "ship near the harbor, gripping the wooden railing, looking "
        "back over his shoulder; the woman stands at the end of the "
        "stone pier holding her long dress and flying long hair against "
        "the wind, one arm stretched toward him; gulls glide high in "
        "the sky; first raindrops streak the air."
    ), "motion": (
        "The sailing ship rocks gently and slowly departs; the wind "
        "whips her dress and hair while she holds her stretched arm "
        "steady; rain begins to streak the air; the camera rises very "
        "slowly above the pier, the distance between ship and pier "
        "growing. Aching, cinematic, full of longing."
    )},
    # 119–136 PEAK (пик 129 внутри) — возвращение и объятия
    {"name": "reunion", "prompt": (
        "The harbor at the most magnificent golden sunset of the whole "
        "film: the sailing ship has returned. The couple embraces on "
        "the wooden pier: he holds her closely against his chest, her "
        "long hair and rose dress streaming in the golden wind, both "
        "eyes closed, cheeks together; golden sparks of sunlight swirl "
        "in the air around them; gulls glide high above, calm; the ship "
        "rests moored behind them."
    ), "motion": (
        "The couple stands embracing, holding each other closely and "
        "swaying just slightly, absolutely no spinning, no lifting; "
        "her dress and hair stream in the wind; golden light swirls "
        "around the pier; the camera circles them very slowly at "
        "constant distance. Pure triumphant happiness."
    )},
    # 136–153 бридж 146–150 + финальный припев 150 — свадьба
    {"name": "wedding", "prompt": (
        "The same Provence lavender field where they first met, at the "
        "most beautiful golden hour: their wedding. The man waits in a "
        "light cream suit with his thin mustache; the woman walks "
        "toward him along the aisle between lavender rows in a simple "
        "ivory dress with a wreath of wildflowers, holding a bouquet, "
        "her long hair under a short veil; guests with paper umbrellas "
        "line the aisle at a respectful distance."
    ), "motion": (
        "The woman walks slowly toward the man down the aisle; he "
        "reaches out his hand; she arrives and they join hands and "
        "stand together facing each other, foreheads leaning close, "
        "absolutely no lifting and no spinning; lavender petals drift "
        "on the wind; guests wave their hands; the camera pushes in "
        "slowly. Breathtaking, triumphant, tender."
    )},
    # 153–170(+3.2 хвост) FINALE — «навеки»: старость на крыльце
    {"name": "forever", "prompt": (
        "The same lavender field in the softest evening light, decades "
        "later: the same couple, now elderly. The man with white hair, "
        "a neat white mustache and beard in his light suit; the woman "
        "with silver hair in a bun and a warm rose shawl over her "
        "dress. They sit together on an old wooden porch bench, her "
        "head resting on his shoulder, his hand gently holding hers, a "
        "cane leaning beside the bench; fireflies rise like tiny warm "
        "lanterns; the first stars appear in the rose sky."
    ), "motion": (
        "They sit almost still on the bench, her head on his shoulder; "
        "fireflies drift slowly upward like warm sparks; the lavender "
        "field sways gently in the evening breeze; stars appear one by "
        "one; the camera pulls back very slowly toward the horizon. "
        "Eternal love - forever. Fade toward warm darkness."
    )},
]

STYLE_ANCHOR_PROMPT = (
    "Hand-painted 2D storybook illustration in gouache and watercolor "
    "with visible warm paper grain: an endless lavender field in "
    "Provence at golden hour, purple rows flowing to the horizon under "
    f"a honey-gold sky. {COUPLE_KF} The young farmer man holds his "
    "straw hat in his hands; the woman with long chestnut hair in a "
    "light cream dress smiles at him shyly; lavender petals and golden "
    "pollen float in the warm air between them. "
    f"{PALETTE} {STYLE} {MOUTH_RULE} {NO_SYMBOLS} Wide 16:9 cinematic "
    "composition, the couple small-medium in the frame, centered."
)


def _log(msg: str) -> None:
    print(msg, flush=True)
    with open(ROOT / "agnes_run.log", "a", encoding="utf-8") as f:
        f.write(msg.rstrip() + "\n")


def _vdir(i: int) -> Path:
    return OUT / f"scene_{i:02d}_{SCENES[i]['name']}"


def _kf_prompt(i: int) -> str:
    return (
        f"{COUPLE_KF} {SCENES[i]['prompt']} {PALETTE} {STYLE} {MOUTH_RULE} "
        f"{NO_SYMBOLS} One single frozen moment, wide 16:9 cinematic "
        "composition, exactly like the reference image in art style, "
        "colors and character design: same painting technique, same "
        "face style, same warm golden-hour palette. The man ALWAYS has "
        "his thin dark mustache clearly visible, the woman ALWAYS has "
        "long hair and a dress, in the same face style as the reference "
        "image."
    )


# Покадровые подсказки для сцен, где i2v допускал дрейф
MOTION_HINTS = {
    2: "In every frame the man keeps his face clearly visible and turned "
       "toward the camera, his thin dark mustache always readable. The "
       "image style stays STRICTLY flat hand-painted 2D gouache "
       "illustration in every frame: flat shapes, visible paper grain, "
       "clean painted outlines - never 3D, never photorealistic, no "
       "depth of field, no realistic textures.",
    3: "The sea is completely EMPTY: absolutely no fish, no dolphins, no "
       "jellyfish, no birds, no marine creatures anywhere in any frame - "
       "only water, light and the boat.",
    8: "In every frame the man's face is clearly visible toward the "
       "camera with his thin dark mustache always present.",
}


def _video_prompt(i: int) -> str:
    return (
        f"Animate this painted scene gently: {SCENES[i]['motion']} "
        f"{MOTION_HINTS.get(i, '')} "
        f"{COUPLE_VID} {MOTION_LAW} {MOUTH_RULE} {NO_SYMBOLS} "
        "Keep the exact art style, palette and character design of the "
        "reference image for every frame of the video. One continuous "
        "shot, cinematic 16:9."
    )


NEGATIVE = (
    "text, captions, subtitles, watermark, logo, letters, words, flag, "
    "emblem, photorealism, live action, real skin texture, 3d render, "
    "two men as a couple, two women as a couple, same-sex couple, "
    "spinning dancer, twirling, lifted person, flying fish, jumping "
    "dolphins, deformed hands, extra fingers, twisted faces, open "
    "singing mouths, lip sync, jump cuts, split screen, collage"
)


def _probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(out.stdout)["format"]["duration"])


def _qa_frames(i: int, video: Path) -> None:
    qa_dir = OUT / "preview"
    qa_dir.mkdir(parents=True, exist_ok=True)
    dur = _probe_duration(video)
    for frac in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        t = dur * frac
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video),
             "-frames:v", "1", str(qa_dir / f"qa_s{i:02d}_{int(frac * 100)}.jpg")],
            check=True,
        )


# ---------------------------------------------------------------- stage: style
async def stage_style() -> Path:
    from core.api.agnes_image import AgnesImageAPI

    OUT.mkdir(parents=True, exist_ok=True)
    anchor = OUT / "style_anchor.png"
    if anchor.exists():
        _log("[style] skip (exists)")
        return anchor
    api_key = os.environ.get("AGNES_API_KEY", "")
    if not api_key:
        sys.exit("AGNES_API_KEY is not set (.env or environment)")
    api = AgnesImageAPI(api_key=api_key)
    for attempt in (1, 2):
        try:
            _log(f"[style] generating style anchor (attempt {attempt})")
            try:
                img = await api.generate_single_image(
                    prompt=STYLE_ANCHOR_PROMPT, size="1280x720"
                )
            except Exception as e:
                _log(f"[style] 1280x720 rejected ({e}), fallback 1024x1024")
                img = await api.generate_single_image(
                    prompt=STYLE_ANCHOR_PROMPT, size="1024x1024"
                )
            await img.save(str(anchor))
            _log(f"[style] saved {anchor}")
            return anchor
        except Exception as e:
            _log(f"[style] attempt {attempt} failed: {type(e).__name__}: {e}")
            if attempt == 2:
                raise
    raise RuntimeError("unreachable")


# ----------------------------------------------------------- stage: keyframes
KF_QC_SYSTEM = (
    "You are a strict art director. IMAGE 1 is the canonical style "
    "anchor of an animated film. IMAGE 2 is a candidate keyframe. "
    "Answer with ONE line: 'PASS - <short>' or 'FAIL - <reason>'. "
    "FAIL if: the couple is not exactly one adult MAN with short hair "
    "and a THIN DARK MUSTACHE plus one adult WOMAN with long hair "
    "wearing a dress or skirt (two women, two men, or a missing/"
    "androgynous partner = instant FAIL); there are other people "
    "besides the couple; the art style clearly differs from IMAGE 1 "
    "(e.g. photo-realistic, 3D, different line work); the palette is "
    "cold or grey instead of the warm golden-hour palette; any readable "
    "text, letters, logo, flag; anyone singing with an open mouth. "
    "Otherwise PASS."
)


# Сцены, где мелкие дальние фоновые фигуры допустимы по замыслу
KF_QC_NOTES = {
    8: "This is the WEDDING scene: small distant background wedding "
       "guests with umbrellas are INTENTIONAL and allowed. The rule "
       "about 'only the couple' applies to the COUPLE itself: one man "
       "with a thin dark mustache + one woman in a wedding dress.",
}


def _qc_keyframe(chat, i: int, kf: Path) -> bool:
    verdict = ""
    try:
        verdict = chat.chat_multimodal(
            KF_QC_SYSTEM,
            f"This keyframe must show: {SCENES[i]['prompt'][:300]}. "
            f"{KF_QC_NOTES.get(i, '')} Judge now.",
            [str(OUT / "style_anchor.png"), str(kf)],
        )
    except Exception as e:
        _log(f"  [KQC] scene {i:02d}: WARN check failed ({e}); treat as PASS")
        return True
    verdict = (verdict or "").strip().splitlines()[0] if verdict else ""
    ok = verdict.upper().startswith("PASS")
    _log(f"  [KQC] scene {i:02d}: {verdict[:170]}")
    return ok


async def stage_keyframes(indices: list[int]) -> None:
    from core.api.agnes_image import AgnesImageAPI

    anchor = await stage_style()
    api_key = os.environ.get("AGNES_API_KEY", "")
    api = AgnesImageAPI(api_key=api_key)
    from core.api.agnes_chat import AgnesChatAPI

    chat = AgnesChatAPI(api_key=api_key)
    sem = asyncio.Semaphore(4)

    async def render(i: int) -> None:
        vdir = _vdir(i)
        vdir.mkdir(parents=True, exist_ok=True)
        kf = vdir / "keyframe.png"
        async with sem:
            if kf.exists():
                _log(f"  scene {i:02d}: keyframe skip (exists)")
                return
            _log(f"  scene {i:02d}: keyframe i2i from style anchor")
            img = await api.generate_single_image(
                prompt=_kf_prompt(i),
                reference_image_paths=[str(anchor)],
                size="1280x720",
                negative_prompt=NEGATIVE,
            )
            await img.save(str(kf))
        if not _qc_keyframe(chat, i, kf):
            hint = (
                f"CRITICAL FIX: previous attempt was rejected: the couple "
                f"must be EXACTLY one man (short hair, thin dark mustache) "
                f"and one woman (long hair, dress). Same style as the "
                f"reference image. "
            )
            _log(f"  [KQC] scene {i:02d}: regenerating keyframe with hint")
            img = await api.generate_single_image(
                prompt=hint + _kf_prompt(i),
                reference_image_paths=[str(anchor)],
                size="1280x720",
                negative_prompt=NEGATIVE,
            )
            await img.save(str(kf))
            if not _qc_keyframe(chat, i, kf):
                _log(f"  [KQC] scene {i:02d}: STILL FAILING - needs manual review")

    results = await asyncio.gather(
        *(render(i) for i in indices), return_exceptions=True
    )
    failed = [(i, r) for i, r in zip(indices, results) if isinstance(r, BaseException)]
    for i, r in failed:
        _log(f"  scene {i:02d}: keyframe GAVE UP: {type(r).__name__}: {r}")
    if failed:
        sys.exit(f"{len(failed)} keyframe(s) failed: {[i for i, _ in failed]}")


# -------------------------------------------------------------- stage: videos
async def _gen_scene(api, i: int, attempts: int = 3) -> Path:
    vdir = _vdir(i)
    video = vdir / "video.mp4"
    kf = vdir / "keyframe.png"
    if not kf.exists():
        raise FileNotFoundError(f"keyframe missing, run --stage keyframes: {kf}")
    if video.exists():
        _log(f"  scene {i:02d}: skip (exists)")
        return video
    for attempt in range(1, attempts + 1):
        _log(f"  scene {i:02d} [{SCENES[i]['name']}] attempt {attempt}/{attempts}: "
             f"submit i2v {CLIP_S}s {W}x{H}")
        try:
            result = await api.generate_single_video(
                prompt=_video_prompt(i),
                reference_image_paths=[str(kf)],
                duration=CLIP_S,
                width=W,
                height=H,
                negative_prompt=NEGATIVE,
            )
            await result.save(str(video))
            dur = _probe_duration(video)
            _log(f"  scene {i:02d}: saved ({dur:.1f}s, {video.stat().st_size // 1024} KiB)")
            if dur < CLIP_S - 2:
                _log(f"  scene {i:02d}: WARN shorter than expected ({dur:.1f}s)")
            _qa_frames(i, video)
            return video
        except Exception as e:
            _log(f"  scene {i:02d}: attempt {attempt} FAILED: {type(e).__name__}: {e}")
            if video.exists():
                video.unlink()
            if attempt == attempts:
                raise
            await asyncio.sleep(60)
    raise RuntimeError("unreachable")


async def stage_videos(indices: list[int], concurrency: int = 6) -> None:
    from core.api.agnes_video import AgnesVideoAPI

    api = AgnesVideoAPI(api_key=os.environ.get("AGNES_API_KEY", ""))
    sem = asyncio.Semaphore(concurrency)

    async def run(i: int) -> None:
        async with sem:
            await _gen_scene(api, i)

    results = await asyncio.gather(
        *(run(i) for i in indices), return_exceptions=True
    )
    failed = [(i, r) for i, r in zip(indices, results) if isinstance(r, BaseException)]
    for i, r in failed:
        _log(f"  scene {i:02d}: GAVE UP: {type(r).__name__}: {r}")
    if failed:
        sys.exit(f"{len(failed)} scene(s) failed: {[i for i, _ in failed]}")


def stage_preview(indices: list[int]) -> None:
    for i in indices:
        video = _vdir(i) / "video.mp4"
        if video.exists():
            _qa_frames(i, video)
            _log(f"  scene {i:02d}: preview frames refreshed")


# -------------------------------------------------------------- stage: stitch
def _normalize(video: Path, out: Path, freeze_tail_s: float = 0.0) -> Path:
    if out.exists():
        return out
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={FPS}"
    )
    if freeze_tail_s > 0:
        vf += f",tpad=stop_mode=clone:stop_duration={freeze_tail_s}"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(video),
         "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-an", str(out)],
        check=True,
    )
    return out


def stage_stitch() -> None:
    tail = SONG_LENGTH_S - CLIP_S * len(SCENES)  # 3.2 s хвост финала
    norm_dir = OUT / "normalized"
    norm_dir.mkdir(parents=True, exist_ok=True)
    norm = []
    for i in range(len(SCENES)):
        video = _vdir(i) / "video.mp4"
        if not video.exists():
            sys.exit(f"Missing scene video: {video}")
        freeze = tail if i == len(SCENES) - 1 and tail > 0 else 0.0
        norm.append(_normalize(video, norm_dir / f"scene_{i:02d}.mp4", freeze))

    concat_list = norm_dir / "list.txt"
    concat_list.write_text(
        "".join(f"file '{n.as_posix()}'\n" for n in norm), encoding="utf-8"
    )
    silent = OUT / "concat.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(concat_list), "-c", "copy", str(silent)],
        check=True,
    )

    final = ROOT / "Хочу навеки — agnes clip.mp4"
    fade_start = SONG_LENGTH_S - 3.2
    _log(f"[stitch] muxing song, fade out at {fade_start:.1f}s")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-i", str(silent), "-i", str(SONG),
         "-map", "0:v:0", "-map", "1:a:0",
         "-t", str(SONG_LENGTH_S),
         "-vf", f"fade=t=out:st={fade_start}:d=3.2",
         "-af", f"afade=t=out:st={fade_start}:d=3.2",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-c:a", "aac", "-b:a", "192k", str(final)],
        check=True,
    )
    _log(f"DONE: {final} ({_probe_duration(Path(final)):.1f}s)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True,
                    choices=["style", "keyframes", "videos", "preview", "stitch"])
    ap.add_argument("--scene", type=int, default=None,
                    help="process a single scene index")
    args = ap.parse_args()

    if args.scene is not None:
        sel = [args.scene]
    else:
        sel = list(range(len(SCENES)))

    if args.stage == "style":
        asyncio.run(stage_style())
    elif args.stage == "keyframes":
        asyncio.run(stage_keyframes(sel))
    elif args.stage == "videos":
        asyncio.run(stage_videos(sel))
    elif args.stage == "preview":
        stage_preview(sel)
    else:
        stage_stitch()


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        with open(ROOT / "agnes_run.log", "a", encoding="utf-8") as f:
            f.write(f"EXIT {type(e).__name__}: {e}\n{traceback.format_exc()}\n")
        raise
