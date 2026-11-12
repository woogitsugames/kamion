#!/usr/bin/env bash
# pairs.sh <tag>: pairs_<tag>/ba_<cam>_<tl>.jpg = before | after (junction cameras: b7 of junctions-r6; SBS cameras: i3 of
# biezenstwa-island), 480 px each; pairs_<tag>/photo_<id>_<tl>.jpg = Mapillary photo | render (same pose, 4:3 crop), 480 px each;
# pairs_<tag>/tri_<id>_<tl>.jpg = photo | before | after, 320 px each. All <= 960 px wide.
set -u
cd "$(dirname "$0")/.."
T=$1; O=pairs_$T; mkdir -p $O
MA=/c/Users/matma/Documents/Claude/kamion/artifacts
SBS=$MA/sbs-gate3/rectified
for tl in low_clear low_overcast; do
  R=renders_${T}_$tl
  [ -d $R ] || continue
  for f in $R/*.png; do
    n=$(basename $f .png)
    case $n in
      sbs-g3-*) id=${n##*-}; lt=${tl#low_}; B=$MA/sbs-poses-r3/after/renders/Low-$lt/$n.png   # main world, ADR 0143 poses
        [ -f $B ] || B=$MA/biezenstwa-island/renders_i3sbs_$tl/$n.png
        if [ -f $SBS/$id.png ]; then
          wh=$(magick identify -format "%w %h" $SBS/$id.png); w=${wh% *}; h=${wh#* }; cw=$(( 1080 * w / h ))
          magick \( $SBS/$id.png -resize 480x \) \( $f -gravity center -crop ${cw}x1080+0+0 +repage -resize 480x \) +append -quality 90 $O/photo_${n}_$tl.jpg
          if [ -f $B ]; then
            bw=$(magick identify -format "%w" $B); bc="-gravity center -crop ${cw}x1080+0+0 +repage"; [ "$bw" = 2340 ] || bc=""
            magick \( $SBS/$id.png -resize 320x \) \( $B $bc -resize 320x \) \( $f -gravity center -crop ${cw}x1080+0+0 +repage -resize 320x \) +append -quality 90 $O/tri_${n}_$tl.jpg
          fi
        fi
        continue ;;
      *) B=$MA/junctions-r6/renders_b7_$tl/$n.png ;;
    esac
    [ -f $B ] && magick \( $B -resize 480x \) \( $f -resize 480x \) +append -quality 88 $O/ba_${n}_$tl.jpg
  done
done
ls $O | wc -l
