#!/usr/bin/env bash
# plaza-barn-fix-s24: before | after sheets (full frames side by side, plus 1:1 crops) -> sbs/
# usage: bash artifacts/plaza-barn-fix-s24/make_sheets.sh
set -e
cd "$(dirname "$0")"
mkdir -p sbs
pair() {  # region cam
  local b="vqa-before/$1/$2.png" a="vqa-after/$1/$2.png"
  [ -f "$b" ] && [ -f "$a" ] || { echo "skip $1/$2"; return; }
  magick "$b" -resize 1170x "$a" -resize 1170x -append -quality 88 "sbs/$1-$2.jpg"
}
crop() {  # region cam geometry tag
  local b="vqa-before/$1/$2.png" a="vqa-after/$1/$2.png"
  [ -f "$b" ] && [ -f "$a" ] || return 0
  magick \( "$b" -crop "$3" +repage \) \( "$a" -crop "$3" +repage \) +append -quality 90 "sbs/crop-$1-$2-$4.jpg"
}
for c in czarniecki-pedestal-0320b czarniecki-34-0320b czarniecki-figure-0320b plaza-furniture-0320b look-tykocin-plaza-cab-0325 \
         look-tykocin-plaza-photo-0325 look-tykocin-plaza-se look-tykocin-czarniecki look-tykocin-rynek-s look-tykocin-rynek-n top-tykocin-rynek; do
  pair tykocin $c
done
for c in drive-kozince rev-kozince route-s0144 route-s0433 route-s0721 drive-wood top-kozince; do pair dk65-07 $c; done
