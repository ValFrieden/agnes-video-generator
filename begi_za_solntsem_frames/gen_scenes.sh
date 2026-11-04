#!/bin/bash
# «Беги за солнцем» / Вариант A «Жёлтый зонт»: генерация 12 кейнфреймов через локальный Agnes сервер
set -u
BASE="http://localhost:8765"
OUT="begi_za_solntsem_frames"
LOG="$OUT/gen.log"
WORK=".working_dir"
: > "$LOG"

n=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  n=$((n+1))
  seq=$(printf "scene_%02d" "$n")
  [ -f "$OUT/$seq.png" ] && { echo "[$(date +%H:%M:%S)] $seq exists, skip" >> "$LOG"; continue; }
  prompt="${line#*|}"
  echo "[$(date +%H:%M:%S)] $seq: requesting..." >> "$LOG"
  resp=$(curl -s --max-time 300 -X POST "$BASE/api/image/generate" \
    -F "prompt=$prompt" -F "size=1280x720" -F "reference_image=@$OUT/character_ref.jpg")
  ok=$(echo "$resp" | grep -o '"ok": *true' | head -1)
  dir=$(echo "$resp" | grep -o '"dir_name": *"[^"]*"' | head -1 | sed 's/.*"dir_name": *"//;s/"//')
  if [ -n "$ok" ] && [ -n "$dir" ]; then
    src=$(find "$WORK/$dir" -name "final_image.png" 2>/dev/null | head -1)
    [ -n "$src" ] && cp "$src" "$OUT/$seq.png" && echo "[$(date +%H:%M:%S)] $seq OK ($dir)" >> "$LOG" \
      || echo "[$(date +%H:%M:%S)] $seq NO FILE ($dir)" >> "$LOG"
  else
    echo "[$(date +%H:%M:%S)] $seq FAILED resp=$resp" >> "$LOG"
  fi
  sleep 3
done < "$OUT/prompts_A_umbrella.txt"
echo "[$(date +%H:%M:%S)] GEN DONE ($n prompts)" >> "$LOG"
