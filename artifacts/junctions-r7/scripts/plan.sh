#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/../../.."
TAG=${1:-f}
PLAN_CACHE=artifacts/junctions-r7/plan_cache.pkl uv run --project tools/worldgen python tools/worldgen/fidelity/planview.py --out artifacts/junctions-r7/plan_${TAG} --rebuild --grid 5 --route \
  --at=-552,118,30,putry_n --at=-560,-8,30,ma010 --at=-782,77,28,kerb_merge --at=-812,57,22,east_split --at=-240,-240,30,n10015785253 \
  --at=-85,-338,40,merge1060 --at=-360,-125,35,fork_putry_s1440 --at=345,-565,25,s610 --at=-216,-227,8,n100_north --at=-110,-322,14,bay_w --at=-553,131,10,putry_nose > artifacts/junctions-r7/logs/${TAG}_plan.log 2>&1; echo "plan rc $?"
