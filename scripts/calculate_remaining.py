import subprocess, glob, os, sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def get_dur(path):
    if not os.path.exists(path): return 0.0
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except:
        return 0.0

audio_files = glob.glob('*.mp3') + glob.glob('output/*.mp3')
audio_path = 'uploaded_media_1793789661300.mp3'
if not os.path.exists(audio_path) and audio_files:
    audio_path = audio_files[0]

audio_dur = get_dur(audio_path)
s23_dur = get_dur('output/metamorfoza_materii_master_23_shots.mp4')

s24_files = glob.glob('output/*shot*24*.mp4')
s24_path = s24_files[0] if s24_files else ''
s24_dur = get_dur(s24_path)

s25_dur = get_dur('output/shot_25_paper_wall.mp4')
s26_dur = get_dur('output/shot_26_paper_granite_wall.mp4')

current_total = s23_dur + s24_dur + s25_dur + s26_dur
remaining = audio_dur - current_total

print(f"Audio file: {audio_path}")
print(f"Audio duration: {audio_dur:.2f}s ({int(audio_dur//60)}:{int(audio_dur%60):02d})")
print(f"Shots 01-23 duration: {s23_dur:.2f}s")
print(f"Shot 24 duration: {s24_dur:.2f}s ({os.path.basename(s24_path)})")
print(f"Shot 25 duration: {s25_dur:.2f}s")
print(f"Shot 26 duration: {s26_dur:.2f}s")
print(f"Total ready so far (Shots 01-26): {current_total:.2f}s ({int(current_total//60)}:{int(current_total%60):02d})")
print(f"Remaining duration to cover: {remaining:.2f}s ({int(remaining//60)}:{int(remaining%60):02d})")
clips_needed = remaining / 7.93
print(f"At ~7.93s per Flow clip: {clips_needed:.2f} clips (approx {round(clips_needed)} clips)")
