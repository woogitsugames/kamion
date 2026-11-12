#!/usr/bin/env bash
# all.sh <tag>: ONE heavy slot: build_world + route + plan -> (import + SBS started in the unity pool in parallel) -> fidelity,
# swept path, pytest gis+physics+gate3 -> release; then wait for the import chain, EditMode, pairs.
set -u
cd "$(dirname "$0")/../../.."
TAG=$1
A=artifacts/biezenstwa-island; L=$A/logs
MAIN=/c/Users/matma/Documents/Claude/kamion
R=bialystok-industrial-c
export KAMION_BLENDER="C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe"
pwsh $MAIN/scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner claude-biezenstwa-island > /dev/null
echo "build start $(date +%H:%M)"
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $R > $L/${TAG}_build.log 2>&1; rc=$?; echo "build rc $rc"
uv run --project tools/worldgen python scripts/export-route.py --region $R > $L/${TAG}_route.log 2>&1; echo "route rc $?"
for f in roads_qa streetscape_qa terrain_walls_qa road_consistency_qa world_manifest; do cp Data/Regions/$R/generated/$f.json $L/${TAG}_$f.json; done
bash $A/scripts/plan.sh $TAG
echo "world ready $(date +%H:%M)"
if [ $rc = 0 ]; then
  ( bash $A/scripts/imp_sbs.sh $TAG > $L/${TAG}_imp.out 2>&1
    pwsh $MAIN/scripts/unity-slot.ps1 -Acquire -PollSeconds 5 -Owner claude-biezenstwa-island > /dev/null
    pwsh scripts/test.ps1 -Platform EditMode > $L/${TAG}_editmode.log 2>&1; echo "editmode rc $?" >> $L/${TAG}_imp.out
    pwsh $MAIN/scripts/unity-slot.ps1 -Release -Owner claude-biezenstwa-island > /dev/null
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>/dev/null
    echo "unity chain done $(date +%H:%M)" >> $L/${TAG}_imp.out ) &
  uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region $R > $L/${TAG}_fidelity.log 2>&1; echo "fidelity rc $?"
  uv run --project tools/worldgen python tools/worldgen/fidelity/summary.py $R > $L/${TAG}_fidelity_summary.txt 2>&1; head -2 $L/${TAG}_fidelity_summary.txt
  uv run --project tools/worldgen python tests/physics/swept_path_gate3.py --out $A/swept_${TAG} > $L/${TAG}_swept.log 2>&1; echo "swept rc $?"
  uv run --project tools/worldgen python $A/scripts/swept_sum.py $A/swept_${TAG}
  uv run --project tools/worldgen python -m pytest tests/gis tests/physics tests/gate3 -q -p no:cacheprovider > $L/${TAG}_pytest.log 2>&1; echo "pytest rc $?"
  tail -4 $L/${TAG}_pytest.log
fi
pwsh $MAIN/scripts/unity-slot.ps1 -Release -Pool heavy -Owner claude-biezenstwa-island > /dev/null
echo "heavy done $(date +%H:%M)"
wait
cat $L/${TAG}_imp.out
bash $A/scripts/pairs.sh $TAG b5
echo "all done $(date +%H:%M)"
