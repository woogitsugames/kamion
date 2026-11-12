#!/usr/bin/env bash
# pairs.sh <tag>: pairs_<tag>/photo_<cam>_<tier>.jpg = Mapillary photo | render (same pose, 480 px each, <= 960 px),
# pairs_<tag>/ba_<cam>.jpg = main (m0) | <tag>, Low clear. ADR 0117 (REVIEW 0110: photo | render, not render | render).
set -u
cd "$(dirname "$0")/.."
T=$1; O=pairs_$T; mkdir -p $O
SBS=/c/Users/matma/Documents/Claude/kamion/artifacts/sbs-gate3/rectified
for pair in "454716650857984:r4_deck_bz_eye" "2948595898752384:r4_deck_bz_eye2" "500263111404933:r4_link_bz_a" "1259231227807789:r4_link_bz_b" "177786140912399:r4_pier_bz"; do
  id=${pair%%:*}; cam=${pair##*:}
  for tl in low_clear high_overcast; do
    [ -f renders_${T}_$tl/$cam.png ] || continue
    magick \( $SBS/$id.png -resize 480x360! \) \( renders_${T}_$tl/$cam.png -gravity center -crop 1440x1080+0+0 +repage -resize 480x360! \) +append -quality 88 $O/photo_${cam}_$tl.jpg
  done
done
for n in p0_kerb_merge_eye p0_lamp_putry_eye r2_fork_link_eye r2_kerb_merge_main_eye r4_putry_nose_eye eye_putry_n r3_e_split_eye p0_lamp_w1101181473_eye stretch-04 stretch-01 g3b-eye-s1482 r4_deck_bz_eye r4_link_bz_a r4_pier_bz; do
  [ -f renders_m0_low_clear/$n.png ] && [ -f renders_${T}_low_clear/$n.png ] || continue
  magick \( renders_m0_low_clear/$n.png -resize 480x \) \( renders_${T}_low_clear/$n.png -resize 480x \) +append -quality 88 $O/ba_$n.jpg
done
ls $O | wc -l
