#!/usr/bin/env bash
# chain.sh <tag>: build.sh -> (rc 0) imp.sh with cams_r7.json (import + Low clear + Low overcast) -> pairs
cd "$(dirname "$0")/../../.."
T=$1; A=artifacts/junctions-r7
bash $A/scripts/build.sh $T > $A/logs/${T}_build.out 2>&1
grep -q "build rc 0" $A/logs/${T}_build.out || { echo "BUILD FAILED" >> $A/logs/${T}_build.out; exit 1; }
CAMS=$A/cams_r7.json bash $A/scripts/imp.sh $T > $A/logs/${T}_imp.out 2>&1
bash $A/scripts/pairs.sh $T >> $A/logs/${T}_imp.out 2>&1
echo "chain done $(date +%H:%M)" >> $A/logs/${T}_imp.out
