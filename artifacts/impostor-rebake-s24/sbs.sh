#!/usr/bin/env bash
# impostor-rebake-s24: side-by-side before|after pairs (<= 960 px) + changed-pixel share per camera.
# usage: sbs.sh <before-label> <after-label> <out-dir>
set -u
cd "$(dirname "$0")"
B=$1; A=$2; O=$3; mkdir -p "$O"
echo -e "set\tcamera\tchanged_px_fuzz6" > "$O/diff.tsv"
for d in "$A"/*-High-*/; do
  s=$(basename "$d")
  [ -d "$B/$s" ] || continue
  for f in "$d"*.png; do
    c=$(basename "$f" .png)
    [ -f "$B/$s/$c.png" ] || continue
    case "$c" in *-hud|cab-*|lamp-*) continue;; esac
    magick "$B/$s/$c.png" "$f" -resize 480x +append "$O/${s}__${c}.jpg"
    ae=$(magick compare -metric AE -fuzz 6% "$B/$s/$c.png" "$f" null: 2>&1 | sed 's/ .*//')
    echo -e "$s\t$c\t$ae" >> "$O/diff.tsv"
  done
done
