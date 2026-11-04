import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path("d:/Projects/VideoGenerator/begi_za_solntsem_frames")
SRC_DIR = BASE_DIR / "clips_flow_v2"
FINAL_DIR = BASE_DIR / "final_scenes"
FINAL_DIR.mkdir(exist_ok=True)

# Canonical mapping of scenes according to script and song structure
MAPPING = [
    ("scene_01_intro_bench.mp4", "scene_tile_09.mp4", "Сцена 01 (00:00-00:08): Интро. Мокрая скамья, фонари, закрытый желтый зонт, людей нет"),
    ("scene_02_umbrella_pickup.mp4", "scene_tile_08.mp4", "Сцена 02 (00:08-00:16): Путник со спины у скамьи под дождем с желтым зонтом"),
    ("scene_03_puddle_sunbeam.mp4", "scene_tile_06.mp4", "Сцена 03 (00:16-00:24): Крупный план брусчатки и лужи с кругами дождя и лучом солнца"),
    ("scene_04_stone_alley.mp4", "scene_tile_11.mp4", "Сцена 04 (00:24-00:32): Узкий каменный переулок, луч солнца сквозь дождь, путник по центру"),
    ("scene_05_attic_window.mp4", "scene_tile_05.mp4", "Сцена 05 (00:32-00:40): Кирпичный фасад, распахнутое чердачное окно с золотым светом"),
    ("scene_06_stone_bridge.mp4", "scene_tile_07.mp4", "Сцена 06 (00:40-00:48): Величественный мост через реку на рассвете на стыке туч и солнца"),
    ("scene_07_face_closeup.mp4", "scene_tile_10.mp4", "Сцена 07 (00:48-00:56): Крупный план лица в профиль/3/4 под желтым зонтом, рассветный свет"),
    ("scene_08_arched_colonnade.mp4", "scene_tile_04.mp4", "Сцена 08 (00:56-01:04): Каменная колоннада в сумерках, желтый зонт как факел надежды"),
    ("scene_09_river_promenade.mp4", "scene_tile_03.mp4", "Сцена 09 (01:04-01:12): Набережная реки у балюстрады, путник отводит зонт назад, солнечная пыль"),
    ("scene_10_cathedral_spires.mp4", "scene_tile_02.mp4", "Сцена 10 (01:12-01:20): Нижний ракурс на шпили собора и крыши, лучи солнца пробивают тучи"),
    ("scene_11_rooftop_panorama.mp4", "scene_tile_01.mp4", "Сцена 11 (01:20-01:28): Панорама с террасы крыши на весь город на рассвете"),
    ("scene_12_outro_park_sun.mp4", "scene_tile_00.mp4", "Сцена 12 (01:28-01:36): Финал. Герой крупным планом у солнечной скамьи в парке под желтым зонтом, цветы")
]

print("Copying and renaming canonical scenes...")
concat_lines = []

for final_name, src_name, desc in MAPPING:
    src_file = SRC_DIR / src_name
    dst_file = FINAL_DIR / final_name
    shutil.copy2(src_file, dst_file)
    print(f"  [OK] {src_name} -> {final_name} | {desc}")
    # Forward slashes for ffmpeg concat
    concat_lines.append(f"file '{dst_file.as_posix()}'")

concat_file = FINAL_DIR / "concat_list.txt"
concat_file.write_text("\n".join(concat_lines), encoding="utf-8")
print(f"\nWrote concat list to {concat_file}")

# Assemble video with song.mp3
output_clip = BASE_DIR / "Беги_за_солнцем_Финал_Flow_Veo.mp4"
song_file = BASE_DIR / "song.mp3"

print("\nRunning FFmpeg assembly...")
cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", str(concat_file),
    "-i", str(song_file),
    "-map", "0:v:0", "-map", "1:a:0",
    "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "320k",
    "-shortest",
    str(output_clip)
]

res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode == 0:
    print(f"\nSUCCESS! Assembled video: {output_clip}")
    print(f"Size: {round(output_clip.stat().st_size / (1024*1024), 2)} MB")
else:
    print("FFmpeg error:", res.stderr)
