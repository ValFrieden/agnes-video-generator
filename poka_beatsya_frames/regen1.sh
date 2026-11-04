#!/bin/bash
# Regen batch 1: scenes 3,4,6,9,12,15,16 with targeted prompt fixes.
cd "$(dirname "$0")/.." || exit 1
set -u
BASE="http://localhost:8765"
OUT="poka_beatsya_frames"
LOG="$OUT/gen_regen1.log"
WORK=".working_dir"
STYLE="Moody cyanotype-style night illustration, deep indigo and bone-white duotone, single warm golden light accent, film grain and etched scratch textures, cinematic wide 16:9 composition"
: > "$LOG"

regen() {  # $1=scene_NN  $2=prompt
  local seq="$1" prompt="$2"
  echo "[$(date +%H:%M:%S)] $seq: requesting..." >> "$LOG"
  local resp ok dir src
  resp=$(curl -s --max-time 300 -X POST "$BASE/api/image/generate" \
    -F "prompt=$STYLE|$prompt" -F "size=1344x768")
  ok=$(echo "$resp" | grep -o '"ok": *true' | head -1)
  dir=$(echo "$resp" | grep -o '"dir_name": *"[^"]*"' | head -1 | sed 's/.*"dir_name": *"//;s/"//')
  if [ -n "$ok" ] && [ -n "$dir" ]; then
    src=$(find "$WORK/$dir" -name "final_image.png" 2>/dev/null | head -1)
    [ -n "$src" ] && cp "$src" "$OUT/$seq.png" && echo "[$(date +%H:%M:%S)] $seq OK" >> "$LOG" \
      || echo "[$(date +%H:%M:%S)] $seq NO FILE" >> "$LOG"
  else
    echo "[$(date +%H:%M:%S)] $seq FAILED resp=$resp" >> "$LOG"
  fi
  sleep 3
}

rm -f "$OUT/scene_03.png" "$OUT/scene_04.png" "$OUT/scene_06.png" "$OUT/scene_09.png" "$OUT/scene_12.png" "$OUT/scene_15.png" "$OUT/scene_16.png"

regen scene_03 "A dark empty country road at night lined with only three or four sharp-edged black stone statues of standing people, clear hard silhouettes against deep indigo mist, the small traveler with a warm glowing lantern stands perfectly still among them, steady cold rain streaks"

regen scene_04 "Deep night: a single lightning flash briefly illuminates the straight empty road all the way to the dark horizon, the sky stays almost black, only the road and field edges flash bone-white for an instant, the lone traveler with lantern a small dark shape, everything else indigo darkness"

regen scene_06 "Cold indigo night sky over a dark ash plain behind the still traveler with glowing lantern, dozens of tiny glowing orange ember dots scattered through grey ash, thin smoke drifting low, the far horizon line barely lighter"

regen scene_09 "Night snowstorm in deep indigo tones, the white lighthouse closer now glowing warmly through the falling snow (a soft halo of light around its lamp only, no visible beam), the small traveler in a long dark coat stands still facing it, dense snowfall streaks"

regen scene_12 "Moonless night: the white lighthouse with dark stripes glowing through dark indigo drifting fog, only a faint warm golden halo around its lamp and a weak reflection on calm black water below, the rest of the scene stays deep blue night"

regen scene_15 "Early dawn before sunrise: the empty dark field where dark statues used to stand is still deep indigo blue, only a narrow warm golden band growing on the far horizon, faint sand drifts at the roadside, the lone traveler in a long dark coat stands on a low hill, cold blue morning light"

regen scene_16 "Pre-dawn indigo scene: the traveler in a long dark coat stands at the top of a hill facing the distant glowing lighthouse, one narrow sun ray breaking over the horizon edge behind the lighthouse, the ray warm gold against the deep blue night sky, everything else still dark"

echo "[$(date +%H:%M:%S)] REGEN1 DONE" >> "$LOG"
