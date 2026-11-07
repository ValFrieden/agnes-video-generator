import subprocess
import os
import shutil

OUTPUT_DIR = r"d:\Projects\VideoGenerator\output"
ART_DIR = r"C:\Users\Valeri\.gemini\antigravity\brain\2d3bd19d-9cfa-4523-9fcb-2fd6327ace66"
AUDIO_PATH = os.path.join(ART_DIR, ".user_uploaded", "uploaded_media_1793789661300.mp3")

FPS = 24
WIDTH, HEIGHT = 1284, 716


def frame_count(path):
    """Real number of decoded video frames (not duration * fps)."""
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_frames",
        "-of", "default=noprint_wrappers=1:nokey=1", path
    ])
    return int(out.decode().strip())


def build_frame_exact(inputs, out):
    """Frame-accurate concat: trim by frame, re-encode, no freeze/tpad/loop.
    Shot boundaries are cumulative in frames. Returns total frame count."""
    counts = [frame_count(p) for p in inputs]
    cmd = ["ffmpeg", "-y"]
    for p in inputs:
        cmd += ["-i", p]
    parts = []
    for i, n in enumerate(counts):
        parts.append(
            f"[{i}:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},"
            f"trim=start_frame=0:end_frame={n},setpts=PTS-STARTPTS[v{i}]"
        )
    labels = "".join(f"[v{i}]" for i in range(len(inputs)))
    parts.append(f"{labels}concat=n={len(inputs)}:v=1:a=0[outv]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "[outv]",
            "-c:v", "libx264", "-crf", "16", "-preset", "slow",
            "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    subprocess.run(cmd, check=True)
    total = sum(counts)
    print(f"Frame-exact: {len(inputs)} inputs, expected {total} frames -> {out}")
    return total


def assemble_act_04():
    shots = [
        os.path.join(OUTPUT_DIR, "shot_13_blossomed_flower.mp4"),
        os.path.join(OUTPUT_DIR, "shot_14_airborne_dew.mp4"),
        os.path.join(OUTPUT_DIR, "shot_15_wide_lake.mp4"),
        os.path.join(OUTPUT_DIR, "shot_16_open_horizon.mp4"),
    ]
    for s in shots:
        if not os.path.exists(s):
            raise FileNotFoundError(f"Missing shot: {s}")

    act_04_out = os.path.join(OUTPUT_DIR, "act_04_assembled.mp4")
    print("Assembling Act IV...")
    build_frame_exact(shots, act_04_out)
    shutil.copyfile(act_04_out, os.path.join(ART_DIR, "act_04_assembled.mp4"))
    print(f"Act IV assembled: {act_04_out}")
    return act_04_out

def assemble_master_video():
    acts = [
        os.path.join(OUTPUT_DIR, "act_01_assembled.mp4"),
        os.path.join(OUTPUT_DIR, "act_02_assembled.mp4"),
        os.path.join(OUTPUT_DIR, "act_03_assembled.mp4"),
        os.path.join(OUTPUT_DIR, "act_04_assembled.mp4"),
    ]
    for a in acts:
        if not os.path.exists(a):
            raise FileNotFoundError(f"Missing act: {a}")

    raw_video = os.path.join(OUTPUT_DIR, "master_video_visuals_only.mp4")
    print("Concatenating all 4 Acts frame-exact (16 shots)...")
    total_frames = build_frame_exact(acts, raw_video)
    v_duration = total_frames / FPS
    print(f"Total video duration: {v_duration:.3f}s ({total_frames} frames)")

    # Mux with audio track
    master_mv = os.path.join(OUTPUT_DIR, "metamorfoza_materii_master_mv.mp4")
    print(f"Muxing visuals with audio from {AUDIO_PATH}...")
    
    # If audio exists, mux it
    if os.path.exists(AUDIO_PATH):
        # We mux audio and video; we can either match the video length or loop/pad.
        # Since audio is 3:39 and 16 shots * 5s is ~80s, let's see audio length.
        a_probe = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            AUDIO_PATH
        ]
        a_duration = float(subprocess.check_output(a_probe).decode().strip())
        print(f"Audio duration: {a_duration:.2f}s")

        # Master audio goes on last, unchanged (no fade), cut to video length
        cmd_mux = [
            "ffmpeg", "-y",
            "-i", raw_video,
            "-i", AUDIO_PATH,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(v_duration),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            master_mv
        ]
        subprocess.run(cmd_mux, check=True)
        shutil.copyfile(master_mv, os.path.join(ART_DIR, "metamorfoza_materii_master_mv.mp4"))
        print(f"Master MV generated: {master_mv}")
    else:
        print(f"Warning: Audio file not found at {AUDIO_PATH}")

if __name__ == "__main__":
    assemble_act_04()
    assemble_master_video()
