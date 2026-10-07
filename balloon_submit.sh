#!/bin/bash
# Submit-only: fire 15 balloon i2v tasks (foreground use). No polling here.
set -u
BASE="http://localhost:8765"
FR="balloon_frames"
CL="clips2"
LOG="$CL/batch.log"
NEG="camera movement, camera rotation, spinning, rolling, warping, morphing, face distortion, extra limbs, text, watermark, logo, subtitle"
mkdir -p "$CL"

declare -A DUR PROMPT
while IFS='|' read -r seq dur prompt; do
  [ -z "$seq" ] && continue
  DUR[$seq]=$dur; PROMPT[$seq]=$prompt
done < "$FR/shots2.txt"

for s in seq01 seq02 seq03 seq04 seq05 seq06 seq07 seq08 seq09 seq10 seq11 seq12 seq13 seq14 seq15; do
  [ -f "$CL/$s.mp4" ] && continue
  grep -q "^$s [0-9a-f]" "$LOG" && { echo "$s already submitted"; continue; }
  resp=$(curl -s --max-time 90 -X POST "$BASE/api/tasks/simple" \
    -F "prompt=${PROMPT[$s]}" -F "mode=i2v" -F "duration=${DUR[$s]}" \
    -F "video_width=1280" -F "video_height=720" -F "video_size=720P" \
    -F "negative_prompt=$NEG" \
    -F "reference_image=@$FR/$s.png;type=image/png")
  tid=$(echo "$resp" | grep -o '"task_id": *"[^"]*"' | head -1 | sed 's/.*"task_id": *"//;s/"//')
  dn=$(echo "$resp" | grep -o '"dir_name": *"[^"]*"' | head -1 | sed 's/.*"dir_name": *"//;s/"//')
  if [ -n "$tid" ]; then
    echo "$s $tid $dn" >> "$LOG"
    echo "[$(date +%H:%M:%S)] $s submitted $tid"
  else
    echo "[$(date +%H:%M:%S)] $s SUBMIT_FAILED $resp"
  fi
  sleep 15
done
echo "SUBMIT PHASE DONE"
