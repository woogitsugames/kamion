#!/usr/bin/env bash
# before/after stacks of the SBS sheets (photo | render): top = baseline, bottom = after. Usage: make-pairs.sh <after-dir-name>
set -e
cd "$(dirname "$0")"
A=${1:-after}
mkdir -p pairs-$A
for f in $A/sheets/Low-overcast/sbs-g3-*.png; do
  n=$(basename "$f" .png)
  [ -f baseline/sheets/Low-overcast/$n.png ] || continue
  magick baseline/sheets/Low-overcast/$n.png -crop 100%x62%+0+0 +repage \( "$f" -crop 100%x62%+0+0 +repage \) -append -resize 960x pairs-$A/$n.jpg
done
ls pairs-$A | wc -l
