#!/bin/bash
# «Пока бьётся» / вариант A «Маяк»: trim clips to targets, concat, mux song.
cd "$(dirname "$0")/.." || exit 1
set -eu
FR="poka_beatsya_frames"
CL="$FR/clips"
NM="$CL/norm"
mkdir -p "$NM"

# seq:target   (sum = 187.4 s)
ORDER="seq01:2 seq02:14 seq03:10 seq04:9 seq05:10 seq06:11 seq07:4 seq08:11 seq09:11 seq10:9 seq11:14 seq12a:9.5 seq12b:9.5 seq13:15 seq14:6 seq15a:13 seq15b:13 seq16:10 seq17:6.4"

rm -f "$CL/concat_list.txt"
for item in $ORDER; do
  s="${item%%:*}"; tgt="${item#*:}"
  ffmpeg -y -loglevel error -i "$CL/$s.mp4" \
    -filter_complex "trim=duration=$tgt,setpts=PTS-STARTPTS,scale=1280:720,setsar=1,fps=24" \
    -t "$tgt" -an -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p "$NM/$s.mp4"
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$NM/$s.mp4")
  echo "$s -> $d"
  echo "file 'D:/Projects/VideoGenerator/$NM/$s.mp4'" >> "$CL/concat_list.txt"
done

ffmpeg -y -loglevel error -f concat -safe 0 -i "$CL/concat_list.txt" -c copy "$CL/silent.mp4"
ffmpeg -y -loglevel error -i "$CL/silent.mp4" -i "$FR/song.mp3" \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest \
  "$FR/Пока бьётся — клип (Маяк).mp4"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$FR/Пока бьётся — клип (Маяк).mp4"
echo "ASSEMBLY DONE"
