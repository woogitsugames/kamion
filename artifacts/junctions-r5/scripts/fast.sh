#!/usr/bin/env bash
# build_world -> export-route -> key tests -> plan views (ADR 0110 iteration); logs artifacts/junctions-r5/logs/<tag>_*
set -u
cd "$(dirname "$0")/../../.."
TAG=${1:-f}
L=artifacts/junctions-r5/logs
R=bialystok-industrial-c
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $R > $L/${TAG}_build.log 2>&1; echo "build rc $?"
uv run --project tools/worldgen python scripts/export-route.py --region $R > $L/${TAG}_route.log 2>&1; echo "route rc $?"
cp Data/Regions/$R/generated/roads_qa.json $L/${TAG}_roads_qa.json; cp Data/Regions/$R/generated/streetscape_qa.json $L/${TAG}_streetscape_qa.json
cp Data/Regions/$R/generated/terrain_walls_qa.json $L/${TAG}_terrain_walls_qa.json; cp Data/Regions/$R/generated/road_consistency_qa.json $L/${TAG}_road_consistency_qa.json
bash artifacts/junctions-r5/scripts/plan.sh $TAG
uv run --project tools/worldgen python -m pytest -q -p no:cacheprovider tests/gis/test_p21_hatch.py tests/gis/test_aprons.py tests/gis/test_junction_paint.py tests/gis/test_road_consistency.py tests/gis/test_route_corridor.py tests/gis/test_lane_edges.py tests/gis/test_gores.py tests/gis/test_streetscape.py tests/gis/test_world_roads.py > $L/${TAG}_keytests.log 2>&1; echo "keytests rc $?"; tail -3 $L/${TAG}_keytests.log
