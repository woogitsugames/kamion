#!/bin/bash
# usage: preview.sh <iteration dir name> [extra args for render_cars.py]   (run from the worktree root)
set -e
D="$(pwd)/artifacts/cars-r9/$1"; shift
uv run --project tools/worldgen python tools/worldgen/qa/car_preview.py --out "$D"
"/c/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe" -b -P tools/blender/world/render_cars.py -- "$D/cars.json" "$D" "$@" 2>&1 | grep -E "Saved|Error|error" || true
