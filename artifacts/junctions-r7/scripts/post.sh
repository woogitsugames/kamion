#!/usr/bin/env bash
# post.sh <tag> [full]: heavy slot -> fidelity -> swept path -> pytest (key files; `full` = tests/gis tests/physics tests/gate3) -> release
set -u
cd "$(dirname "$0")/../../.."
TAG=$1
L=artifacts/junctions-r7/logs
MAIN=/c/Users/matma/Documents/Claude/kamion
R=bialystok-industrial-c
export KAMION_BLENDER="C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe"
pwsh $MAIN/scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner claude-junctions-r7 > /dev/null
uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region $R > $L/${TAG}_fidelity.log 2>&1; echo "fidelity rc $?"
uv run --project tools/worldgen python tools/worldgen/fidelity/summary.py $R > $L/${TAG}_fidelity_summary.txt 2>&1; head -2 $L/${TAG}_fidelity_summary.txt
uv run --project tools/worldgen python tests/physics/swept_path_gate3.py --out artifacts/junctions-r7/swept_${TAG} > $L/${TAG}_swept.log 2>&1; echo "swept rc $?"
uv run --project tools/worldgen python artifacts/junctions-r7/scripts/swept_sum.py artifacts/junctions-r7/swept_${TAG}
if [ "${2:-}" = full ]; then
  uv run --project tools/worldgen python -m pytest tests/gis tests/physics tests/gate3 -q -p no:cacheprovider > $L/${TAG}_pytest.log 2>&1; echo "pytest rc $?"
else
  uv run --project tools/worldgen python -m pytest -q -p no:cacheprovider tests/gis/test_junctions_r4.py tests/gis/test_hero_bridge.py tests/gis/test_gores.py tests/gis/test_streetscape.py tests/gis/test_world_roads.py tests/gis/test_lane_edges.py > $L/${TAG}_pytest.log 2>&1; echo "keytests rc $?"
fi
tail -6 $L/${TAG}_pytest.log
pwsh $MAIN/scripts/unity-slot.ps1 -Release -Pool heavy -Owner claude-junctions-r7 > /dev/null
echo "post done $(date +%H:%M)"
