#!/usr/bin/env bash
# qa.sh <tag> <Tier> <lighting> : unity slot (max 4 Unity, waits for PHONE_RUN) + GPT_UNITY_HOLD -> visual-qa junction
# cameras -> renders_<tag>_<tier>_<lighting>
set -u
cd "$(dirname "$0")/../../.."
TAG=$1; TIER=$2; LIGHT=$3
L=artifacts/junctions-r5/logs
MAIN=/c/Users/matma/Documents/Claude/kamion
LOCKS=$MAIN/artifacts/locks
while [ -e $LOCKS/PHONE_RUN ] || [ -e $LOCKS/GPT_UNITY_HOLD ]; do sleep 60; done
pwsh $MAIN/scripts/unity-slot.ps1 -Acquire -Owner claude-junctions-r5 > /dev/null
t=$(echo $TIER | tr A-Z a-z)
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $TIER -Lighting $LIGHT -Gate3 Data/Regions/bialystok-industrial-c/junctions_cameras.json -OutputDir artifacts/junctions-r5/renders_${TAG}_${t}_${LIGHT} > $L/${TAG}_qa_${t}_${LIGHT}.log 2>&1; echo "qa $TIER $LIGHT rc $? $(date +%H:%M)"
pwsh $MAIN/scripts/unity-slot.ps1 -Release -Owner claude-junctions-r5 > /dev/null
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset game/Assets/_Project/Rendering/Settings/Lighting/LP_Dusk.asset game/Assets/_Project/Rendering/Settings/Lighting/LP_LowSun.asset 2>/dev/null
