#!/usr/bin/env bash
# tykocin-plaza-s24: comparison sheets  reference (Commons, local only) | before | after  ->  sbs/<tag>-*.jpg
# usage: bash artifacts/tykocin-plaza-s24/make_sheets.sh <after dir> <tag>
set -e
cd "$(dirname "$0")"
A="$1"; T="$2"; B=vqa-before
R=../../Data/raw/refs/tykocin-rynek-commons
mkdir -p sbs
crop() { magick "$1" -gravity center -crop "$2" +repage -resize x900 "$3"; }
crop $B/czarniecki-figure-0320b.png 760x1080+0+0 sbs/_b.jpg; crop $A/czarniecki-figure-0320b.png 760x1080+0+0 sbs/_a.jpg
magick \( $R/cs35733636.jpg -resize x900 \) sbs/_b.jpg sbs/_a.jpg +append -quality 88 sbs/$T-figure-ref-before-after.jpg
crop $B/czarniecki-34-0320b.png 900x1080+0+0 sbs/_b.jpg; crop $A/czarniecki-34-0320b.png 900x1080+0+0 sbs/_a.jpg
magick \( $R/cs152250560.jpg -resize x900 \) sbs/_b.jpg sbs/_a.jpg +append -quality 88 sbs/$T-monument34-ref-before-after.jpg
crop $B/czarniecki-pedestal-0320b.png 900x1080+0+0 sbs/_b.jpg; crop $A/czarniecki-pedestal-0320b.png 900x1080+0+0 sbs/_a.jpg
magick \( $R/cs152250558.jpg -resize x900 \) sbs/_b.jpg sbs/_a.jpg +append -quality 88 sbs/$T-pedestal-ref-before-after.jpg
for c in look-tykocin-plaza-cab-0325 plaza-furniture-0320b look-tykocin-plaza-se look-tykocin-plaza-photo-0325 look-tykocin-czarniecki; do
  magick \( $B/$c.png -resize 1500x \) \( $A/$c.png -resize 1500x \) -append -quality 88 sbs/$T-$c-before-after.jpg
done
magick \( $R/cs202183366.jpg -resize 1500x \) \( $A/look-tykocin-plaza-photo-0325.png -resize 1500x \) -append -quality 88 sbs/$T-plaza-photo-ref-after.jpg
rm -f sbs/_a.jpg sbs/_b.jpg
ls sbs
