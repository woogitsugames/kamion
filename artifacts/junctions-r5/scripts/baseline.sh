#!/usr/bin/env bash
# baseline.sh <tag>: import the world of MAIN (its Data/raw/derived world + generated manifest + hero asset of main)
# into this worktree's Unity project, render the junction cameras Low clear + High overcast, then restore this
# worktree's world (not re-imported: run imp.sh afterwards). Honest "before" for the ADR 0117 budget.
set -u
cd "$(dirname "$0")/../../.."
TAG=$1
MAIN=/c/Users/matma/Documents/Claude/kamion
R=bialystok-industrial-c
D=Data/raw/derived/$R
L=artifacts/junctions-r5/logs
LOCKS=$MAIN/artifacts/locks
B=artifacts/junctions-r5/_swap; mkdir -p $B
mv $D/world $D/world_cur && cp -r $MAIN/$D/world $D/world || exit 1
cp Data/Regions/$R/generated/world_manifest.json $B/world_manifest.json
cp $MAIN/Data/Regions/$R/generated/world_manifest.json Data/Regions/$R/generated/world_manifest.json
cp Data/Regions/$R/route_start.json $B/route_start.json; cp $MAIN/Data/Regions/$R/route_start.json Data/Regions/$R/route_start.json
for f in art-source/world/landmarks/viaduct_biezenstwa/viaduct_biezenstwa.glb art-source/world/landmarks/viaduct_biezenstwa/viaduct_biezenstwa_meta.json art-source/world/textures/viaduct_steel.png; do
  cp $f $B/$(basename $f); cp $MAIN/$f $f; done
while [ -e $LOCKS/PHONE_RUN ] || [ -e $LOCKS/GPT_UNITY_HOLD ]; do sleep 60; done
pwsh scripts/import-region.ps1 -Region $R > $L/${TAG}_import.log 2>&1; echo "import rc $? $(date +%H:%M)"
bash artifacts/junctions-r5/scripts/qa.sh $TAG Low clear
bash artifacts/junctions-r5/scripts/qa.sh $TAG High overcast
rm -rf $D/world && mv $D/world_cur $D/world
cp $B/world_manifest.json Data/Regions/$R/generated/world_manifest.json; cp $B/route_start.json Data/Regions/$R/route_start.json
for f in art-source/world/landmarks/viaduct_biezenstwa/viaduct_biezenstwa.glb art-source/world/landmarks/viaduct_biezenstwa/viaduct_biezenstwa_meta.json art-source/world/textures/viaduct_steel.png; do cp $B/$(basename $f) $f; done
echo "restored $(date +%H:%M)"; git status --short | head
