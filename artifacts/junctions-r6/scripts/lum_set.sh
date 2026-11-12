#!/usr/bin/env bash
# lum_set.sh <tag>: luminance ratios of asphalt / W-beam / cap / grass in the photo frames (fixed rectangles, 1440x1080 crop) for
# Low clear and High overcast (+ Low overcast, High clear when rendered) -> stdout. Rectangles chosen on renders_m0 (ADR 0123).
cd "$(dirname "$0")/.."
T=$1
for tl in low_clear high_overcast low_overcast high_clear; do
  d=renders_${T}_$tl; [ -f $d/r4_deck_bz_eye.png ] || continue
  python scripts/lum.py $d/r4_deck_bz_eye.png --crop1440 --out _lum_${T}_${tl}_eye.jpg asphalt=700,900,900,1000 beamR=1330,905,1435,930 capR=1225,935,1295,968 kerbR=1175,985,1235,1005 beamL=100,790,400,808 capL=120,880,330,900 sky=600,200,900,300
  python scripts/lum.py $d/r4_deck_bz_eye2.png --crop1440 --out _lum_${T}_${tl}_eye2.jpg asphalt=500,880,720,960 beamR=1320,800,1435,826 capR=1330,885,1390,905 kerbR=1300,908,1380,930 beamL=40,742,300,768 capL=60,905,300,960 sky=560,100,720,200
  python scripts/lum.py $d/r4_link_bz_a.png --crop1440 --out _lum_${T}_${tl}_la.jpg beam=500,948,900,985 grass=300,860,800,900 asphalt=1250,1000,1400,1050
  python scripts/lum.py $d/r4_link_bz_b.png --crop1440 beam=500,948,900,985 grass=300,860,800,900
done
