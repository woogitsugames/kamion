#!/usr/bin/env bash
# forest2-s24: before (round 1 = r5 of forest-height-s24) over after sheets (960 px wide) -> pairs-<round>/<region>_<light>_<cam>.jpg
# usage: bash artifacts/forest2-s24/tools/pairs.sh [round, default r1]
set -e
cd "$(dirname "$0")/.."
R=${1:-r1}
B=/c/Users/matma/Documents/Claude/kamion/artifacts/forest-height-s24/r5-after
mkdir -p pairs-$R
for d in $B/*/High-*; do
  reg=$(basename "$(dirname "$d")"); light=$(basename "$d" | sed 's/High-//')
  for f in "$d"/*.png; do
    cam=$(basename "$f" .png); g="$R/$reg/High-$light/$cam.png"
    [ -f "$g" ] || continue
    magick \( "$f" -resize 960x -gravity NorthWest -fill white -undercolor '#00000090' -pointsize 22 -annotate +8+8 " przed (runda 1, r5)  $reg $cam $light " \) \
           \( "$g" -resize 960x -gravity NorthWest -fill white -undercolor '#00000090' -pointsize 22 -annotate +8+8 " po (runda 2) " \) \
           -append -quality 88 "pairs-$R/${reg}_${light}_${cam}.jpg"
  done
done
ls pairs-$R | wc -l
