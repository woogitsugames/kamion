#!/usr/bin/env bash
# wait for phone / GPT locks -> import-region -> visual-qa High overcast (junction cameras) + Low clear ; ADR 0110
set -u
cd "$(dirname "$0")/../../.."
TAG=${1:-b}
L=artifacts/junctions-r4/logs
LOCKS=/c/Users/matma/Documents/Claude/kamion/artifacts/locks
waitlock() { while [ -e $LOCKS/PHONE_RUN ] || [ -e $LOCKS/GPT_UNITY_HOLD ]; do sleep 60; done; }
R=bialystok-industrial-c
CAMS=Data/Regions/$R/junctions_cameras.json
waitlock; echo "import start $(date +%H:%M)"
pwsh scripts/import-region.ps1 -Region $R > $L/${TAG}_import.log 2>&1; echo "import rc $?"
waitlock
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting overcast -Gate3 $CAMS -OutputDir artifacts/junctions-r4/renders_${TAG}_high > $L/${TAG}_qa_high.log 2>&1; echo "qa high rc $?"
if [ "${2:-}" = "low" ]; then
waitlock
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -Gate3 $CAMS -OutputDir artifacts/junctions-r4/renders_${TAG}_low > $L/${TAG}_qa_low.log 2>&1; echo "qa low rc $?"
fi
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset game/Assets/_Project/Rendering/Settings/Lighting/LP_Dusk.asset game/Assets/_Project/Rendering/Settings/Lighting/LP_LowSun.asset 2>/dev/null
echo "done $(date +%H:%M)"
