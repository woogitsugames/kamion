#!/usr/bin/env bash
# b5_all.sh: import b5 + 4 render sets + SBS G3-A cameras + PlayMode (route / barrier tests) + post full. Waits while PHONE_RUN exists.
set -u
cd "$(dirname "$0")/../../.."
MAIN=/c/Users/matma/Documents/Claude/kamion
L=artifacts/biezenstwa-island/logs
while [ -e $MAIN/artifacts/locks/PHONE_RUN ]; do sleep 60; done
bash artifacts/biezenstwa-island/scripts/imp.sh b5
while [ -e $MAIN/artifacts/locks/PHONE_RUN ]; do sleep 60; done
bash artifacts/biezenstwa-island/scripts/qa.sh b5sbs Low overcast artifacts/biezenstwa-island/cams_sbs_a.json
pwsh $MAIN/scripts/unity-slot.ps1 -Acquire -Owner claude-biezenstwa-island > /dev/null
pwsh scripts/test.ps1 -Platform PlayMode -Filter "WorldCRouteTests|WorldCBarrierTests" > $L/b5_playmode.log 2>&1; echo "playmode rc $?"
pwsh scripts/test.ps1 -Platform EditMode > $L/b5_editmode.log 2>&1; echo "editmode rc $?"
pwsh $MAIN/scripts/unity-slot.ps1 -Release -Owner claude-biezenstwa-island > /dev/null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>/dev/null
tail -2 $L/b5_playmode.log; tail -1 $L/b5_editmode.log
bash artifacts/biezenstwa-island/scripts/post.sh b5 full
echo "b5_all done $(date +%H:%M)"
