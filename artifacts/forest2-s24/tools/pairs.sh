#!/usr/bin/env bash
# forest2-s24: before | after sheets (960 px each) of the forest control cameras -> pairs/<region>_<light>_<cam>.jpg
# usage: bash artifacts/forest2-s24/tools/pairs.sh [after-round, default r1-after]
set -e
cd "$(dirname "$0")/.."
R=${1:-r1-after}
mkdir -p pairs-$R
for d in r5-before/*/High-*; do
  reg=$(basename "$(dirname "$d")"); light=$(basename "$d" | sed 's/High-//')
  for f in "$d"/*.png; do
    cam=$(basename "$f" .png); g="$R/$reg/High-$light/$cam.png"
    [ -f "$g" ] || continue
    magick \( "$f" -resize 960x -gravity NorthWest -fill white -undercolor '#00000090' -pointsize 22 -annotate +8+8 " przed  $reg $cam $light " \) \
           \( "$g" -resize 960x -gravity NorthWest -fill white -undercolor '#00000090' -pointsize 22 -annotate +8+8 " po (runda 2) " \) \
           +append -quality 88 "pairs-$R/${reg}_${light}_${cam}.jpg"
  done
done
ls pairs-$R | wc -l
