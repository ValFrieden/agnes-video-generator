import subprocess
import os
import shutil

shots = [
    r'd:\Projects\VideoGenerator\output\shot_09_cracking_cube.mp4',
    r'd:\Projects\VideoGenerator\output\shot_10_smoldering_embers.mp4',
    r'd:\Projects\VideoGenerator\output\shot_11_walls_to_ash.mp4',
    r'd:\Projects\VideoGenerator\output\shot_12_emerald_sprout.mp4'
]

out_ws = r'd:\Projects\VideoGenerator\output\act_03_assembled.mp4'
art_ws = r'C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66\act_03_assembled.mp4'

concat_txt = r'd:\Projects\VideoGenerator\output\concat_act_03.txt'
with open(concat_txt, 'w', encoding='utf-8') as f:
    for s in shots:
        s_norm = s.replace('\\', '/')
        f.write(f"file '{s_norm}'\n")

subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_txt, '-c', 'copy', out_ws], check=True)
shutil.copyfile(out_ws, art_ws)

cmd_probe = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', out_ws]
dur = float(subprocess.check_output(cmd_probe).decode().strip())
print(f'Act III assembled duration: {dur:.2f}s, size: {os.path.getsize(out_ws)} bytes')
