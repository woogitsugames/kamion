#!/usr/bin/env bash
# usage: bash artifacts/hospgate-0189/sbs.sh <render dir> [camera id]  -> artifacts/hospgate-0189/sbs/sbs-P11-129-<tag>.jpg
set -e
cd "$(dirname "$0")/../.."
dir="$1"; cam="${2:-photo_P11-129c}"; tag="$(basename "$dir")"
mkdir -p artifacts/hospgate-0189/sbs
photo=research/_incoming/mistral-p11-dojlidy-photos-v2/files/P11-129.jpg
magick "$photo" -resize 960x -gravity center -crop 960x540+0+0 +repage /tmp/_p.png
magick "$dir/$cam.png" -resize 960x540! /tmp/_r.png
magick /tmp/_p.png /tmp/_r.png +append -quality 90 "artifacts/hospgate-0189/sbs/sbs-P11-129-$tag.jpg"
magick "$dir/$cam.png" -resize 960x -quality 90 "artifacts/hospgate-0189/sbs/render-$tag.jpg"
echo "artifacts/hospgate-0189/sbs/sbs-P11-129-$tag.jpg"
