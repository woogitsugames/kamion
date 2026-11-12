#!/usr/bin/env bash
# build_world -> export-route -> plan -> fidelity -> swept -> pytest gis ; logs in artifacts/junctions-r6/logs/<tag>_*.log
set -u
cd "$(dirname "$0")/../../.."
TAG=${1:-b}
L=artifacts/junctions-r6/logs
mkdir -p $L
R=bialystok-industrial-c
export KAMION_BLENDER="C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe"
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $R > $L/${TAG}_build.log 2>&1; echo "build rc $?"
uv run --project tools/worldgen python scripts/export-route.py --region $R > $L/${TAG}_route.log 2>&1; echo "route rc $?"
for f in roads_qa streetscape_qa terrain_walls_qa road_consistency_qa; do cp Data/Regions/$R/generated/$f.json $L/${TAG}_$f.json; done
echo "world ready $(date +%H:%M)"
bash artifacts/junctions-r6/scripts/plan.sh $TAG
uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region $R > $L/${TAG}_fidelity.log 2>&1; echo "fidelity rc $?"
uv run --project tools/worldgen python tools/worldgen/fidelity/summary.py $R > $L/${TAG}_fidelity_summary.txt 2>&1; head -2 $L/${TAG}_fidelity_summary.txt
uv run --project tools/worldgen python tests/physics/swept_path_gate3.py --out artifacts/junctions-r6/swept_${TAG} > $L/${TAG}_swept.log 2>&1; echo "swept rc $?"
uv run --project tools/worldgen python artifacts/junctions-r6/scripts/swept_sum.py artifacts/junctions-r6/swept_${TAG}
uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider > $L/${TAG}_pytest.log 2>&1; echo "pytest rc $?"; tail -5 $L/${TAG}_pytest.log
echo "loop done $(date +%H:%M)"
