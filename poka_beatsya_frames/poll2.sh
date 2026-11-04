#!/bin/bash
# «Пока бьётся» / A: v2 — poll i2v tasks, collect clips to clips2/.
cd "$(dirname "$0")/.." || exit 1
set -u
BASE="http://localhost:8765"
FR="poka_beatsya_frames"
CL="$FR/clips2"
LOG="$CL/batch2.log"
WORK=".working_dir"
for i in $(seq 1 180); do
  sleep 60
  left=0
  while read -r s tid dn; do
    [ -f "$CL/$s.mp4" ] && continue
    [ -f "$CL/$s.FAILED" ] && continue
    st=$(curl -s --max-time 30 "$BASE/api/tasks/$tid" | grep -o '"status": *"[^"]*"' | head -1 | sed 's/.*"status": *"//;s/"//')
    case "$st" in
      completed)
        src=$(find "$WORK/$dn" -name "*.mp4" 2>/dev/null | head -1)
        if [ -n "$src" ]; then
          cp "$src" "$CL/$s.mp4"
          echo "[$(date +%H:%M:%S)] $s DONE" >> "$LOG"
        else
          left=$((left+1))
        fi ;;
      failed)
        echo "[$(date +%H:%M:%S)] $s FAILED" >> "$LOG"
        touch "$CL/$s.FAILED" ;;
      *) left=$((left+1)) ;;
    esac
  done < <(grep -E '^seq[0-9]+[ab]? [0-9a-f]{12} ' "$LOG")
  echo "[poll2 round $i] pending: $left"
  [ "$left" -eq 0 ] && break
done
echo "POLL2 DONE"
