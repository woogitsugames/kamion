#!/bin/bash
# side by side: photo | render, both 960x540. usage: sbs.sh <render dir> <out dir>
R=C:/Users/matma/Documents/Claude/kamion/research/_incoming/mistral-p11-dojlidy-photos-v2/files
mkdir -p "$2"
for id in 001 056 063 094; do
  f="$1/photo-P11-$id.png"; [ -f "$f" ] || f="$1/photo_P11-$id.png"; [ -f "$f" ] || continue
  magick \( "$R/P11-$id.jpg" -resize 960x540! \) \( "$f" -resize 960x540! \) +append -quality 88 "$2/sbs-P11-$id.jpg"
done
