#!/bin/bash
# Animatic: build the full clip from still keyframes (placeholder clips)
# to validate the assembly pipeline and give a watchable preview.
cd "$(dirname "$0")/.." || exit 1
set -eu
FR="poka_beatsya_frames"
CP="$FR/clips_ph"
mkdir -p "$CP"

ORDER="seq01:2 seq02a:12 seq02b:2 seq03:10 seq04:9 seq05:10 seq06:11 seq07:4 seq08:11 seq09:11 seq10:9 seq11a:12 seq11b:2 seq12a:9.5 seq12b:9.5 seq13a:12 seq13b:3 seq14:6 seq15a:10 seq15b:10 seq15c:6 seq16:10 seq17:6.4"

for item in $ORDER; do
  s="${item%%:*}"; tgt="${item#*:}"
  [ -f "$CP/$s.mp4" ] && continue
  n=$((10#$(echo "${s%%[abc]}" | tr -d 'seq')))
  img=$(printf "$FR/scene_%02d.png" "$n")
  ffmpeg -y -loglevel error -loop 1 -framerate 24 -i "$img" \
    -filter_complex "scale=1280:720,setsar=1" -t "$tgt" \
    -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p "$CP/$s.mp4"
  echo "$s placeholder $tgt"
done
echo "PLACEHOLDERS DONE"
# reuse assemble2 with placeholders as primary source and no fallback
sed -e 's|CL="$FR/clips"      # v1 fallback|CL="$FR/clips_none"|' \
    -e 's|C2="$FR/clips2"     # v2 primary|C2="$FR/clips_ph"|' \
    -e 's|Пока бьётся — клип (Маяк).mp4|Пока бьётся — аниматик (Маяк).mp4|g' \
    "$FR/assemble2.sh" > "$FR/assemble_animatic.sh"
bash "$FR/assemble_animatic.sh"
