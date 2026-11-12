#!/usr/bin/env bash
# sbs.sh <tag> [combos...]: ONE unity slot -> SBS photo-pose cameras (main sbs_cameras.json copy) Low overcast + Low clear -> release
set -u
cd "$(dirname "$0")/../../.."
TAG=$1; shift
MAIN=/c/Users/matma/Documents/Claude/kamion
while [ -e $MAIN/artifacts/locks/PHONE_RUN ]; do sleep 60; done
pwsh $MAIN/scripts/unity-slot.ps1 -Acquire -PollSeconds 5 -Owner claude-biezenstwa-island > /dev/null
echo "slot $(date +%H:%M)"
[ $# -eq 0 ] && set -- "Low overcast" "Low clear"
for c in "$@"; do HOLD=1 bash artifacts/biezenstwa-island/scripts/qa.sh ${TAG}sbs $c artifacts/biezenstwa-island/cams_sbs.json; done
pwsh $MAIN/scripts/unity-slot.ps1 -Release -Owner claude-biezenstwa-island > /dev/null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>/dev/null
echo "sbs done $(date +%H:%M)"
