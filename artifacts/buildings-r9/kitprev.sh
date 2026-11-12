#!/usr/bin/env bash
# kit preview loop: geometry -> Blender renders -> two contact sheets. Run from the worktree root.
set -e
D=artifacts/buildings-r9/kitprev
uv run --project tools/worldgen python artifacts/buildings-r9/kit_preview.py $D 2>&1 | tail -2
"/c/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe" -b --factory-startup -P artifacts/buildings-r9/kit_preview_blender.py -- "$(pwd -W)/$D" 2>&1 | grep -i -E "error|Traceback" | head -5 || true
magick montage $D/view_0.png $D/view_1.png $D/view_2.png $D/view_3.png -geometry 960x+2+2 -tile 2x $D/sheet_a.jpg 2>/dev/null
magick montage $D/view_4.png $D/view_5.png $D/view_6.png $D/view_7.png -geometry 960x+2+2 -tile 2x $D/sheet_b.jpg 2>/dev/null
