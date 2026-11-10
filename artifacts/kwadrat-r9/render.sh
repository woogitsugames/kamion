#!/usr/bin/env bash
# Asset iteration: spec (standalone) -> Blender control renders -> 960 px JPG. Usage: render.sh <iteration> [cams]
set -e
cd "$(dirname "$0")/../.."
IT="$1"
CAMS="${2:-}"
BL="/c/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe"
uv run --project tools/worldgen python -c "
import sys; sys.path.insert(0,'tools/worldgen')
from streetscape import hero_depot as HD
res,stats=HD.standalone_spec('bialystok-industrial-c')
for h in res.values(): print('spec sha', h['sha'][:12], 'holes', len(h['spec']['holes']), 'unmatched', h['unmatched'])
" 2>&1 | tail -1
OUT="$(pwd -W 2>/dev/null || pwd)/artifacts/kwadrat-r9/blender/$IT"
ARGS=(--spec Data/Regions/bialystok-industrial-c/generated/landmarks/kwadrat_park.spec.json --render "$OUT")
if [ -n "$CAMS" ]; then ARGS+=(--cams "$CAMS"); fi
"$BL" -b --factory-startup -P tools/blender/world/landmarks/make_depot.py -- "${ARGS[@]}" 2>&1 | grep -i "error\|Traceback\|DEPOT\|  File \|line " | tail -12
cd "artifacts/kwadrat-r9/blender/$IT"
for f in *.png; do magick "$f" -resize 960x "${f%.png}.jpg" 2>/dev/null; done
ls *.jpg
