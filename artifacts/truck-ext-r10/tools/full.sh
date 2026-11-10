#!/bin/bash
# r10 loop from the worktree root: exterior + trailer export (in place, parallel) -> validators -> Unity build -> frames.
# usage: bash artifacts/truck-ext-r10/tools/full.sh <tag> [tiers] [lights]
B="/c/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe"
T=$1; TI=${2:-High,Low}; LI=${3:-overcast,clear}
R=artifacts/truck-ext-r10
mkdir -p $R/logs
"$B" -b --factory-startup --python-exit-code 1 --python tools/blender/truck/exterior/a6_export.py -- --no-renders > $R/logs/ext-export-$T.log 2>&1 &
P1=$!
"$B" -b --factory-startup --python-exit-code 1 --python tools/blender/truck/trailer/trailer_export.py -- --no-renders > $R/logs/trl-export-$T.log 2>&1 &
P2=$!
wait $P1; echo "ext export exit $?"
wait $P2; echo "trl export exit $?"
grep -a "^LOD[0-9]: \|done in\|Traceback\|Error" $R/logs/ext-export-$T.log | cut -c1-70
grep -a "^LOD[0-9]: \|done in\|Traceback\|Error" $R/logs/trl-export-$T.log | cut -c1-70
"$B" -b --factory-startup --python-exit-code 1 --python tools/blender/truck/exterior/check_export.py > $R/logs/ext-check-$T.log 2>&1; echo "ext check exit $?"; tail -3 $R/logs/ext-check-$T.log | cut -c1-200
"$B" -b --factory-startup --python-exit-code 1 --python tools/blender/truck/trailer/check_export.py > $R/logs/trl-check-$T.log 2>&1; echo "trl check exit $?"; tail -3 $R/logs/trl-check-$T.log | cut -c1-200
pwsh -NoProfile -File $R/tools/unity.ps1 -Step build 2>&1 | grep "exit"
pwsh -NoProfile -File $R/tools/unity.ps1 -Step render -Out $T -Tiers $TI -Lights $LI -Cameras 'truck-34,truck-front,trailer-34,chase,truck-side,truck-rear34,trailer-side,truck-34r' 2>&1 | grep "exit"
echo "full $T done"
