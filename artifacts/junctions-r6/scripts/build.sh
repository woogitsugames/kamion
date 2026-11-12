#!/usr/bin/env bash
# build.sh <tag>: heavy slot -> build_world -> export-route -> QA copies -> plan views -> release (ADR 0123 loop, step 1)
set -u
cd "$(dirname "$0")/../../.."
TAG=$1
L=artifacts/junctions-r6/logs
MAIN=/c/Users/matma/Documents/Claude/kamion
R=bialystok-industrial-c
export KAMION_BLENDER="C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe"
pwsh $MAIN/scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner claude-junctions-r6 > /dev/null
echo "build start $(date +%H:%M)"
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $R > $L/${TAG}_build.log 2>&1; echo "build rc $?"
uv run --project tools/worldgen python scripts/export-route.py --region $R > $L/${TAG}_route.log 2>&1; echo "route rc $?"
for f in roads_qa streetscape_qa terrain_walls_qa road_consistency_qa; do cp Data/Regions/$R/generated/$f.json $L/${TAG}_$f.json; done
cp Data/Regions/$R/generated/world_manifest.json $L/${TAG}_world_manifest.json
echo "world ready $(date +%H:%M)"
[ "${PLAN:-1}" = 1 ] && bash artifacts/junctions-r6/scripts/plan.sh $TAG
pwsh $MAIN/scripts/unity-slot.ps1 -Release -Pool heavy -Owner claude-junctions-r6 > /dev/null
echo "build done $(date +%H:%M)"
