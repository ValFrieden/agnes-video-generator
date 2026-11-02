#!/bin/bash
# Poll balloon tasks (GET-only), collect finished clips to clips2/.
set -u
BASE="http://localhost:8765"
CL="clips2"
LOG="$CL/batch.log"
WORK=".working_dir"
for i in $(seq 1 80); do
  sleep 60
  left=0
  while read -r s tid dn; do
    [ -f "$CL/$s.mp4" ] && continue
    st=$(curl -s --max-time 30 "$BASE/api/tasks/$tid" | grep -o '"status": *"[^"]*"' | head -1 | sed 's/.*"status": *"//;s/"//')
    case "$st" in
      completed)
        src=$(find "$WORK/$dn" -name "*.mp4" 2>/dev/null | head -1)
        if [ -n "$src" ]; then
          cp "$src" "$CL/$s.mp4"
          echo "[$(date +%H:%M:%S)] $s DONE" >> "$LOG"
        fi ;;
      failed)
        echo "[$(date +%H:%M:%S)] $s FAILED" >> "$LOG"
        touch "$CL/$s.FAILED" ;;
      *) left=$((left+1)) ;;
    esac
  done < <(grep -E '^seq[0-9]+ [0-9a-f]{12} ' "$LOG")
  echo "[$(date +%H:%M:%S)] round $i: $left pending" >> "$LOG"
  [ "$left" -eq 0 ] && break
done
echo "[$(date +%H:%M:%S)] POLL DONE" >> "$LOG"
