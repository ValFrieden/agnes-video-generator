#!/bin/bash
# «Пока бьётся» / «Кинетическая диорама»: build the full film.
# Per segment: 2-layer paper parallax (far/near counter-drift) or gentle
# zoom (single-layer scenes), source = i2v clip if present else still.
# Then: concat -> global swinging heart overlay -> unifying grade -> song -> QC.
cd "$(dirname "$0")/.." || exit 1
set -eu
FR="poka_beatsya_frames"
C2="$FR/clips2"          # i2v ambient clips (optional per scene)
ND="$FR/clips_d/norm"    # parallax-normalized segments
mkdir -p "$ND"

# seq|target|scene|mode(L/S)|horizon|videooffset
TABLE="seq01|2|01|L|0.86|0
seq02a|12|02|L|0.86|0
seq02b|2|02|L|0.86|3
seq03|10|03|L|0.86|0
seq04|9|04|L|0.86|0
seq05|10|05|S|0|0
seq06|11|06|L|0.86|0
seq07|4|07|S|0|0
seq08|11|08|L|0.86|0
seq09|11|09|L|0.86|0
seq10|9|10|L|0.86|0
seq11a|12|11|S|0|0
seq11b|2|11|S|0|3
seq12a|9.5|12|L|0.86|0
seq12b|9.5|12|L|0.86|4
seq13a|12|13|L|0.86|0
seq13b|3|13|L|0.86|5
seq14|6|14|S|0|0
seq15a|10|15|L|0.86|0
seq15b|10|15|L|0.86|3
seq15c|6|15|L|0.86|7
seq16|10|16|L|0.86|0
seq17|6.4|17|L|0.86|0"

build_segment() { # seq target scene mode horizon voff
  local seq="$1" T="$2" sc="$3" mode="$4" hz="$5" voff="$6"
  local out="$ND/$seq.mp4"
  [ -f "$out" ] && { echo "$seq exists"; return; }
  local src_vid="$C2/seq${sc%%[a-z]}$([ "${seq: -1}" = "${seq//[0-9]/}" ] && echo "${seq: -1}" || echo).mp4"
  # i2v clip exists for this scene's base name? (seq12a -> seq12a.mp4 only for a-segments)
  if [ -f "$C2/$seq.mp4" ]; then src="$C2/$seq.mp4"; instart="$voff"
  elif [ -f "$C2/seq${sc}.mp4" ] && [ "$sc" != "$seq" ]; then src="$C2/seq${sc}.mp4"; instart="$voff"
  else src="$FR/scene_$sc.png"; instart=""; fi
  local input_args=()
  if [ "${src##*.}" = "png" ]; then
    input_args=(-loop 1 -framerate 24 -t "$T" -i "$src")
  else
    if [ -n "$instart" ] && [ "$instart" != "0" ]; then input_args=(-ss "$instart" -i "$src"); else input_args=(-i "$src"); fi
  fi
  local HYpx=$(awk -v h="$hz" -v OH=792 'BEGIN{printf "%d", h*OH}')
  local BANDH=$((792 - HYpx + 40))
  local BANDOFF=$((720 - BANDH))
  local fc
  if [ "$mode" = "L" ]; then
    fc="[0]trim=duration=$T,setpts=PTS-STARTPTS,fps=24,scale=1408:792,setsar=1[s];\
[s]split=2[s1][s2];\
[s1]crop=1280:720:x='64+$dir*24*(t/$T)':y=36[far];\
[s2]crop=1408:$BANDH:0:$HYpx[b0];\
[b0]crop=1280:$BANDH:x='36-$dir*36*(t/$T)':y=0[nb];\
[nb]drawbox=x=0:y=0:w=1280:h=3:color=0x14141C@1:t=fill[nr];\
[far][nr]overlay=0:$BANDOFF[out]"
  else
    local NF=$(awk -v t="$T" 'BEGIN{printf "%d", t*24}')
    fc="[0]trim=duration=$T,setpts=PTS-STARTPTS,fps=24,scale=1408:792,setsar=1,\
zoompan=z='1+0.05*(1-on/$NF)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1280x720:fps=24[out]"
  fi
  ffmpeg -y -loglevel error "${input_args[@]}" -filter_complex "$fc" -map "[out]" \
    -t "$T" -an -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p "$out"
  echo "$seq -> $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")"
}

rm -f "$ND"/*.mp4 "$ND/concat_list.txt"
total=0
idx=0
for item in $TABLE; do
  IFS='|' read -r seq T sc mode hz voff <<< "$item"
  idx=$((idx+1))
  dir=$(( idx % 2 == 0 ? -1 : 1 ))
  build_segment "$seq" "$T" "$sc" "$mode" "$hz" "$voff"
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$ND/$seq.mp4")
  total=$(awk -v a="$total" -v b="$d" 'BEGIN{printf "%.2f", a+b}')
  echo "  total $total"
  echo "file 'D:/Projects/VideoGenerator/$ND/$seq.mp4'" >> "$ND/concat_list.txt"
done
echo "TOTAL: $total (song 187.4)"

ffmpeg -y -loglevel error -f concat -safe 0 -i "$ND/concat_list.txt" -c copy "$FR/clips_d/silent_d.mp4"

# heart overlay (swinging on a thread) + unifying grade, one pass
ffmpeg -y -loglevel error -i "$FR/clips_d/silent_d.mp4" -loop 1 -framerate 24 -t 187.4 -i "$FR/heart_sprite.png" \
  -filter_complex "\
[1]scale=264:340[hrt];\
[0][hrt]overlay=x=120:y='-2+5*sin(2*PI*t/4.5)':shortest=1,\
eq=contrast=1.03:saturation=0.94:gamma=1.02,\
curves=all='0/0.02 0.25/0.24 0.75/0.77 1/0.98',\
noise=alls=3:allf=t+u,vignette=PI/7,format=yuv420p" \
  -c:v libx264 -preset medium -crf 18 "$FR/clips_d/graded_d.mp4"

ffmpeg -y -loglevel error -i "$FR/clips_d/graded_d.mp4" -i "$FR/song.mp3" \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest \
  "$FR/Пока бьётся — аниматик v2 (Диорама).mp4"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$FR/Пока бьётся — аниматик v2 (Диорама).mp4"
echo "DIORAMA ANIMATIC V2 DONE"
