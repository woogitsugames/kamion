#!/usr/bin/env bash
# Pairs <= 960 px wide: render | reference frame, and base | final. Run from the worktree root:
#   bash artifacts/buildings-r16/pairs.sh <final round>
# Reference frames (Mapillary CC BY-SA 4.0, Commons) are looked at only; the pairs stay in artifacts/ (not in git, not in a build).
set -e
R=${1:-r5}
A=artifacts/buildings-r16
M=Data/raw/mapillary/posesje
C=Data/raw/refs/posesje
O=$A/pairs
mkdir -p $O
pair() {   # out left right
  magick \( "$2" -resize 476x300^ -gravity center -extent 476x300 \) \( "$3" -resize 476x300^ -gravity center -extent 476x300 \) +append -bordercolor black -border 2 "$O/$1.jpg"
}
ref() {    # style camera reference-file label
  pair "ref_$1" "$A/$R/extra/$2.png" "$3"
}
ref picket_C04 r15_front_picket "$C/cmFile_Drewniany_dom_z_gankiem_za_czerwon_furtk_w_Supra_lu.jpg.jpg"
ref boards_P09 r15_front_boards_brown "$M/269756941543675.jpg"
ref chainlink_P10 r15_front_chainlink "$M/4073869122651585.jpg"
ref brick_picket_C01 r15_front_brick_picket "$C/cmFile_8782_October_2022_in_Podlaskie_Voivodeship.jpg.jpg"
ref brick_bars_P24 r15_front_brick_bars "$M/376100606965433.jpg"
ref bars_P06 r15_front_bars "$M/1566871480311497.jpg"
ref wall_P14 r15_front_wall "$M/1185672959149756.jpg"
ref lamella_P13 r15_front_lamella "$M/1160266725277203.jpg"
ref concrete_P10 r15_front_concrete "$M/4073869122651585.jpg"
ref cab0_P08 r15_cab_0 "$M/1889914111167007.jpg"
for c in r14_plot2_eye_az250 r14_plot2_eye_az160 r14_plot2_eye_az70 r14_plots_aerial_low r13_houses_aerial r13_house1_az200 r13_block3_close; do
  pair "base_${c}" "$A/base/extra/$c.png" "$A/$R/extra/$c.png"
done
for c in r10_house_1 r10_house_2 r10_shed_2 r10_fence_2 r10_block_3; do
  pair "base_low_${c}" "$A/base/Low-overcast/$c.png" "$A/$R/Low-overcast/$c.png"
done
ls $O | wc -l
