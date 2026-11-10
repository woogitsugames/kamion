#!/bin/bash
# before / after pairs (stacked, 1500 px wide, labelled) for every control camera: sheets/<tier>-<light>_<cam>.jpg
# usage: bash artifacts/truck-ext-r10/tools/sheets.sh <before dir> <after dir>
R=artifacts/truck-ext-r10; A=$1; Z=$2
mkdir -p $R/sheets
for d in High-overcast High-clear Low-overcast Low-clear; do
  for c in chase truck-side truck-rear34 trailer-side truck-34 truck-34r trailer-34 truck-front; do
    [ -f $R/$A/$d/$c.png ] && [ -f $R/$Z/$d/$c.png ] || continue
    magick \( $R/$A/$d/$c.png -resize 1500x -gravity NorthWest -fill white -undercolor '#000a' -pointsize 26 -annotate +10+8 " $A | $d | $c " \) \
           \( $R/$Z/$d/$c.png -resize 1500x -gravity NorthWest -fill white -undercolor '#000a' -pointsize 26 -annotate +10+8 " $Z | $d | $c " \) \
           -append -quality 88 $R/sheets/${d}_${c}.jpg
  done
done
ls $R/sheets | wc -l
