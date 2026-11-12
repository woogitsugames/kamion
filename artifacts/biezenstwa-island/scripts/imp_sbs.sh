#!/usr/bin/env bash
# imp_sbs.sh <tag>: ONE unity slot -> import-region -> SBS photo-pose cameras Low overcast + Low clear (-> renders_<tag>sbs_*) -> release
set -u
cd "$(dirname "$0")/../../.."
TAG=$1; shift
L=artifacts/biezenstwa-island/logs
MAIN=/c/Users/matma/Documents/Claude/kamion
[ "${REBUILD_SETS:-0}" = 1 ] || find art-source/world/materials -name "*.png" -not -path "*/_src/*" -exec touch {} +
while [ -e $MAIN/artifacts/locks/PHONE_RUN ]; do sleep 60; done
pwsh $MAIN/scripts/unity-slot.ps1 -Acquire -PollSeconds 5 -Owner claude-biezenstwa-island > /dev/null
echo "slot $(date +%H:%M)"
if [ "${NOIMPORT:-0}" != 1 ]; then
  pwsh scripts/import-region.ps1 -Region bialystok-industrial-c > $L/${TAG}_import.log 2>&1; echo "import rc $? $(date +%H:%M)"
  git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>/dev/null
fi
[ $# -eq 0 ] && set -- "Low overcast" "Low clear"
for c in "$@"; do HOLD=1 bash artifacts/biezenstwa-island/scripts/qa.sh ${TAG}sbs $c artifacts/biezenstwa-island/cams_sbs.json; done
pwsh $MAIN/scripts/unity-slot.ps1 -Release -Owner claude-biezenstwa-island > /dev/null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>/dev/null
echo "imp_sbs done $(date +%H:%M)"
