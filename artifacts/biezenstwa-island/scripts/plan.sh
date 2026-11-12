#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/../../.."
TAG=${1:-f}
export ORTHO_HR_EXTRA="$PWD/artifacts/biezenstwa-island/ortho_hr"
PLAN_CACHE=artifacts/biezenstwa-island/plan_cache.pkl uv run --project tools/worldgen python tools/worldgen/fidelity/planview.py --out artifacts/biezenstwa-island/plan_${TAG} --rebuild --grid 1 --outline \
  --at=537,-693,9,bz_corner --at=540,-690,22,bz_n_slip --at=-219,-236,9,and_nose > artifacts/biezenstwa-island/logs/${TAG}_plan.log 2>&1; echo "plan rc $?"
