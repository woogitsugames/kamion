#!/usr/bin/env bash
# final iteration: cycle.sh <tag> low (build, Unity import + renders, loop) then EditMode + PlayMode (locks respected)
set -u
cd "$(dirname "$0")/../../.."
TAG=$1
L=artifacts/junctions-r4/logs
LOCKS=/c/Users/matma/Documents/Claude/kamion/artifacts/locks
waitlock() { while [ -e $LOCKS/PHONE_RUN ] || [ -e $LOCKS/GPT_UNITY_HOLD ]; do sleep 60; done; }
bash artifacts/junctions-r4/scripts/cycle.sh $TAG low
waitlock; echo "editmode start $(date +%H:%M)" >> $L/${TAG}_unity.out
pwsh scripts/test.ps1 -Platform EditMode > $L/${TAG}_editmode.log 2>&1; echo "editmode rc $?" >> $L/${TAG}_unity.out
waitlock; echo "playmode start $(date +%H:%M)" >> $L/${TAG}_unity.out
pwsh scripts/test.ps1 -Platform PlayMode -Filter "WorldCRouteTests|WorldCBarrierTests" > $L/${TAG}_playmode.log 2>&1; echo "playmode rc $?" >> $L/${TAG}_unity.out
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset game/Assets/_Project/Rendering/Settings/Lighting/LP_Dusk.asset game/Assets/_Project/Rendering/Settings/Lighting/LP_LowSun.asset 2>/dev/null
echo "final done $(date +%H:%M)" >> $L/${TAG}_unity.out
