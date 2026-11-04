# -*- coding: utf-8 -*-
"""Structural analysis of "Пока бьётся.mp3": energy curve, section boundaries, BPM."""
import subprocess, sys, io
print("START", flush=True)
import numpy as np

SRC = "../poka_beatsya_frames/song.mp3"
SR = 22050

# decode to mono f32 PCM
proc = subprocess.run(
    ["ffmpeg", "-v", "quiet", "-i", SRC, "-ac", "1", "-ar", str(SR),
     "-f", "f32le", "-"],
    capture_output=True,
)
raw = np.frombuffer(proc.stdout, dtype=np.float32)
dur = len(raw) / SR
print(f"duration: {dur:.1f}s = {int(dur//60)}:{dur%60:04.1f}")

# --- RMS energy per 0.25 s window ---
win = int(SR * 0.25)
n = len(raw) // win
rms = np.sqrt(np.mean(raw[:n*win].reshape(n, win) ** 2, axis=1))
rms_db = 20 * np.log10(rms + 1e-9)

# --- onset envelope for BPM (flux of band energies via STFT) ---
hop, nfft = 512, 2048
frames = len(raw) // hop - 1
spec = np.empty((frames, nfft // 2), dtype=np.float32)
w = np.hanning(nfft).astype(np.float32)
for i in range(frames):
    seg = raw[i*hop:i*hop+nfft]
    if len(seg) < nfft:
        break
    spec[i] = np.abs(np.fft.rfft(seg * w))[:nfft // 2]
flux = np.sum(np.maximum(0, np.diff(spec, axis=0)), axis=1)

# BPM via autocorrelation of flux, search 60–180 bpm
fr = SR / hop
ac = np.correlate(flux - flux.mean(), flux - flux.mean(), mode="full")
ac = ac[len(ac)//2:]
cands = []
for bpm in np.arange(60, 180.5, 0.5):
    lag = int(round(60.0 / bpm * fr))
    if lag < len(ac):
        cands.append((ac[lag] + ac[min(lag*2, len(ac)-1)] * 0.5, bpm))
cands.sort(reverse=True)
print("BPM candidates:", [f"{b:.1f}" for _, b in cands[:5]])

# --- section boundary detection on smoothed RMS ---
k = np.ones(8) / 8  # 2 s smoothing
sm = np.convolve(rms_db, k, mode="same")
diff = np.abs(np.diff(np.convolve(sm, np.ones(4)/4, mode="same")))
thresh = np.percentile(diff, 90)
bounds = [i * 0.25 for i in range(1, len(diff)) if diff[i] > thresh and diff[i] >= diff[max(0,i-4):i+5].max()]

# merge boundaries closer than 3 s apart
merged = []
for b in bounds:
    if not merged or b - merged[-1] > 3.0:
        merged.append(b)

# --- ASCII energy curve, 1 column per 2 s ---
print("\nenergy curve (dB rel., 1 col = 2 s, sections marked with |):")
cols = int(dur // 2)
prof = np.array([sm[min(int(t/0.25), len(sm)-1)] for t in range(0, int(dur), 2)])
lo, hi = prof.min(), prof.max()
for level in np.linspace(hi, lo, 12):
    line = "".join("#" if p >= level else " " for p in prof)
    print(f"{level:6.1f} |{line}")
bset = set(int(b // 2) for b in merged)
print("        " + "".join("|" if i in bset else " " for i in range(cols)))

print(f"\nsection boundary candidates (s): {[round(b,1) for b in merged]}")

# --- energy stats per 10 s block (to find quiet intro/outro/drops) ---
print("\nper-10s block mean dB:")
for i in range(0, int(dur), 10):
    seg = sm[i*4:min((i+10)*4, len(sm))]
    if len(seg):
        bar = "#" * int(max(0, (seg.mean() - lo) / (hi - lo) * 40))
        print(f"  {i:3d}-{i+10:3d}s {seg.mean():6.1f} {bar}")
