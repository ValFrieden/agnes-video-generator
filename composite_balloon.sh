#!/bin/bash
# v5 stage 2: composite the stringless balloon sprite into all 15 scenes.
set -eu
FR="balloon_frames"
SP="$FR/balloon_sprite.png"
# seq: x,y,width  (sprite is 730x940; height = width*1.288)
POS="seq01:430,110,110 seq02:560,70,120 seq03:880,90,100 seq04:420,90,115 seq05:1020,80,105 seq06:330,120,110 seq07:760,280,60 seq08:400,110,110 seq09:900,90,110 seq10:640,80,115 seq11:800,100,115 seq12:920,110,110 seq13:1050,70,110 seq14:380,70,120 seq15:620,180,90"

for item in $POS; do
  s="${item%%:*}"; geo="${item##*:}"
  x="${geo%%,*}"; rest="${geo#*,}"; y="${rest%%,*}"; w="${rest##*,}"
  h=$(awk -v w="$w" 'BEGIN{printf "%d", w*1.288}')
  ffmpeg -y -loglevel error -i "$FR/${s}_base.png" -i "$SP" \
    -filter_complex "[1]scale=${w}:${h}[bal];[0][bal]overlay=${x}:${y}" \
    -frames:v 1 "$FR/${s}_final.png"
  echo "$s composited"
done
echo "COMPOSITE DONE"
