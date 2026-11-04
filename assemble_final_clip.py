import subprocess
import os
import shutil

WORKDIR = 'd:/Projects/VideoGenerator/moy_mir_iz_snov_frames'
OUT_FINAL = os.path.join(WORKDIR, 'Moy_Mir_Iz_Snov_FINAL_1080p.mp4')
OUT_ROOT = 'd:/Projects/VideoGenerator/Мой_Мир_Из_Снов_FINAL_1080p.mp4'
AUDIO_PATH = os.path.join(WORKDIR, 'song.mp3')

segments_meta = [
    # (id, filename, target_duration, pts_factor or None)
    ('01', 'anime_scene_01_clean_veo.mp4', 7.200, None),
    ('02', 'anime_scene_02_clean.mp4', 7.200, None),
    ('03', 'anime_scene_03_clean.mp4', 7.200, None),
    ('04', 'anime_scene_04_clean.mp4', 7.300, None),
    ('05', 'anime_scene_05_clean.mp4', 7.200, 7.200 / 7.167),
    ('06', 'anime_scene_06_clean.mp4', 7.200, None),
    ('07', 'anime_scene_07_clean.mp4', 7.200, None),
    ('08', 'anime_scene_08_clean.mp4', 7.300, None),
    ('09', 'anime_scene_09_clean.mp4', 7.200, None),
    ('10', 'anime_scene_10_clean.mp4', 7.200, None),
    ('11', 'anime_scene_11_clean.mp4', 7.800, None),
]

temp_segments = []

print('=== STEP 1: PREPARING NORMALIZED 1080p 24FPS SEGMENTS ===')
for sc_id, fname, target_dur, pts_factor in segments_meta:
    src_path = os.path.join(WORKDIR, fname)
    seg_out = os.path.join(WORKDIR, f'norm_s{sc_id}_1080p.mp4')
    temp_segments.append(seg_out)

    # Build video filter
    vf_parts = [
        'scale=1920:1080:flags=lanczos',
        'fps=24'
    ]
    if pts_factor is not None:
        vf_parts.append(f'setpts=PTS*{pts_factor:.6f}')
    
    if sc_id == '11':
        # Add subtle fade to black on the last 0.8 second
        vf_parts.append(f'fade=t=out:st=7.0:d=0.8')

    vf_str = ','.join(vf_parts)

    cmd = [
        'ffmpeg', '-y',
        '-ss', '0',
        '-t', str(target_dur),
        '-i', src_path,
        '-vf', vf_str,
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '16',
        '-pix_fmt', 'yuv420p',
        '-an',
        seg_out
    ]

    print(f'Processing Scene {sc_id} -> {target_dur}s (pts: {pts_factor})...')
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f'Error processing Scene {sc_id}:', res.stderr)
        exit(1)

print('=== STEP 2: CREATING CONCAT LIST ===')
concat_list_file = os.path.join(WORKDIR, 'concat_list.txt')
with open(concat_list_file, 'w', encoding='utf-8') as f:
    for seg in temp_segments:
        # ffmpeg concat demuxer expects forward slashes or escaped backslashes
        safe_path = seg.replace('\\', '/')
        f.write(f"file '{safe_path}'\n")

print('=== STEP 3: CONCATENATING ALL 11 SEGMENTS & MERGING WITH MASTER AUDIO ===')
concat_video_temp = os.path.join(WORKDIR, 'temp_video_only.mp4')
cmd_concat = [
    'ffmpeg', '-y',
    '-f', 'concat',
    '-safe', '0',
    '-i', concat_list_file,
    '-c', 'copy',
    concat_video_temp
]
res_concat = subprocess.run(cmd_concat, capture_output=True, text=True)
if res_concat.returncode != 0:
    print('Concat error:', res_concat.stderr)
    exit(1)

print('=== STEP 4: MERGING AUDIO & EXPORTING MASTER 1080P MV ===')
cmd_final = [
    'ffmpeg', '-y',
    '-i', concat_video_temp,
    '-i', AUDIO_PATH,
    '-c:v', 'copy',
    '-c:a', 'aac',
    '-b:a', '320k',
    '-shortest',
    OUT_FINAL
]
res_final = subprocess.run(cmd_final, capture_output=True, text=True)
if res_final.returncode != 0:
    print('Final merge error:', res_final.stderr)
    exit(1)

print('=== STEP 5: COPYING TO ROOT DIRECTORY ===')
shutil.copyfile(OUT_FINAL, OUT_ROOT)

print('SUCCESS: Complete Anime MV created at:')
print('  1) ' + OUT_FINAL)
print('  2) Master MV copied to root directory successfully!')

