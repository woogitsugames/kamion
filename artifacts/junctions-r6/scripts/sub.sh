#!/usr/bin/env bash
# sub.sh <tag>: Low clear + High overcast of the 11-camera subset (cams_sub.json) under one unity slot - material iteration on the
# generated .mat files without a re-import (values go back to build_world.MATERIALS afterwards)
cd "$(dirname "$0")/../../.."
MAIN=/c/Users/matma/Documents/Claude/kamion
pwsh $MAIN/scripts/unity-slot.ps1 -Acquire -PollSeconds 5 -Owner claude-junctions-r6 > /dev/null
for c in "Low clear" "High overcast" ${EXTRA:+"High clear"}; do HOLD=1 bash artifacts/junctions-r6/scripts/qa.sh $1 $c artifacts/junctions-r6/cams_sub.json; done
pwsh $MAIN/scripts/unity-slot.ps1 -Release -Owner claude-junctions-r6 > /dev/null
bash artifacts/junctions-r6/scripts/lum_set.sh $1
