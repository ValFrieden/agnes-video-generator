#!/bin/bash
# «Пока бьётся» / A: v2 assembly.
# trim v2 clips to beat-grid targets (fallback v1) -> QC -> concat ->
# unifying grade pass -> mux song -> final QC.
cd "$(dirname "$0")/.." || exit 1
set -eu
FR="poka_beatsya_frames"
C1="$FR/clips"      # v1 fallback
C2="$FR/clips_ph"
NM="$C2/norm"
mkdir -p "$NM"
: > "$C2/qc.log"

ORDER="seq01:2 seq02a:12 seq02b:2 seq03:10 seq04:9 seq05:10 seq06:11 seq07:4 seq08:11 seq09:11 seq10:9 seq11a:12 seq11b:2 seq12a:9.5 seq12b:9.5 seq13a:12 seq13b:3 seq14:6 seq15a:10 seq15b:10 seq15c:6 seq16:10 seq17:6.4"

rm -f "$C2/concat_list.txt"
total=0
for item in $ORDER; do
  s="${item%%:*}"; tgt="${item#*:}"
  src="$C2/$s.mp4"
  [ -f "$src" ] || { src="$C1/$s.mp4"; echo "FALLBACK v1: $s"; }
  ffmpeg -y -loglevel error -i "$src" \
    -filter_complex "trim=duration=$tgt,setpts=PTS-STARTPTS,scale=1280:720,setsar=1,fps=24" \
    -t "$tgt" -an -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p "$NM/$s.mp4"
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$NM/$s.mp4")
  total=$(awk -v a="$total" -v b="$d" 'BEGIN{printf "%.2f", a+b}')
  echo "$s -> $d (total $total)"
  bash "$FR/qc_clip.sh" "$NM/$s.mp4" -50dB || true
  echo "file 'D:/Projects/VideoGenerator/$NM/$s.mp4'" >> "$C2/concat_list.txt"
done
echo "TOTAL: $total (song 187.4)"

ffmpeg -y -loglevel error -f concat -safe 0 -i "$C2/concat_list.txt" -c copy "$C2/silent.mp4"

# Unifying grade: gentle contrast/saturation, lifted blacks, film grain, soft vignette
ffmpeg -y -loglevel error -i "$C2/silent.mp4" \
  -vf "eq=contrast=1.03:saturation=0.94:gamma=1.02,\
curves=all='0/0.02 0.25/0.24 0.75/0.77 1/0.98',\
noise=alls=3:allf=t+u,vignette=PI/7,format=yuv420p" \
  -c:v libx264 -preset medium -crf 18 "$C2/graded.mp4"

ffmpeg -y -loglevel error -i "$C2/graded.mp4" -i "$FR/song.mp3" \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest \
  "$FR/Пока бьётся — аниматик (Маяк).mp4"

ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$FR/Пока бьётся — аниматик (Маяк).mp4"
echo "QC of final:"
bash "$FR/qc_clip.sh" "$FR/Пока бьётся — аниматик (Маяк).mp4" -50dB || true
echo "ASSEMBLE2 DONE"
