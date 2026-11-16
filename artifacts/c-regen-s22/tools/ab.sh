#!/bin/bash
# side-by-side before|after JPG (each 800 px wide) for chosen cameras: tools/ab.sh <region> <Tier-lighting> cam1 cam2 ...
cd "$(dirname "$0")/.."; r=$1; tl=$2; shift 2; mkdir -p view
for c in "$@"; do magick before/$r/$tl/$c.png -resize 800x after/$r/$tl/$c.png -resize 800x +append -quality 85 view/ab_${r}_${tl}_$c.jpg; done
