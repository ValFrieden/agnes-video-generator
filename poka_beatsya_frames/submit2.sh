#!/bin/bash
# «Пока бьётся» / A: v2 — submit 19 i2v tasks from unified v2 keyframes.
cd "$(dirname "$0")/.." || exit 1
set -u
BASE="http://localhost:8765"
FR="poka_beatsya_frames"
CL="$FR/clips2"
LOG="$CL/batch2.log"
NEG="flicker, strobing, jitter, frame jumps, ghosting, temporal inconsistency, morphing, warping, melting edges, crawling textures, shifting background, changing facial features, distorted face, duplicate subject, extra limbs, deformed hands, sudden lighting changes, walking, running, limb movement, arm movement, head turn, camera movement, camera pan, camera zoom, camera rotation, spinning, rolling, jump cut, text, subtitles, logo, watermark"
mkdir -p "$CL"

declare -A DUR PROMPT
while IFS='|' read -r seq dur prompt; do
  [ -z "$seq" ] && continue
  DUR[$seq]=$dur; PROMPT[$seq]=$prompt
done < "$FR/shots_A_mayak_25.txt"

ORDER="seq01 seq02a seq02b seq03 seq04 seq05 seq06 seq07 seq08 seq09 seq10 seq11a seq11b seq12a seq12b seq13a seq13b seq14 seq15a seq15b seq15c seq16 seq17"
for s in $ORDER; do
  n=$((10#$(echo "${s%%[abc]}" | tr -d 'seq')))
  [ -z "$n" ] && n=1
  img=$(printf "$FR/scene_%02d.png" "$n")
  [ -f "$img" ] || { echo "$s MISSING $img"; continue; }
  [ -f "$CL/$s.mp4" ] && { echo "$s done, skip"; continue; }
  grep -q "^$s [0-9a-f]" "$LOG" 2>/dev/null && { echo "$s already submitted"; continue; }
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
echo "SUBMIT2 PHASE DONE"
