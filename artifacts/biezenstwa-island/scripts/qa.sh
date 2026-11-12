#!/usr/bin/env bash
# qa.sh <tag> <Tier> <lighting> [cameras.json] : unity slot (unless HOLD=1: the caller holds it) -> visual-qa junction cameras
# -> renders_<tag>_<tier>_<lighting>
set -u
cd "$(dirname "$0")/../../.."
TAG=$1; TIER=$2; LIGHT=$3
CAMS=${4:-Data/Regions/bialystok-industrial-c/junctions_cameras.json}
L=artifacts/biezenstwa-island/logs
MAIN=/c/Users/matma/Documents/Claude/kamion
[ "${HOLD:-0}" = 1 ] || pwsh $MAIN/scripts/unity-slot.ps1 -Acquire -PollSeconds 5 -Owner claude-biezenstwa-island > /dev/null
t=$(echo $TIER | tr A-Z a-z)
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $TIER -Lighting $LIGHT -Gate3 $CAMS -OutputDir artifacts/biezenstwa-island/renders_${TAG}_${t}_${LIGHT} > $L/${TAG}_qa_${t}_${LIGHT}.log 2>&1; echo "qa $TIER $LIGHT rc $? $(date +%H:%M)"
[ "${HOLD:-0}" = 1 ] || pwsh $MAIN/scripts/unity-slot.ps1 -Release -Owner claude-biezenstwa-island > /dev/null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>/dev/null
