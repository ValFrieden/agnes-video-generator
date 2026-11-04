#!/bin/bash
# Headless QC gate for one clip: black frames / freezes -> qc log line.
# Usage: qc_clip.sh <clip.mp4> [freeze_thresh_db]
cd "$(dirname "$0")/.." || exit 1
clip="$1"
frz="${2:--45dB}"
log="$(dirname "$clip")/qc.log"
issues=$(ffmpeg -hide_banner -i "$clip" -vf \
  "blackdetect=d=0.25:pix_th=0.08:pic_th=0.98,freezedetect=n=$frz:d=1.5" \
  -an -f null - 2>&1 | grep -E "black_start|freeze_start" | head -5)
if [ -n "$issues" ]; then
  echo "[$(date +%H:%M:%S)] QC WARN $(basename "$clip")" >> "$log"
  echo "$issues" | while IFS= read -r l; do echo "    $l" >> "$log"; done
  echo "QC WARN: $clip"
  echo "$issues"
else
  echo "[$(date +%H:%M:%S)] QC OK $(basename "$clip")" >> "$log"
  echo "QC OK: $clip"
fi
