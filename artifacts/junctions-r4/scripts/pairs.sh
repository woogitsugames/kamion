#!/usr/bin/env bash
# pairs.sh <before tag> <after tag>: before | after sheets (<= 960 px wide each half -> 1920 total, stacked labels) in pairs_<after>/
set -u
cd "$(dirname "$0")/.."
A=$1; B=$2; O=pairs_$B; mkdir -p $O
for n in eye_putry_n p0_median_slot_eye r2_n100_eye r2_fork_link_eye p0_kerb_merge_eye p0_lamp_w1101181473_eye r2_kerb_merge_main_eye r3_e_split_eye r3_e_split_top r3_bay_w_top r3_n100_se_eye p0_n10015785253_top p0_fork_putry_eye g3a-eye-s0262 g3b-eye-s1482 stretch-02 top_putry_n top_merge; do
  [ -f renders_${A}_high/$n.png ] && [ -f renders_${B}_high/$n.png ] || continue
  magick \( renders_${A}_high/$n.png -resize 480x \) \( renders_${B}_high/$n.png -resize 480x \) +append -quality 88 $O/$n.jpg
done
SBS=/c/Users/matma/Documents/Claude/kamion/artifacts/sbs-gate3
for pair in "454716650857984:r4_deck_bz_eye" "2948595898752384:r4_deck_bz_eye2" "500263111404933:r4_link_bz_a" "1259231227807789:r4_link_bz_b" "177786140912399:r4_pier_bz"; do
  id=${pair%%:*}; cam=${pair##*:}
  ref=$(ls $SBS/rectified/*$id* 2>/dev/null | head -1); [ -z "$ref" ] && ref=$(ls $SBS/ref-$id.jpg 2>/dev/null | head -1)
  r0=$SBS/r0/renders/High-overcast/sbs-g3-a-$id.png
  [ -f renders_${B}_high/$cam.png ] || continue
  if [ -f "$r0" ]; then magick \( $r0 -resize 480x \) \( renders_${B}_high/$cam.png -resize 480x \) +append -quality 88 $O/$cam.jpg; fi
done
ls $O | wc -l
