"""scripts/generate_masha_omni.py — Omni R2V для клипов Маши: S01 (замена морфа) и S26 (мост).

Запуск: python scripts/generate_masha_omni.py s01|s26
Правила: лист героини в каждой генерации, рот закрыт, цену одобряет один «Genehmigen»,
лимит 20 кредитов. Готовый клип сохраняется под новым именем, исходники не трогаются.
Импорт engine идёт мимо core/__init__ (в нём тянутся edge_tts/srt, которых нет в окружении).
"""

import asyncio
import importlib
import logging
import sys
import types
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
for name, sub in (("core", ROOT / "core"), ("core.api", ROOT / "core" / "api")):
    pkg = types.ModuleType(name)
    pkg.__path__ = [str(sub)]
    sys.modules[name] = pkg
GoogleFlowEngine = importlib.import_module("core.api.google_flow_engine").GoogleFlowEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("MashaOmni")

PROJECT_URL = "https://flow.google.com/u/0/project/0559cf6d-d69a-4ba0-a214-0b4c5d6c0c81"
SHEET = ROOT / "masha_frames/old_project/01_turnaround.jpg"
MAX_CREDITS = 20

SILENCE = "Do not render any text, caption, name label or watermark from the character sheet. Mouth closed, not speaking, not singing, lips do not move. No dialogue, no lip movement."
HEAD = (
    "Generate a video with Veo using Reference-to-Video (R2V), 8 seconds, 16:9. "
    "The first image is the starting composition. The second image is the character sheet of the "
    "animated heroine Masha: keep her face, hair and style exactly as on the sheet. "
)

SHOTS = {
    "s01": dict(
        frame=ROOT / "masha_frames/ref/masha_02_steps.jpg",
        out=ROOT / "masha_frames/clips/clip_01_v2_omni.mp4",
        prompt=HEAD
        + "The first image is a real photograph of a young woman with dark hair on grey stone steps, "
        "chin resting on her hand. A warm sunspot glides slowly across the photograph. Where it passes, "
        "the photograph gently turns into a stylized 3D animated Masha from the sheet, in the same pose "
        "and on the same steps, with the real photo dissolving into the animated look. At the end she is "
        "fully animated, blinks softly and smiles with a closed mouth. Smooth slow push-in, constant "
        "motion from the first second, no frozen frames. " + SILENCE + " No text, no subtitles, no sound.",
    ),
    "s01v3": dict(
        frame=ROOT / "masha_frames/ref/s01v3_start_from_clip02_0s.png",
        out=ROOT / "masha_frames/clips/clip_01_v3_omni.mp4",
        prompt=HEAD
        + "The first image is the starting composition: animated Masha sleeping in a bright bedroom, "
        "cherry blossoms outside the window. Keep her face, long brown hair, brown eyes, blue shirt and "
        "gold necklace and the Pixar-like 3D style exactly as on the character sheet and the first image. "
        "A warm sunspot glides slowly across the bedroom, over the pillow and onto her face; the white "
        "curtain stirs in a light breeze and blossom petals drift past the window. She stays asleep with "
        "eyes closed and a faint smile. Slow smooth push-in, constant gentle motion from the first second, "
        "no frozen frames. " + SILENCE + " No text, no subtitles, no sound.",
    ),
    "morph": dict(
        frame=ROOT / "masha_frames/ref/s01_photo_16x9_crop.jpg",
        sheet=ROOT / "masha_frames/ref/s01_sheet_plus_keyframe.jpg",
        out=ROOT / "masha_frames/clips/clip_01_v4_morph_omni.mp4",
        prompt="Generate a video with Veo using Reference-to-Video (R2V), 8 seconds, 16:9. "
        "The first image is the starting frame: a real photograph of a young woman on grey stone steps, "
        "cheek resting on her fist. The second image is a collage: on the left the final frame (animated Masha in exactly the same pose), on the right the character sheet of the animated heroine Masha. Do not show the collage itself. "
        "A warm sunspot glides "
        "slowly across the photograph; where it passes, the real photo smoothly turns into the animated "
        "3D Pixar-like Masha from the left part of the second image, same pose, same steps, same framing. By the end she is "
        "fully animated exactly as in the left part of the second image and softly blinks. Slow gentle push-in, constant "
        "motion from the first second, no frozen frames. " + SILENCE + " No text, no subtitles, no sound.",
    ),
    "s26": dict(
        frame=ROOT / "masha_frames/ref/s26_start_from_clip25_last.png",
        out=ROOT / "masha_frames/clips/clip_26_bridge_omni.mp4",
        prompt=HEAD
        + "The first image is the last moment of the previous shot: animated Masha embraces herself, "
        "a golden swirl of light circles around her shoulders. The light swirl slowly gathers into a "
        "bright glowing sparkle that drifts away from her toward the upper right of the frame, as if "
        "calling a fairy. Masha follows it with her eyes and lifts her gaze with a gentle closed-mouth "
        "smile, then the sparkle grows into soft golden light filling the frame. Slow camera drift, "
        "constant motion from the first second, no frozen frames. " + SILENCE
        + " No text, no subtitles, no sound.",
    ),
}


async def main(key: str) -> None:
    shot = SHOTS[key]
    SHEET_ = shot.get("sheet", SHEET)
    for p in (shot["frame"], SHEET_):
        if not Path(p).is_file():
            raise FileNotFoundError(p)
    out: Path = shot["out"]
    if out.exists():
        raise FileExistsError(f"{out} уже есть, не перезаписываю")

    engine = GoogleFlowEngine(
        downloads_dir=str(out.parent), default_model="Omni Flash", max_credits=MAX_CREDITS
    )
    page = await engine.connect()
    if "/edit/" in page.url or "/project/" not in page.url:
        log.info("Переход на холст проекта")
        await page.goto(PROJECT_URL, wait_until="domcontentloaded")
        await asyncio.sleep(4.0)

    await engine.clear_prompt()
    initial_tiles = await engine.get_video_tiles_count()
    prev_cards = await engine.count_cost_cards()
    log.info("Старт: плиток %s, карточек стоимости %s", initial_tiles, prev_cards)

    await engine.attach_reference_image(str(shot["frame"]))
    await engine.attach_reference_image(str(SHEET_))
    log.info("Прикреплено чипов: %s", await engine.count_attached_chips())
    await engine.set_prompt(shot["prompt"])
    await asyncio.sleep(1.0)
    await engine.submit_prompt()
    await asyncio.sleep(2.0)

    card = await engine.wait_for_cost_card(previous_count=prev_cards, timeout_seconds=90)
    log.info("Карточка: %s", card)
    cost = card.get("cost")
    if cost is None:
        log.warning("Цена не прочитана, ничего не нажимаю. Проверь страницу вручную.")
        return
    if cost > MAX_CREDITS:
        log.error("Цена %s выше лимита %s, отклоняю", cost, MAX_CREDITS)
        await engine.reject_cost_card()
        return
    log.info("Цена %s кредитов, нажимаю Genehmigen (разово)", cost)
    await engine.approve_cost_card()

    done = await engine.wait_for_video_completion(
        initial_tiles_count=initial_tiles, timeout_seconds=900, poll_interval=10.0
    )
    if not done:
        raise TimeoutError("Генерация не завершилась за 15 минут")
    await asyncio.sleep(3.0)
    await engine.download_latest_video(str(out))
    log.info("Скачано: %s (%s байт)", out, out.stat().st_size)
    print("COST", cost)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
