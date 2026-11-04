#!/bin/bash
# «Пока бьётся» / вариант A «Маяк»: submit 19 i2v tasks (foreground, no polling).
cd "$(dirname "$0")/.." || exit 1
set -u
BASE="http://localhost:8765"
FR="poka_beatsya_frames"
CL="$FR/clips"
LOG="$CL/batch.log"
NEG="walking, running, gait, limb movement, arm movement, hand movement, head turn, camera movement, camera pan, camera zoom, camera rotation, spinning, rolling, warping, morphing, melting, face distortion, extra fingers, deformed hands, changing shape, object duplication, flickering geometry, jump cut, text, watermark, logo, subtitle"
mkdir -p "$CL"

declare -A DUR PROMPT SCENE
while IFS='|' read -r seq dur prompt; do
  [ -z "$seq" ] && continue
  DUR[$seq]=$dur; PROMPT[$seq]=$prompt
done < "$FR/shots_A_mayak.txt"

ORDER="seq01 seq02 seq03 seq04 seq05 seq06 seq07 seq08 seq09 seq10 seq11 seq12a seq12b seq13 seq14 seq15a seq15b seq16 seq17"
for s in $ORDER; do
  base="${s%%[ab]}"                      # seq12a -> seq12
  SCENE[$s]=$(printf "$FR/scene_%02d.png" "${base#seq}")
done

for s in $ORDER; do
  [ -f "$CL/$s.mp4" ] && { echo "$s done, skip"; continue; }
  grep -q "^$s [0-9a-f]" "$LOG" 2>/dev/null && { echo "$s already submitted"; continue; }
  img="${SCENE[$s]}"
  [ -f "$img" ] || { echo "$s MISSING KEYFRAME $img"; continue; }
  resp=$(curl -s --max-time 180 -X POST "$BASE/api/tasks/simple" \
    -F "prompt=${PROMPT[$s]}" -F "mode=i2v" -F "duration=${DUR[$s]}" \
    -F "video_width=1280" -F "video_height=720" -F "video_size=720P" \
    -F "negative_prompt=$NEG" \
    -F "reference_image=@$img;type=image/png")
  tid=$(echo "$resp" | grep -o '"task_id": *"[^"]*"' | head -1 | sed 's/.*"task_id": *"//;s/"//')
  dn=$(echo "$resp" | grep -o '"dir_name": *"[^"]*"' | head -1 | sed 's/.*"dir_name": *"//;s/"//')
  if [ -n "$tid" ]; then
    echo "$s $tid $dn" >> "$LOG"
    echo "[$(date +%H:%M:%S)] $s submitted $tid"
  else
    echo "[$(date +%H:%M:%S)] $s SUBMIT_FAILED $resp"
  fi
  sleep 20
done
echo "SUBMIT PHASE DONE"
