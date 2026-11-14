"""scripts/generate_all_remaining_shots.py
Полная надежная генерация оставшихся шотов (30-36) и финальный монтаж.
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

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.api.google_flow_engine import GoogleFlowEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FullMvGenerator")

PROJECT_URL = "https://flow.google.com/project/88686c92-a9eb-47d7-b2a9-c88317951cef"
CHAR_REF = Path("references/character_valeri_costume_master.png").resolve()
OUTPUT_DIR = Path("output").resolve()
BRAIN_DIR = Path(r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66")
AUDIO_TRACK = Path("uploaded_media_1793789661300.mp3").resolve()

REMAINING_SHOTS = [
    {
        "id": 29,
        "name": "shot_29_stepping_to_light",
        "has_char": True,
        "lyric": "Сгустился над нами холодный туман...",
        "prompt": (
            "Generate video with Veo: Cinematic 35mm live-action motion video, Kodak Vision3 500T, authentic human actor. "
            "The same 42-year-old Caucasian man with short hair greying at the temples and subtle stubble, identical facial features to attached reference. "
            "He wears the exact same canonical costume: a sand-beige textured chunky knit cardigan with ribbed cuffs over a dark grey plaid flannel button-down collared shirt, and dark charcoal straight trousers. "
            "He takes deliberate, confident steps forward towards the bright vertical beam of golden morning dawn sunlight. "
            "Swirling cold blue mist and dim shadows in the room dissipate as he approaches the radiant golden light. "
            "Lips strictly pressed shut, completely silent, mouth closed, no talking, no lip movement, walking forward in silence. "
            "Natural slow camera tracking, volumetric god rays, realistic lighting, 16:9 widescreen, no cartoon, no animation, no 2D, no CGI, no talking, no mouth open"
        )
    },
    {
        "id": 30,
        "name": "shot_30_decisive_eyes",
        "has_char": True,
        "lyric": "Нам так не хватает последнего шага...",
        "prompt": (
            "Generate video with Veo: Cinematic 35mm live-action motion video, Kodak Vision3 500T, authentic human actor. "
            "Medium close-up on the same 42-year-old Caucasian man with short hair greying at the temples and subtle stubble, identical facial features to attached reference. "
            "He wears the exact same canonical costume: a sand-beige textured chunky knit cardigan over a dark grey plaid flannel button-down collared shirt. "
            "He moves forward with intense, resolute determination in his eyes. Warm golden sunrise light illuminates the side of his face, sparkling in his eyes. "
            "His gaze is focused straight ahead with unwavering clarity. "
            "Lips strictly pressed shut, completely silent, mouth closed, no talking, no lip movement, resolute expression. "
            "Cinematic shallow depth of field, subtle film grain, 16:9 widescreen, no cartoon, no animation, no 2D, no CGI, no talking, no mouth open"
        )
    },
    {
        "id": 31,
        "name": "shot_31_walls_crumble_to_dust",
        "has_char": True,
        "lyric": "Когда эти стены рассыплются в прах!",
        "prompt": (
            "Generate video with Veo: Cinematic 35mm live-action motion video, Kodak Vision3 500T, authentic human actor. "
            "The same 42-year-old Caucasian man wearing the exact same canonical costume: a sand-beige textured chunky knit cardigan over a dark grey plaid flannel button-down collared shirt, and dark charcoal straight trousers. "
            "He firmly steps through the decaying paper wall barrier; dry craft paper wallpaper and brittle plaster fragments break apart and fall straight down onto the wooden floorboards under natural gravity, crumbling into glittering golden dust particles. "
            "Brilliant warm morning sunlight floods the room. "
            "Lips strictly pressed shut, completely silent, mouth closed, no talking, breaking through the barrier. "
            "Strict downward gravity, debris drops to floorboards, 16:9 widescreen, no cartoon, no animation, no 2D, no CGI, no talking, no upward motion, no shutters"
        )
    },
    {
        "id": 32,
        "name": "shot_32_step_onto_pier",
        "has_char": True,
        "lyric": "Инструментал: выход в реальный мир",
        "prompt": (
            "Generate video with Veo: Cinematic 35mm live-action motion video, Kodak Vision3 500T, authentic human actor. "
            "The same 42-year-old Caucasian man with short hair greying at the temples and subtle stubble, identical facial features to attached reference. "
            "He wears the exact same canonical costume: a sand-beige textured chunky knit cardigan with ribbed cuffs over a dark grey plaid flannel button-down collared shirt, and dark charcoal straight trousers. "
            "He steps out from the shadows onto a sunlit rustic wooden pier above a calm pristine lake. "
            "A gentle fresh morning breeze softly ruffles his hair and the knit fabric of his cardigan. "
            "Lips strictly pressed shut, completely silent, mouth closed, no talking, stepping out into open nature. "
            "Warm golden dawn sun, sparkling water reflections, 16:9 widescreen, no cartoon, no animation, no 2D, no CGI, no talking, no mouth open"
        )
    },
    {
        "id": 33,
        "name": "shot_33_lake_dawn_panorama",
        "has_char": False,
        "lyric": "Инструментал: панорама озера на рассвете",
        "prompt": (
            "Generate video with Veo: Pristine edge-to-edge cinematic 35mm live-action motion video, natural color grading. "
            "Wide panoramic landscape shot of a boundless pristine calm lake at sunrise. "
            "The golden morning sun rises just above the misty dark green pine forest horizon. "
            "Subtle morning mist floats gently across the mirror-like glass surface of the water, reflecting the blazing golden and amber hues of the dawn sky. "
            "Smooth slow cinematic camera glide across the calm water surface. "
            "Pure cinematic nature landscape, realistic fluid physics, 16:9 widescreen, no borders, no film frame, no film border, no text, no captions, no watermarks, no film perforations, no black bars, full bleed edge-to-edge video, no cartoon, no animation, no 2D, no CGI"
        )
    },
    {
        "id": 34,
        "name": "shot_34_deep_breath_freedom",
        "has_char": True,
        "lyric": "Инструментал: вдох свободы",
        "prompt": (
            "Generate video with Veo: Pristine edge-to-edge cinematic 35mm live-action motion video, authentic human actor. "
            "Medium shot of the same 42-year-old Caucasian man with short hair greying at the temples and subtle stubble, identical facial features to attached reference. "
            "He wears the exact same canonical costume: a sand-beige textured chunky knit cardigan over a dark grey plaid flannel button-down collared shirt, and dark charcoal straight trousers. "
            "He stands on the wooden lake pier bathed in warm golden morning light. "
            "He closes his eyes briefly, inhaling a deep breath of fresh crisp air, his shoulders relaxing in profound peace and liberation, then opens his eyes looking at the open sky with serene calm. "
            "Lips strictly pressed shut, completely silent, mouth closed, no talking, no smiling, peaceful demeanor. "
            "16:9 widescreen, no borders, no film frame, no film border, no text, no captions, no watermarks, no film perforations, no black bars, full bleed edge-to-edge video, no cartoon, no animation, no 2D, no CGI, no talking, no mouth open"
        )
    },
    {
        "id": 35,
        "name": "shot_35_dewdrops_wildflowers",
        "has_char": False,
        "lyric": "Инструментал: капли росы на рассвете",
        "prompt": (
            "Generate video with Veo: Pristine edge-to-edge cinematic 35mm live-action motion video, natural color grading. "
            "Close-up macro nature shot of wild lake shore plants, delicate reeds and wildflowers swaying in a gentle morning breeze. "
            "Clear, glistening dewdrops cling to green stems, catching the early morning golden sunlight and sparkling like diamonds. "
            "In the soft blurred background, the calm blue and golden lake water glimmers. "
            "Cinematic shallow depth of field, authentic macro photography, 16:9 widescreen, no borders, no film frame, no film border, no text, no captions, no watermarks, no film perforations, no black bars, full bleed edge-to-edge video, no cartoon, no animation, no 2D, no CGI"
        )
    },
    {
        "id": 36,
        "name": "shot_36_grand_finale_sunrise",
        "has_char": True,
        "lyric": "Финал: человек у рассветного горизонта",
        "prompt": (
            "Generate video with Veo: Pristine edge-to-edge cinematic 35mm live-action motion video, authentic human actor. "
            "Wide grand cinematic shot. The same 42-year-old Caucasian man in the exact same canonical costume (sand-beige textured chunky knit cardigan, dark grey plaid flannel shirt, dark charcoal trousers) stands at the edge of the rustic wooden pier facing the vast, boundless calm lake and the magnificent golden sunrise. "
            "The camera slowly and smoothly cranes upwards and pulls back into the glowing golden dawn sky, leaving the solitary man peacefully admiring the infinite horizon. "
            "Lips strictly pressed shut, mouth closed, peaceful heroic posture. "
            "Golden hour brilliance, 16:9 widescreen, no borders, no film frame, no film border, no text, no captions, no watermarks, no film perforations, no black bars, full bleed edge-to-edge video, no cartoon, no animation, no 2D, no CGI, no talking, no mouth open"
        )
    }
]


async def dismiss_any_modal(page):
    try:
        has_dialog = await page.evaluate("() => document.querySelectorAll('.cdk-overlay-backdrop-showing, mat-dialog-container').length > 0")
        if has_dialog:
            logger.info("⚠️ Обнаружен модальный диалог, закрываем...")
            await page.keyboard.press("Escape")
            await asyncio.sleep(1.0)
            btn = await page.query_selector("mat-dialog-container button, .cdk-overlay-pane button")
            if btn and await btn.is_visible():
                await btn.click()
                await asyncio.sleep(1.0)
    except Exception as e:
        logger.warning(f"Ошибка при закрытии диалога: {e}")


async def wait_for_tile_0_ready(page, timeout_seconds=600, poll_interval=6.0):
    start_time = time.time()
    logger.info("⏳ Ожидание завершения генерации (проверка готовности плитки или редактора)...")
    await asyncio.sleep(12.0)
    while (time.time() - start_time) < timeout_seconds:
        status = await page.evaluate('''() => {
            const editor = !!document.querySelector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]');
            const firstTile = document.querySelector('flow-video-tile');
            const hasPlayCircle = firstTile ? (firstTile.innerText || '').includes('play_circle') : false;
            const video = firstTile ? firstTile.querySelector('video') : null;
            const hasVideo = !!(video && video.src && video.src.length > 20);
            const text = (firstTile ? firstTile.innerText : '') || document.body.innerText || '';
            const match = text.match(/(\\d+)\\s*%/);
            const hasProgress = !!match;
            const hasSpinner = !!document.querySelector('mat-progress-spinner, mat-spinner, .loading, .spinner');
            return {
                ready: (hasVideo || editor || hasPlayCircle) && !hasProgress && !hasSpinner,
                editor,
                hasPlayCircle,
                progress: match ? match[1] : null,
                hasVideo,
                hasSpinner
            };
        }''')
        elapsed = int(time.time() - start_time)
        if status.get("ready"):
            logger.info(f"🎉 [+{elapsed}s] Видео отрендерено! (editor={status.get('editor')}, play_circle={status.get('hasPlayCircle')}, hasVideo={status.get('hasVideo')})")
            await asyncio.sleep(2.0)
            return True
        elif status.get("progress"):
            logger.info(f"⏳ [+{elapsed}s] Прогресс: {status['progress']}%")
        else:
            logger.info(f"⏳ [+{elapsed}s] Рендеринг в процессе (editor={status.get('editor')})...")
        await asyncio.sleep(poll_interval)
    raise TimeoutError(f"Превышено время ожидания рендера ({timeout_seconds}с)")


async def download_shot(page, target_path: Path):
    logger.info(f"📥 Скачивание 720p видео в {target_path.name}...")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists():
        target_path.unlink()

    btn = await page.query_selector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]')
    if not (btn and await btn.is_visible()):
        logger.info("Открытие первой видео-плитки...")
        await page.evaluate("""(() => {
            const tiles = document.querySelectorAll('flow-video-tile');
            if (tiles.length > 0) tiles[0].click();
        })()""")
        await asyncio.sleep(2.0)

    async with page.expect_download(timeout=60000) as dl_info:
        btn = await page.query_selector('button[aria-label*="Medien herunterladen"], button[aria-label*="Download"]')
        if btn:
            await btn.click()
            await asyncio.sleep(1.0)

        clicked = await page.evaluate("""(() => {
            const all = Array.from(document.querySelectorAll('*'));
            const opt = all.find(el => el.innerText && el.innerText.includes('720p') && (
                el.getAttribute('role') === 'menuitem' || 
                el.tagName === 'BUTTON' || 
                el.classList.contains('mat-mdc-menu-item') ||
                el.tagName === 'SPAN'
            ));
            if (opt) {
                const clickTarget = opt.closest('button') || opt.closest('[role=\"menuitem\"]') || opt;
                clickTarget.click();
                return true;
            }
            return false;
        })()""")
        logger.info(f"Клик по элементу 720p: {clicked}")
        if not clicked:
            raise RuntimeError("Не удалось найти и кликнуть пункт меню 720p!")

    download = await dl_info.value
    await download.save_as(str(target_path))
    logger.info(f"✅ Файл сохранен: {target_path} ({target_path.stat().st_size} байт)")


def extract_qc_frames(target_path: Path):
    qc_25 = target_path.parent / f"{target_path.stem}_qc_25.jpg"
    qc_50 = target_path.parent / f"{target_path.stem}_qc_50.jpg"
    qc_75 = target_path.parent / f"{target_path.stem}_qc_75.jpg"

    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(target_path)]
    ).decode().strip())

    subprocess.run(["ffmpeg", "-y", "-ss", str(dur * 0.25), "-i", str(target_path), "-vframes", "1", "-q:v", "2", str(qc_25)], check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-ss", str(dur * 0.50), "-i", str(target_path), "-vframes", "1", "-q:v", "2", str(qc_50)], check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-ss", str(dur * 0.75), "-i", str(target_path), "-vframes", "1", "-q:v", "2", str(qc_75)], check=True, capture_output=True)

    qa_contact = target_path.parent / f"{target_path.stem}_qa_trio.png"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(qc_25), "-i", str(qc_50), "-i", str(qc_75),
        "-filter_complex", "hstack=inputs=3",
        str(qa_contact)
    ], check=True, capture_output=True)

    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(target_path), BRAIN_DIR / target_path.name)
    shutil.copy2(str(qc_25), BRAIN_DIR / qc_25.name)
    shutil.copy2(str(qc_50), BRAIN_DIR / qc_50.name)
    shutil.copy2(str(qc_75), BRAIN_DIR / qc_75.name)
    shutil.copy2(str(qa_contact), BRAIN_DIR / qa_contact.name)
    logger.info(f"📸 QC-кадры скопированы в brain: {qa_contact.name}")


async def generate_single_shot(engine, page, shot_info: dict):
    shot_id = shot_info["id"]
    shot_name = shot_info["name"]
    target_mp4 = OUTPUT_DIR / f"{shot_name}.mp4"

    if target_mp4.exists() and target_mp4.stat().st_size > 500000:
        logger.info(f"⏭️ Шот {shot_id} ({shot_name}) уже существует ({target_mp4.stat().st_size} байт). Пропускаем.")
        if not (OUTPUT_DIR / f"{shot_name}_qa_trio.png").exists():
            extract_qc_frames(target_mp4)
        return

    logger.info(f"\n========================================================")
    logger.info(f"🎬 Генерация Шота {shot_id}: «{shot_info['lyric']}»")
    logger.info(f"========================================================")

    if "/edit/" in page.url or page.url != PROJECT_URL:
        logger.info(f"Переход на главный холст проекта: {PROJECT_URL}...")
        await page.goto(PROJECT_URL, wait_until="domcontentloaded")
        await asyncio.sleep(3.0)

    await dismiss_any_modal(page)

    logger.info("🧹 Очистка поля промпта...")
    await engine.clear_prompt()

    prev_cards = await engine.count_cost_cards()

    if shot_info["has_char"]:
        logger.info(f"📎 Прикрепление мастер-референса: {CHAR_REF.name}...")
        await engine.attach_reference_image(str(CHAR_REF))
        await asyncio.sleep(1.0)

    logger.info("✍️ Ввод промпта...")
    await engine.set_prompt(shot_info["prompt"])
    await asyncio.sleep(1.0)

    logger.info("🚀 Отправка в Veo 3.1...")
    await engine.submit_prompt()
    await asyncio.sleep(2.0)

    logger.info("⏳ Ожидание карточки стоимости...")
    card_info = await engine.wait_for_cost_card(previous_count=prev_cards, timeout_seconds=45)
    cost = card_info.get("cost")
    if cost is not None:
        logger.info(f"💰 Карточка стоимости: {cost} кредитов. Подтверждаем...")
        await engine.approve_cost_card()
        await asyncio.sleep(1.0)
        start_btn = await page.query_selector("[aria-label*='Generierung starten'], button:has-text('Generierung starten'), [aria-label*='Start generation']")
        if start_btn and await start_btn.is_visible():
            await start_btn.click(force=True)

    # Ожидание готовности по состоянию плитки 0
    await wait_for_tile_0_ready(page, timeout_seconds=900)

    logger.info("🎉 Рендер завершен! Скачивание...")
    await asyncio.sleep(2.0)
    await download_shot(page, target_mp4)

    if not target_mp4.exists() or target_mp4.stat().st_size < 300000:
        raise RuntimeError(f"Файл {target_mp4} поврежден или отсутствует!")

    extract_qc_frames(target_mp4)
    logger.info(f"✅ Шот {shot_id} успешно готов!")


def assemble_final_music_video():
    logger.info("\n🎞️ СБОРКА ФИНАЛЬНОГО МУЗЫКАЛЬНОГО КЛИПА (Шоты 01-36)...")

    ordered_files = [
        OUTPUT_DIR / "metamorfoza_materii_master_23_shots.mp4",
        OUTPUT_DIR / "shot_24_infinite_freedom.mp4",
        OUTPUT_DIR / "shot_25_paper_wall.mp4",
        OUTPUT_DIR / "shot_26_gravity_crumble.mp4",
        OUTPUT_DIR / "shot_27_mirror_reflections.mp4",
        OUTPUT_DIR / "shot_28_peeling_scenery.mp4",
        OUTPUT_DIR / "shot_29_stepping_to_light.mp4",
        OUTPUT_DIR / "shot_30_decisive_eyes.mp4",
        OUTPUT_DIR / "shot_31_walls_crumble_to_dust.mp4",
        OUTPUT_DIR / "shot_32_step_onto_pier.mp4",
        OUTPUT_DIR / "shot_33_lake_dawn_panorama.mp4",
        OUTPUT_DIR / "shot_34_deep_breath_freedom.mp4",
        OUTPUT_DIR / "shot_35_dewdrops_wildflowers.mp4",
        OUTPUT_DIR / "shot_36_grand_finale_sunrise.mp4",
    ]

    for f in ordered_files:
        if not f.exists():
            logger.error(f"❌ Файл отсутствует: {f}")
            return False

    concat_list_file = OUTPUT_DIR / "concat_full_36_shots.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for vid in ordered_files:
            f.write(f"file '{vid.resolve()}'\n")

    temp_video_only = OUTPUT_DIR / "temp_full_visuals_36.mp4"
    final_output = OUTPUT_DIR / "metamorfoza_materii_final_full_mv.mp4"

    logger.info("1. Склейка видеоряда (36 шотов)...")
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list_file),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast",
        "-an",
        str(temp_video_only)
    ], check=True)

    logger.info("2. Наложение мастер-аудио трека...")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(temp_video_only),
        "-i", str(AUDIO_TRACK),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest",
        str(final_output)
    ], check=True)

    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(final_output), BRAIN_DIR / final_output.name)

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "json", str(final_output)],
        capture_output=True, text=True, check=True
    )
    info = json.loads(probe.stdout)
    logger.info(f"🏆 ФИНАЛЬНЫЙ КЛИП УСПЕШНО ГОТОВ: {final_output}")
    logger.info(f"📊 Хронометраж: {info['format'].get('duration')}s, размер: {info['format'].get('size')} байт")
    return True


async def main():
    logger.info("🚀 Запуск пайплайна оставшихся шотов...")
    engine = GoogleFlowEngine(downloads_dir=str(OUTPUT_DIR))
    page = await engine.connect()

    for shot in REMAINING_SHOTS:
        try:
            await generate_single_shot(engine, page, shot)
        except Exception as e:
            logger.error(f"❌ Ошибка на шоте {shot['id']}: {e}", exc_info=True)
            logger.info("🔄 Повторная попытка через 5 секунд...")
            await asyncio.sleep(5.0)
            await generate_single_shot(engine, page, shot)

    logger.info("🎉 ВСЕ 36 ШОТОВ ГОТОВЫ!")
    assemble_final_music_video()


if __name__ == '__main__':
    asyncio.run(main())
