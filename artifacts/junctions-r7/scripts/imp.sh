#!/usr/bin/env bash
# imp.sh <tag> [combos...] : touch PBR PNGs unless REBUILD_SETS=1 -> ONE unity slot for import-region + all renders (default: Low
# clear, High overcast, Low overcast, High clear) of the junction cameras -> release. NOIMPORT=1 skips the import.
set -u
cd "$(dirname "$0")/../../.."
TAG=$1; shift
L=artifacts/junctions-r7/logs
MAIN=/c/Users/matma/Documents/Claude/kamion
[ "${REBUILD_SETS:-0}" = 1 ] || find art-source/world/materials -name "*.png" -not -path "*/_src/*" -exec touch {} +
while [ -e $MAIN/artifacts/locks/PHONE_RUN ]; do sleep 60; done
pwsh $MAIN/scripts/unity-slot.ps1 -Acquire -PollSeconds 5 -Owner claude-junctions-r7 > /dev/null
echo "slot $(date +%H:%M)"
if [ "${NOIMPORT:-0}" != 1 ]; then
  pwsh scripts/import-region.ps1 -Region bialystok-industrial-c > $L/${TAG}_import.log 2>&1; echo "import rc $? $(date +%H:%M)"
  git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>/dev/null
fi
[ $# -eq 0 ] && set -- "Low clear" "Low overcast"
for c in "$@"; do HOLD=1 bash artifacts/junctions-r7/scripts/qa.sh $TAG $c ${CAMS:-}; done
pwsh $MAIN/scripts/unity-slot.ps1 -Release -Owner claude-junctions-r7 > /dev/null
echo "imp done $(date +%H:%M)"
