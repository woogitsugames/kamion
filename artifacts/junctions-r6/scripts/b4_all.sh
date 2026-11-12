#!/usr/bin/env bash
# b4_all.sh: import b4 + 4 render sets + SBS G3-A cameras + PlayMode (route / barrier tests) + post full. Waits while PHONE_RUN exists.
set -u
cd "$(dirname "$0")/../../.."
MAIN=/c/Users/matma/Documents/Claude/kamion
L=artifacts/junctions-r6/logs
while [ -e $MAIN/artifacts/locks/PHONE_RUN ]; do sleep 60; done
bash artifacts/junctions-r6/scripts/imp.sh b4
while [ -e $MAIN/artifacts/locks/PHONE_RUN ]; do sleep 60; done
bash artifacts/junctions-r6/scripts/qa.sh b4sbs Low overcast artifacts/junctions-r6/cams_sbs_a.json
pwsh $MAIN/scripts/unity-slot.ps1 -Acquire -Owner claude-junctions-r6 > /dev/null
pwsh scripts/test.ps1 -Platform PlayMode -Filter "WorldCRouteTests|WorldCBarrierTests" > $L/b4_playmode.log 2>&1; echo "playmode rc $?"
pwsh scripts/test.ps1 -Platform EditMode > $L/b4_editmode.log 2>&1; echo "editmode rc $?"
pwsh $MAIN/scripts/unity-slot.ps1 -Release -Owner claude-junctions-r6 > /dev/null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>/dev/null
tail -2 $L/b4_playmode.log; tail -1 $L/b4_editmode.log
bash artifacts/junctions-r6/scripts/post.sh b4 full
echo "b4_all done $(date +%H:%M)"
