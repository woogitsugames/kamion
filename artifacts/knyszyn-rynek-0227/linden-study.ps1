$ErrorActionPreference='Stop'
Set-Location 'C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/knyszyn-rynek-0227'
try {
 if ((Get-PSDrive C).Free -lt 60GB) { throw 'C below 60 GiB' }
 & pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner knyszyn-linden-0227
 if ($LASTEXITCODE -ne 0) { throw 'slot acquisition failed' }
 try {
  & 'C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe' -b --factory-startup --python-exit-code 1 -P tools/blender/world/make_trees.py -- --park-linden-study --out artifacts/knyszyn-rynek-0227/linden-study
  if ($LASTEXITCODE -ne 0) { throw "blender exit $LASTEXITCODE" }
  if (-not (Test-Path artifacts/knyszyn-rynek-0227/linden-study/tree_linden_park_study.glb)) { throw 'missing study GLB' }
 } finally { & pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner knyszyn-linden-0227 }
 'OK' | Set-Content artifacts/knyszyn-rynek-0227/linden-study.done
} catch { $_ | Out-String | Set-Content artifacts/knyszyn-rynek-0227/linden-study.done; exit 1 }
