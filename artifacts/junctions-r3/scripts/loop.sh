#!/usr/bin/env bash
# build_world -> export-route -> fidelity -> pytest gis ; logs in artifacts/junctions-r3/logs/<tag>_*.log
set -u
cd "$(dirname "$0")/../../.."
TAG=${1:-b}
L=artifacts/junctions-r3/logs
mkdir -p $L
R=bialystok-industrial-c
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $R > $L/${TAG}_build.log 2>&1; echo "build rc $?"
uv run --project tools/worldgen python scripts/export-route.py --region $R > $L/${TAG}_route.log 2>&1; echo "route rc $?"
uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region $R > $L/${TAG}_fidelity.log 2>&1; echo "fidelity rc $?"
uv run --project tools/worldgen python tools/worldgen/fidelity/summary.py $R > $L/${TAG}_fidelity_summary.txt 2>&1; head -2 $L/${TAG}_fidelity_summary.txt
uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider > $L/${TAG}_pytest.log 2>&1; echo "pytest rc $?"; tail -5 $L/${TAG}_pytest.log
uv run --project tools/worldgen python tests/physics/swept_path_gate3.py --out artifacts/junctions-r3/swept_${TAG} > $L/${TAG}_swept.log 2>&1; echo "swept rc $?"
