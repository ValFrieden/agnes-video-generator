#!/bin/bash
# v5 stage 1: generate 15 balloon-less scenes + one balloon sprite on white.
set -u
BASE="http://localhost:8765"
OUT="balloon_frames"
LOG="$OUT/gen_v5.log"
WORK=".working_dir"
: > "$LOG"

# balloon sprite
echo "[$(date +%H:%M:%S)] sprite: requesting..." >> "$LOG"
resp=$(curl -s --max-time 300 -X POST "$BASE/api/image/generate" \
  -F "prompt=A single glossy round red balloon with a small sealed knot at the bottom, storybook gouache painting style, centered large on a pure plain white background, soft even studio light" \
  -F "size=1024x1024")
dir=$(echo "$resp" | grep -o '"dir_name": *"[^"]*"' | head -1 | sed 's/.*"dir_name": *"//;s/"//')
if [ -n "$dir" ]; then
  src=$(find "$WORK/$dir" -name "final_image.png" 2>/dev/null | head -1)
  [ -n "$src" ] && cp "$src" "$OUT/balloon_sprite_raw.png" && echo "[$(date +%H:%M:%S)] sprite OK" >> "$LOG"
else
  echo "[$(date +%H:%M:%S)] sprite FAILED resp=$resp" >> "$LOG"
fi
sleep 3

while IFS='|' read -r seq prompt; do
  [ -z "$seq" ] && continue
  echo "[$(date +%H:%M:%S)] $seq: requesting..." >> "$LOG"
  resp=$(curl -s --max-time 300 -X POST "$BASE/api/image/generate" \
    -F "prompt=$prompt" -F "size=1344x768")
  ok=$(echo "$resp" | grep -o '"ok": *true' | head -1)
  dir=$(echo "$resp" | grep -o '"dir_name": *"[^"]*"' | head -1 | sed 's/.*"dir_name": *"//;s/"//')
  if [ -n "$ok" ] && [ -n "$dir" ]; then
    src=$(find "$WORK/$dir" -name "final_image.png" 2>/dev/null | head -1)
    [ -n "$src" ] && cp "$src" "$OUT/${seq}_base.png" && echo "[$(date +%H:%M:%S)] $seq OK" >> "$LOG"
  else
    echo "[$(date +%H:%M:%S)] $seq FAILED resp=$resp" >> "$LOG"
  fi
  sleep 3
done < "$OUT/prompts_v5.txt"
echo "[$(date +%H:%M:%S)] V5 STAGE1 DONE" >> "$LOG"
