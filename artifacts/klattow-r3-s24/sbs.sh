#!/usr/bin/env bash
# render over the owner's photo (local reference only), 960 px wide: bash artifacts/klattow-r3-s24/sbs.sh r1
set -e
T=$1; D=$(dirname "$0"); R=Data/raw/refs/owner-knyszyn-klattow-2026-11-19; mkdir -p $D/sbs
for p in "street:look-dom-klattow-street:01" "lamus:look-lamus-plebanski:02" "gable:look-dom-klattow-gable-e:04" "yard:look-dom-klattow-yard:05" "street3q:look-dom-klattow:01"; do
  IFS=: read n cam ph <<< "$p"
  f=$(ls $D/$T/${cam}.png $D/$T/${cam//-/_}.png 2>/dev/null | head -1)
  [ -n "$f" ] && magick "$f" -resize 960x \( $R/klattow-$ph.webp -resize 960x \) -append -quality 88 $D/sbs/$n-vs-photo$ph-$T.jpg
done
ls $D/sbs
