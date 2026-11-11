#!/usr/bin/env bash
# build_world -> export-route -> key tests -> plan views (ADR 0100 iteration); logs artifacts/junctions-r3/logs/<tag>_*
set -u
cd "$(dirname "$0")/../../.."
TAG=${1:-f}
L=artifacts/junctions-r3/logs
R=bialystok-industrial-c
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $R > $L/${TAG}_build.log 2>&1; echo "build rc $?"
uv run --project tools/worldgen python scripts/export-route.py --region $R > $L/${TAG}_route.log 2>&1; echo "route rc $?"
uv run --project tools/worldgen python -m pytest -q -p no:cacheprovider tests/gis/test_p21_hatch.py tests/gis/test_aprons.py tests/gis/test_junction_paint.py tests/gis/test_road_consistency.py tests/gis/test_route_corridor.py tests/gis/test_lane_edges.py tests/gis/test_gores.py > $L/${TAG}_keytests.log 2>&1; echo "keytests rc $?"; tail -3 $L/${TAG}_keytests.log
PLAN_CACHE=artifacts/junctions-r3/plan_cache.pkl uv run --project tools/worldgen python tools/worldgen/fidelity/planview.py --out artifacts/junctions-r3/plan_${TAG} --rebuild --grid 5 --route \
  --at=-552,118,30,putry_n --at=-560,-8,30,ma010 --at=-782,77,28,kerb_merge --at=-812,57,22,east_split --at=-240,-240,30,n10015785253 \
  --at=-85,-338,40,merge1060 --at=-360,-125,35,fork_putry_s1440 --at=345,-565,25,s610 > $L/${TAG}_plan.log 2>&1; echo "plan rc $?"
