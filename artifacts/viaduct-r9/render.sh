#!/usr/bin/env bash
# usage: render.sh <outname> [tiers] [lightings]   -> artifacts/viaduct-r9/<outname>/<Tier>-<lighting>/*.png + small/*.jpg
cd "$(dirname "$0")/../.."
OUT=${1:-after}; TIERS=${2:-"High Low"}; LIGHTS=${3:-"overcast lowsun"}
CAMS=stretch_04,photo_biezenstwa_ground,g3a_rondo_bie_approach,g3a_eye_s0362,g3a_eye_s0312,biezenstwa_above
for t in $TIERS; do for l in $LIGHTS; do
  while [ -e ../../../artifacts/locks/PHONE_RUN ]; do sleep 60; done
  d=artifacts/viaduct-r9/$OUT/$t-$l
  pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $t -Lighting $l -Gate3 Data/Regions/bialystok-industrial-c/gate3_cameras.json -Cameras $CAMS -OutputDir $d > artifacts/viaduct-r9/logs/vqa_${OUT}_${t}_${l}.log 2>&1
  echo "$t $l exit $?"
  mkdir -p $d/small; for f in $d/*.png; do magick "$f" -resize 960x "$d/small/$(basename "${f%.png}").jpg" 2>/dev/null; done
done; done
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>/dev/null
[ -d game/Assets/Resources ] && [ -z "$(ls -A game/Assets/Resources)" ] && rm -rf game/Assets/Resources game/Assets/Resources.meta
echo RENDER_DONE
