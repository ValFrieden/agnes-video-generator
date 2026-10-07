#!/bin/bash
# v5 assembly: trim each balloon-less clip to target, overlay the stringless
# balloon sprite with gentle bobbing (rise in seq01/seq15), concat, mux song.
set -eu
CL="clips2"
NM="$CL/norm5"
mkdir -p "$NM"

ORDER="seq01:6 seq02:9 seq03:9 seq04:12 seq05:14 seq06:10 seq07:4 seq08:16 seq09:13 seq10:13 seq11:12 seq12:14 seq13:14 seq14:14 seq15:13"

# seq:x,y,width:mode   (mode: bob | rise1 | rise15)
POS="seq01:430,110,110:rise1 seq02:560,70,120:bob seq03:880,90,100:bob seq04:420,90,115:bob seq05:1020,80,105:bob seq06:1000,140,110:bob seq07:760,280,60:bob seq08:120,280,110:bob seq09:150,40,110:bob seq10:640,80,115:bob seq11:800,100,115:bob seq12:240,200,110:bob seq13:1050,70,110:bob seq14:380,70,120:bob seq15:620,180,90:rise15"

for item in $POS; do
  s="${item%%:*}"; rest="${item#*:}"
  geo="${rest%%:*}"; mode="${rest##*:}"
  x="${geo%%,*}"; r1="${geo#*,}"; y="${r1%%,*}"; w="${r1##*,}"
  tgt=$(echo "$ORDER" | tr ' ' '\n' | grep "^$s:" | cut -d: -f2)
  h=$(awk -v w="$w" 'BEGIN{printf "%d", w*1.288}')
  case "$mode" in
    rise1)  yexpr="$y-5*t+6*sin(2*PI*t/4)" ;;
    rise15) yexpr="$y-2.5*t+6*sin(2*PI*t/4.5)" ;;
    *)      yexpr="$y+8*sin(2*PI*t/4.5)" ;;
  esac
  ffmpeg -y -loglevel error -i "$CL/$s.mp4" -i "balloon_frames/balloon_sprite.png" \
    -filter_complex "[0]trim=duration=$tgt,setpts=PTS-STARTPTS,scale=1280:720,setsar=1,fps=24[bg];[1]scale=$w:$h[bal];[bg][bal]overlay=x=$x:y=$yexpr" \
    -t "$tgt" -an -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p "$NM/$s.mp4"
  echo "$s -> $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$NM/$s.mp4")"
done

rm -f "$CL/concat_list.txt"
for item in $POS; do
  s="${item%%:*}"
  echo "file 'D:/Projects/VideoGenerator/$CL/norm5/$s.mp4'" >> "$CL/concat_list.txt"
done
ffmpeg -y -loglevel error -f concat -safe 0 -i "$CL/concat_list.txt" -c copy "$CL/silent5.mp4"
ffmpeg -y -loglevel error -i "$CL/silent5.mp4" -i "Хочу навеки.mp3" \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest \
  "Хочу навеки — клип (Красный шар).mp4"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "Хочу навеки — клип (Красный шар).mp4"
echo "ASSEMBLY V5 DONE"
