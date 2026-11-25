#!/bin/bash
# side-by-side before | after (960 px wide pairs) of the control and field cameras
cd "$(dirname "$0")"
A=${1:-after-r2}
mkdir -p sbs
for t in knyszyn-w dk65-07; do for l in clear overcast; do for x in "" "-extra"; do
  b=vqa/before/$t-$l$x; a=vqa/$A/$t-$l$x
  [ -d "$a" ] || continue
  for f in $a/*.png; do n=$(basename $f .png); [ -f $b/$n.png ] || continue
    magick $b/$n.png -resize 960x \( $a/$n.png -resize 960x \) +append -quality 86 sbs/${t}_${l}_${n}.jpg
  done
done; done; done
ls sbs | wc -l
