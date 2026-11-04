import subprocess
import json
import os

def get_duration(path):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(res.stdout)
    return float(data['format']['duration'])

vids = [
    'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_scene_01_clean_veo.mp4',
    'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_scene_02_clean.mp4',
    'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_scene_03_clean.mp4',
    'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_scene_04_clean.mp4',
    'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_scene_05_clean.mp4',
    'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_scene_06_clean.mp4',
    'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_scene_07_clean.mp4',
    'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_scene_08_clean.mp4',
    'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_scene_09_clean.mp4',
    'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_scene_10_clean.mp4',
    'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/anime_scene_11_clean.mp4',
]

audio = 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames/song.mp3'
audio_dur = get_duration(audio)
print(f'Song duration: {audio_dur:.3f} s')

total_vid = 0
for i, v in enumerate(vids, 1):
    d = get_duration(v)
    total_vid += d
    print(f'Scene {i:02d}: {d:.3f} s  ({os.path.basename(v)})')

print(f'Total video raw duration: {total_vid:.3f} s')
