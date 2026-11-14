#!/bin/bash
# side by side: CC0 photo | render, 960 px each. usage: sbs.sh <render dir> <out dir>
P=/c/Users/matma/Documents/Claude/kamion/research/_incoming/mistral-p11-dojlidy-photos-v2/files
mkdir -p "$2"
for id in 001 063 056 094 129; do
  r=$(ls "$1"/photo-P11-$id*.png 2>/dev/null | head -1); [ -z "$r" ] && continue
  magick \( $P/P11-$id.jpg -resize 960x540! \) \( "$r" -resize 960x540! \) +append -quality 88 "$2/sbs-P11-$id.jpg"
done
