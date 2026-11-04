#!/bin/bash
# «Пока бьётся» / A: unify ALL remaining frames to the flat cyanotype-print
# style (the style the i2i hero scenes converged to). i2i for hero scenes
# (from character_ref), t2i for hero-less scenes. See docs/dev/mv_style_consistency.md.
cd "$(dirname "$0")/.." || exit 1
set -u
BASE="http://localhost:8765"
OUT="poka_beatsya_frames"
LOG="$OUT/gen_regen3.log"
WORK=".working_dir"
STYLE="Vintage cyanotype storybook print, flat textured illustration, deep indigo and bone-white duotone with one warm golden light accent, aged paper with bone-white border and scratched edges, film grain, cinematic wide 16:9 composition"
HERO="the same hooded traveler in a long dark coat carrying a warm brass lantern as in the reference image"
NEG="daylight, bright sky, cheerful colors, oversaturated, photorealistic, text, watermark, logo, different person"
: > "$LOG"

gen() {  # $1=mode(i2i|t2i)  $2=scene_NN  $3=prompt
  local mode="$1" seq="$2" prompt="$3" extra=()
  [ "$mode" = "i2i" ] && extra=(-F "reference_image=@$OUT/character_ref.png;type=image/png")
  echo "[$(date +%H:%M:%S)] $seq ($mode): requesting..." >> "$LOG"
  local resp ok dir src
  resp=$(curl -s --max-time 300 -X POST "$BASE/api/image/generate" \
    -F "prompt=$STYLE|$prompt" -F "size=1344x768" \
    -F "negative_prompt=$NEG" "${extra[@]}")
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

gen i2i scene_01 "A single harsh lightning flash freezes $HERO standing on a dark country road at night, one instant of bone-white illumination, diagonal rain streaks across the frame"
gen i2i scene_02 "$HERO stands perfectly still in the middle of a foggy night field road, thick low fog drifting around his legs, warm lantern glow lighting the mist"
gen i2i scene_03 "A dark empty road lined with sharp black stone statue silhouettes of standing people turned away from the road, $HERO stands still among them holding his glowing lantern, steady cold rain"
gen i2i scene_04 "A lightning flash illuminates the straight empty road all the way to the horizon, $HERO a small dark shape with lantern at the center, everything else deep indigo darkness"
gen i2i scene_05 "Close view: a weathered stone statue of a sneering man holding a knife stands at the roadside, $HERO small in the distance behind it on the road with his glowing lantern, cold fog"
gen t2i scene_07 "Vast empty dark indigo night sky over a calm black sea, one tiny warm lantern flame glowing at the center bottom of the frame, minimal almost abstract scene"
gen t2i scene_11 "Macro close-up of water drops on the frosted glass of a brass lantern, the warm fire glowing inside each drop as a golden reflection, deep indigo darkness behind the glass"
gen t2i scene_12 "A white lighthouse with dark stripes glowing warmly through dark indigo drifting fog at night, a soft golden halo around its lamp, weak light reflection on calm black water below, moonless night"
gen t2i scene_14 "Almost black frame with two small warm lights pulsing in the darkness, a lantern flame in the near foreground and a distant lighthouse light point on the horizon, minimal scene"
gen t2i scene_17 "Close view of a striped lighthouse at dawn, its warm lamp glow merging with the rising golden sun, soft warm haze over calm water, the sky still indigo at the top"

echo "[$(date +%H:%M:%S)] REGEN3 DONE" >> "$LOG"
