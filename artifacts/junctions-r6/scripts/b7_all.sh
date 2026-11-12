#!/usr/bin/env bash
# b7_all.sh: import b7 + 4 render sets + SBS G3-A cameras + PlayMode (route / barrier tests) + post full. Waits while PHONE_RUN exists.
set -u
cd "$(dirname "$0")/../../.."
MAIN=/c/Users/matma/Documents/Claude/kamion
L=artifacts/junctions-r6/logs
while [ -e $MAIN/artifacts/locks/PHONE_RUN ]; do sleep 60; done
bash artifacts/junctions-r6/scripts/imp.sh b7
while [ -e $MAIN/artifacts/locks/PHONE_RUN ]; do sleep 60; done
bash artifacts/junctions-r6/scripts/qa.sh b7sbs Low overcast artifacts/junctions-r6/cams_sbs_a.json
pwsh $MAIN/scripts/unity-slot.ps1 -Acquire -Owner claude-junctions-r6 > /dev/null
pwsh scripts/test.ps1 -Platform PlayMode -Filter "WorldCRouteTests|WorldCBarrierTests" > $L/b7_playmode.log 2>&1; echo "playmode rc $?"
pwsh scripts/test.ps1 -Platform EditMode > $L/b7_editmode.log 2>&1; echo "editmode rc $?"
pwsh $MAIN/scripts/unity-slot.ps1 -Release -Owner claude-junctions-r6 > /dev/null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>/dev/null
tail -2 $L/b7_playmode.log; tail -1 $L/b7_editmode.log
bash artifacts/junctions-r6/scripts/post.sh b7 full
echo "b7_all done $(date +%H:%M)"
