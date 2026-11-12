#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/../../.."
TAG=${1:-f}
export ORTHO_HR_EXTRA="/c/Users/matma/Documents/Claude/kamion/artifacts/biezenstwa-island/ortho_hr"
PLAN_CACHE=artifacts/junctions-r7/plan_cache.pkl uv run --project tools/worldgen python tools/worldgen/fidelity/planview.py --out artifacts/junctions-r7/plan_${TAG} --rebuild --grid 1 --outline \
  --at=-752,76,9,kerb_joint --at=-766,76,20,kerb_merge --at=537,-693,9,bz_corner > artifacts/junctions-r7/logs/${TAG}_plan.log 2>&1; echo "plan rc $?"
PLAN_CACHE=artifacts/junctions-r7/plan_cache.pkl uv run --project tools/worldgen python tools/worldgen/fidelity/planview.py --out artifacts/junctions-r7/plan_${TAG} --grid 10 --outline \
  --at=552,-723,60,via >> artifacts/junctions-r7/logs/${TAG}_plan.log 2>&1; echo "plan2 rc $?"
