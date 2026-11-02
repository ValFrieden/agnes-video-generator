#!/bin/bash
# Generate 15 keyframes for the balloon scenario via the free image API.
set -u
BASE="http://localhost:8765"
IN="balloon_frames/prompts.txt"
OUT="balloon_frames"
LOG="$OUT/gen.log"
WORK=".working_dir"
: > "$LOG"
n=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  n=$((n+1))
  nn=$(printf "%02d" "$n")
  style="${line%%|*}"
  scene="${line#*|}"
  echo "[$(date +%H:%M:%S)] scene $nn: requesting..." >> "$LOG"
  resp=$(curl -s --max-time 300 -X POST "$BASE/api/image/generate" \
    -F "prompt=$style. $scene" \
    -F "size=1344x768")
  ok=$(echo "$resp" | grep -o '"ok": *true' | head -1)
  dir=$(echo "$resp" | grep -o '"dir_name": *"[^"]*"' | head -1 | sed 's/.*"dir_name": *"//;s/"//')
  if [ -n "$ok" ] && [ -n "$dir" ]; then
    src=$(find "$WORK/$dir" -name "final_image.png" 2>/dev/null | head -1)
    if [ -n "$src" ]; then
      cp "$src" "$OUT/scene_$nn.png"
      echo "[$(date +%H:%M:%S)] scene $nn: OK ($dir)" >> "$LOG"
    else
      echo "[$(date +%H:%M:%S)] scene $nn: file not found in $dir" >> "$LOG"
    fi
  else
    echo "[$(date +%H:%M:%S)] scene $nn: FAILED resp=$resp" >> "$LOG"
  fi
  sleep 3
done < "$IN"
echo "[$(date +%H:%M:%S)] ALL DONE ($n scenes)" >> "$LOG"
