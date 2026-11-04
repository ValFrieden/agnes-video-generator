#!/bin/bash
# «Пока бьётся» / A: re-generate character scenes i2i from the canonical
# character_ref.png so the traveler stays the same person across the video.
# Per docs/dev/mv_style_consistency.md.
cd "$(dirname "$0")/.." || exit 1
set -u
BASE="http://localhost:8765"
OUT="poka_beatsya_frames"
LOG="$OUT/gen_regen2.log"
WORK=".working_dir"
STYLE="Moody cyanotype-style night illustration, deep indigo and bone-white duotone, single warm golden light accent, film grain and etched scratch textures, cinematic wide 16:9 composition"
HERO="the same hooded traveler in a long dark coat carrying a warm brass lantern as in the reference image"
NEG="daylight, bright sky, cheerful colors, oversaturated, text, watermark, logo, different person, clean shaven face"
: > "$LOG"

regen() {  # $1=scene_NN  $2=prompt
  local seq="$1" prompt="$2"
  echo "[$(date +%H:%M:%S)] $seq: requesting i2i..." >> "$LOG"
  local resp ok dir src
  resp=$(curl -s --max-time 300 -X POST "$BASE/api/image/generate" \
    -F "prompt=$STYLE|$prompt" -F "size=1344x768" \
    -F "negative_prompt=$NEG" \
    -F "reference_image=@$OUT/character_ref.png;type=image/png")
  ok=$(echo "$resp" | grep -o '"ok": *true' | head -1)
  dir=$(echo "$resp" | grep -o '"dir_name": *"[^"]*"' | head -1 | sed 's/.*"dir_name": *"//;s/"//')
  if [ -n "$ok" ] && [ -n "$dir" ]; then
    src=$(find "$WORK/$dir" -name "final_image.png" 2>/dev/null | head -1)
    [ -n "$src" ] && cp "$src" "$OUT/$seq.png" && echo "[$(date +%H:%M:%S)] $seq OK" >> "$LOG" \
      || echo "[$(date +%H:%M:%S)] $seq NO FILE" >> "$LOG"
  else
    echo "[$(date +%H:%M:%S)] $seq FAILED resp=$resp" >> "$LOG"
  fi
  sleep 3
}

regen "$@"
echo "[$(date +%H:%M:%S)] REGEN2 ITEM DONE" >> "$LOG"
