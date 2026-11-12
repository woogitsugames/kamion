#!/usr/bin/env bash
# pairs.sh <tag> [base]: pairs_<tag>/<cam>_<tl>.jpg = photo | render(tag) (and | render(base) when given), 3 x 320 px = 960 px
set -u
cd "$(dirname "$0")/.."
T=$1; B=${2:-}; O=pairs_$T; mkdir -p $O
SBS=/c/Users/matma/Documents/Claude/kamion/artifacts/sbs-gate3/rectified
for tl in low_overcast low_clear; do
  for f in renders_${T}sbs_$tl/sbs-g3-*.png; do
    [ -f "$f" ] || continue
    n=$(basename $f .png); id=${n##*-}
    [ -f $SBS/$id.png ] || continue
    wh=$(magick identify -format "%w %h" $SBS/$id.png); w=${wh% *}; h=${wh#* }
    cw=$(( 1080 * w / h ))
    if [ -n "$B" ] && [ -f renders_${B}sbs_$tl/$n.png ]; then
      magick \( $SBS/$id.png -resize 320x \) \( renders_${B}sbs_$tl/$n.png -gravity center -crop ${cw}x1080+0+0 +repage -resize 320x \) \( $f -gravity center -crop ${cw}x1080+0+0 +repage -resize 320x \) +append -quality 90 $O/${n}_$tl.jpg
    else
      magick \( $SBS/$id.png -resize 480x \) \( $f -gravity center -crop ${cw}x1080+0+0 +repage -resize 480x \) +append -quality 90 $O/${n}_$tl.jpg
    fi
  done
done
ls $O | wc -l
