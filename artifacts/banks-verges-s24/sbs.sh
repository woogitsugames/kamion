#!/usr/bin/env bash
# Side-by-side sheets: before (r0) | after (<round>), per camera, clear and overcast; reference | game for the bridge.
# usage: bash sbs.sh r1   -> sbs/<round>/*.jpg (<= 1920 px wide)
set -e
R=${1:?round}
A="$(cd "$(dirname "$0")" && pwd)"
MAIN=/c/Users/matma/Documents/Claude/kamion
O="$A/sbs/$R"; mkdir -p "$O"
lab() { magick "$1" -resize 960x -gravity NorthWest -fill white -undercolor '#00000090' -pointsize 20 -annotate +8+6 " $2 " "$3"; }
for t in tykocin dk65-07 knyszyn-w; do
  for l in clear overcast; do
    d0="$A/r0/$t-High-$l"; d1="$A/$R/$t-High-$l"
    [ -d "$d1" ] || continue
    for f in "$d1"/*.png; do
      b=$(basename "${f%.png}")
      case "$b" in *_mask|*_envcube) continue;; esac
      lab "$f" "po ($R) $t $b $l" "$O/_b.png"
      if [ -f "$d0/$b.png" ]; then
        lab "$d0/$b.png" "przed (r0) $t $b $l" "$O/_a.png"
        magick "$O/_a.png" "$O/_b.png" +append -quality 86 "$O/$t-$b-$l.jpg"
      else
        magick "$O/_b.png" -quality 86 "$O/$t-$b-$l-only.jpg"
      fi
    done
  done
done
rm -f "$O/_a.png" "$O/_b.png"
# reference | game (Commons "Tykocin Most drogowy" 03 / 05, Zala, CC BY-SA 4.0 - viewing only, not shipped)
REF="$MAIN/Data/raw/refs/tykocin-bridge-commons"
if [ -f "$A/$R/tykocin-High-clear/bv_bank_se.png" ]; then
  for pr in "03:bv_bank_sw" "05:bv_bank_se" "06:bv_bank_n" "06:bv_bank_close"; do
    n=${pr%%:*}; c=${pr##*:}
    [ -f "$REF/Tykocin_Most_drogowy_$n.jpg" ] || continue
    magick "$REF/Tykocin_Most_drogowy_$n.jpg" -resize x540 -gravity NorthWest -fill white -undercolor '#00000090' -pointsize 18 -annotate +8+6 " ref: Commons Tykocin Most drogowy $n (Zala, CC BY-SA 4.0) " "$O/_r.png"
    magick "$A/$R/tykocin-High-clear/$c.png" -resize x540 -gravity NorthWest -fill white -undercolor '#00000090' -pointsize 18 -annotate +8+6 " gra ($R) $c " "$O/_g.png"
    magick "$O/_r.png" "$O/_g.png" +append -quality 86 "$O/ref-vs-game-bridge-$n-$c.jpg"
  done
  rm -f "$O/_r.png" "$O/_g.png"
fi
ls "$O" | wc -l
