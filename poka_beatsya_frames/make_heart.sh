#!/bin/bash
# Draw the paper-heart sprite deterministically (no AI): indigo heart curve,
# thin golden kintsugi seam, bone-white thread. Output: heart_sprite.png (RGBA).
cd "$(dirname "$0")/.." || exit 1
set -eu
FR="poka_beatsya_frames"
W=480; H=620; CX=240; S=150; CY=310
U="(X-$CX)/$S"
V="($CY-Y)/$S"
U2="($U)*($U)"
V2="($V)*($V)"
CUBE="( ($U2+$V2-1)*($U2+$V2-1)*($U2+$V2-1) )"
VCUB="($V)*($V)*($V)"
INSIDE="lt($CUBE-$U2*$VCUB,0)"
SEAM="lt(abs(($V)+0.8*($U)-0.05),0.02)"
# paper texture: subtle darker speckle via hash-ish stripes
TXT="lt(abs(sin((X)*12.9898+(Y)*78.233)*43758.5453-floor(sin((X)*12.9898+(Y)*78.233)*43758.5453)),0.06)"
ffmpeg -y -loglevel error -f lavfi -i "color=c=black@0:s=${W}x${H},format=rgba" -frames:v 1 -vf \
 "geq=r='if($INSIDE,if($SEAM,212,if($TXT,18,26)),0)':g='if($INSIDE,if($SEAM,175,if($TXT,30,42)),0)':b='if($INSIDE,if($SEAM,55,if($TXT,70,94)),0)':a='if($INSIDE,255,0)'" \
 "$FR/heart_shape.png"
ffmpeg -y -loglevel error -i "$FR/heart_shape.png" \
  -vf "drawbox=x=$((CX-2)):y=0:w=4:h=$(($CY-$S+6)):color=0xE8E2D0@1:t=fill" \
  "$FR/heart_sprite.png"
rm -f "$FR/heart_shape.png"
echo "HEART SPRITE DONE"
