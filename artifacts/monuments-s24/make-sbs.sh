#!/usr/bin/env bash
# monuments-s24: side-by-side sheets (left = reference photo, right = game render). Usage: make-sbs.sh <round, e.g. r2>
set -e
cd "$(dirname "$0")"
R=$1; K=$R-knyszyn; T=$R-tykocin; mkdir -p sbs
pair() { magick \( "$1" -resize x${4:-720} \) \( "$2" -resize x${4:-720} \) +append "$3" 2>/dev/null; }
if [ -d $K ]; then
  magick $K/king-front-0325.png -gravity center -crop 760x1000+0-20 +repage sbs/_a.png
  magick $K/king-34-0325.png -gravity center -crop 760x1000+0-20 +repage sbs/_b.png
  magick $K/king-head-0325.png -gravity center -crop 1000x1000+0+0 +repage sbs/_c.png
  magick $K/king-side-0325.png -gravity center -crop 620x1000+0-20 +repage sbs/_d.png
  pair refs/king-front.jpg sbs/_a.png sbs/_1.jpg; pair refs/king-34.jpg sbs/_b.png sbs/_2.jpg
  pair refs/king-head.jpg sbs/_c.png sbs/_3.jpg; pair refs/king-side-owner1.jpg sbs/_d.png sbs/_4.jpg
  magick sbs/_1.jpg sbs/_2.jpg +append -resize 1900x sbs/_r1.jpg; magick sbs/_3.jpg sbs/_4.jpg +append -resize 1900x sbs/_r2.jpg
  magick \( refs/king-owner8.jpg -resize 950x \) \( $K/king-square-0325.png -resize 950x \) +append -resize 1900x sbs/_r3.jpg
  magick sbs/_r1.jpg sbs/_r2.jpg sbs/_r3.jpg -append sbs/$R-king-sheet.jpg
  rm -f sbs/_*.jpg sbs/_*.png
fi
if [ -d $T ]; then
  magick refs/plaza-photo.jpg -gravity south -crop 100%x62%+0+0 +repage -resize 950x sbs/_p1.jpg
  magick $T/look-tykocin-plaza-photo-0325.png -resize 950x sbs/_p2.jpg
  magick refs/plaza-ortho.jpg -resize 950x sbs/_p3.jpg
  magick $T/top-tykocin-rynek.png -crop 760x700+760+280 +repage -resize 950x sbs/_p4.jpg
  magick $T/look-tykocin-plaza-setts-0325.png -resize 950x sbs/_p5.jpg
  magick $T/look-tykocin-plaza-cab-0325.png -resize 950x sbs/_p6.jpg
  magick \( sbs/_p1.jpg sbs/_p2.jpg +append \) \( sbs/_p3.jpg sbs/_p4.jpg +append \) \( sbs/_p5.jpg sbs/_p6.jpg +append \) -append sbs/$R-plaza-sheet.jpg
  rm -f sbs/_p*.jpg
fi
ls sbs
