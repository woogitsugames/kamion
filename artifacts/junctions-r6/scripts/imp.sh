#!/usr/bin/env bash
# imp.sh <tag> [combos...] : touch PBR PNGs unless REBUILD_SETS=1 -> unity slot -> import-region -> renders (default: Low clear,
# High overcast, Low overcast, High clear) of the junction cameras
set -u
cd "$(dirname "$0")/../../.."
TAG=$1; shift
L=artifacts/junctions-r6/logs
MAIN=/c/Users/matma/Documents/Claude/kamion
[ "${REBUILD_SETS:-0}" = 1 ] || find art-source/world/materials -name "*.png" -not -path "*/_src/*" -exec touch {} +
echo "import start $(date +%H:%M)"
pwsh $MAIN/scripts/unity-slot.ps1 -Acquire -Owner claude-junctions-r6 > /dev/null
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c > $L/${TAG}_import.log 2>&1; echo "import rc $? $(date +%H:%M)"
pwsh $MAIN/scripts/unity-slot.ps1 -Release -Owner claude-junctions-r6 > /dev/null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>/dev/null
[ $# -eq 0 ] && set -- "Low clear" "High overcast" "Low overcast" "High clear"
for c in "$@"; do bash artifacts/junctions-r6/scripts/qa.sh $TAG $c; done
echo "imp done $(date +%H:%M)"
