#!/usr/bin/env bash
# r4 pairs <= 960 px: base2 (content of main built here) | r4, and r4 | reference frame. Run from the worktree root:
#   bash artifacts/buildings-r9/pairs_r4.sh
# Reference frames (Mapillary CC BY-SA 4.0, Commons) are looked at only; the pairs stay in artifacts/.
set -e
A=artifacts/buildings-r9
M=Data/raw/mapillary/posesje
C=Data/raw/refs/posesje
O=$A/pairs_r4
mkdir -p $O
pair() {   # out left right
  magick \( "$2" -resize 476x300^ -gravity center -extent 476x300 \) \( "$3" -resize 476x300^ -gravity center -extent 476x300 \) +append -bordercolor black -border 2 "$O/$1.jpg"
}
for c in r15_front_brick_bars r16_drive_0 r16_drive_3 r16_garden_2 r17_over_0 r17_street_0a r17_street_1a r17_street_3a; do
  pair "base_hc_$c" "$A/base2/extra_hc/$c.png" "$A/r4/extra_hc/$c.png"
done
for c in r15_front_brick_bars r16_drive_0 r16_drive_3 r16_garden_2 r17_over_0 r17_street_0a r17_street_1a r17_street_3a r16_cab_1 r16_garden_0 r14_plots_aerial_low r15_front_picket; do
  pair "base_low_$c" "$A/base2/extra_low/$c.png" "$A/r4/extra_low/$c.png"
done
for c in cab-driver r10_fence_1 r10_fence_3 r10_house_1 r10_house_2 r10_shed_2; do
  pair "low_$c" "$A/base2/Low-overcast/$c.png" "$A/r4/Low-overcast/$c.png"
done
pair ref_brick_bars_P24 "$A/r4/extra_hc/r15_front_brick_bars.png" "$M/376100606965433.jpg"
pair ref_street1_P08 "$A/r4/extra_hc/r17_street_1a.png" "$M/1889914111167007.jpg"
pair ref_street0_P09 "$A/r4/extra_hc/r17_street_0a.png" "$M/269756941543675.jpg"
pair ref_street3_P14 "$A/r4/extra_hc/r17_street_3a.png" "$M/1185672959149756.jpg"
pair ref_picket_C04 "$A/r4/extra_low/r15_front_picket.png" "$C/cmFile_Drewniany_dom_z_gankiem_za_czerwon_furtk_w_Supra_lu.jpg.jpg"
pair ref_cab0_P08 "$A/r4/extra_low/r15_cab_0.png" "$M/1889914111167007.jpg"
magick montage $O/base_hc_*.jpg -geometry 960x+2+2 -tile 1x -label '%t' -pointsize 13 $O/sheet_base_hc.jpg
magick montage $O/base_low_*.jpg -geometry 960x+2+2 -tile 1x -label '%t' -pointsize 13 $O/sheet_base_low.jpg
magick montage $O/low_*.jpg -geometry 960x+2+2 -tile 1x -label '%t' -pointsize 13 $O/sheet_low.jpg
magick montage $O/ref_*.jpg -geometry 960x+2+2 -tile 1x -label '%t' -pointsize 13 $O/sheet_ref.jpg
ls $O | wc -l
