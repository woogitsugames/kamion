#!/bin/sh
# usage: sh artifacts/viaduct-r9/wip.sh "<status line>" "<commit subject>"   (run from the worktree root)
[ -n "$1" ] && printf -- '- %s\n' "$1" >> artifacts/viaduct-r9/STATUS.md
mkdir -p /c/Users/matma/Documents/Claude/kamion/artifacts/viaduct-r9
cp artifacts/viaduct-r9/STATUS.md /c/Users/matma/Documents/Claude/kamion/artifacts/viaduct-r9/STATUS.md
git add -f artifacts/viaduct-r9/STATUS.md artifacts/viaduct-r9/wip.sh
git add art-source/world/landmarks art-source/world/textures/viaduct_steel.png art-source/world/materials tools tests/gis/test_hero_bridge.py \
  Data/Regions/bialystok-industrial-c/overrides.yaml Data/Regions/bialystok-industrial-c/generated/landmarks \
  game/Assets/_Project/World/Import/InstanceImporter.cs docs 2>/dev/null
git commit -q -m "WIP(viaduct): $2

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>"
git log --oneline | head -1
