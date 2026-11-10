#!/usr/bin/env bash
# usage: cycle.sh <outname> [tiers] [lights]  : build_world -> import-region -> render (waits for PHONE_RUN lock)
cd "$(dirname "$0")/../.."
L=artifacts/viaduct-r9/logs
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c > $L/build_world_$1.log 2>&1; echo "build_world exit $?"
grep "hero bridges" $L/build_world_$1.log
while [ -e ../../../artifacts/locks/PHONE_RUN ]; do sleep 60; done
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c > $L/import_$1.log 2>&1; echo "import exit $?"
grep "IMPORT_RESULT" $L/import_$1.log
bash artifacts/viaduct-r9/render.sh "$@"
