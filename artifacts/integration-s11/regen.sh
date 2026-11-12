#!/usr/bin/env bash
# s11 regeneration after merges (heavy pool). Usage: bash artifacts/integration-s11/regen.sh <tag>
set -u
cd /c/Users/matma/Documents/Claude/kamion
TAG=${1:-regen}; R=bialystok-industrial-c
SLOT="pwsh -NoProfile -File scripts/unity-slot.ps1"
echo "START $(date -Iseconds) $(git rev-parse --short HEAD)"
$SLOT -Acquire -Pool heavy -Priority -PollSeconds 5 -Owner lead-s11-$TAG
uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py; echo "build_all rc=$?"
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $R; echo "build_world rc=$?"
uv run --project tools/worldgen python scripts/export-route.py --region $R; echo "export-route rc=$?"
uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region $R; echo "fidelity rc=$?"
uv run --project tools/worldgen python -m pytest tests/gis tests/physics tests/gate3 -q -p no:cacheprovider 2>&1 | tail -25; echo "PYTEST rc=${PIPESTATUS[0]}"
$SLOT -Release -Pool heavy -Owner lead-s11-$TAG
echo "END $(date -Iseconds)"
