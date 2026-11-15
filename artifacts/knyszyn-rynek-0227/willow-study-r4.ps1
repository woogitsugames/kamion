$ErrorActionPreference='Stop'
Set-Location 'C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/knyszyn-rynek-0227'
try {
 if ((Get-PSDrive C).Free -lt 60GB) { throw 'C below 60 GiB' }
 New-Item -ItemType Directory -Force artifacts/knyszyn-rynek-0227/willow-study-r4 | Out-Null
 Copy-Item art-source/world/vegetation/bark_linden.png,art-source/world/vegetation/leaves_birch.png artifacts/knyszyn-rynek-0227/willow-study-r4/
 & pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner knyszyn-willow-0227
 if ($LASTEXITCODE -ne 0) { throw 'slot acquisition failed' }
 try {
  & 'C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe' -b --python-exit-code 1 --python tools/blender/world/make_trees.py -- --quick tree_willow_0 --out artifacts/knyszyn-rynek-0227/willow-study-r4
  if ($LASTEXITCODE -ne 0) { throw "Blender exit $LASTEXITCODE" }; foreach ($f in @("impostor_tree_willow_0.png","impostor_tree_willow_0_n.png")) { if (-not (Test-Path "artifacts/knyszyn-rynek-0227/willow-study-r4/$f")) { throw "missing bake $f" } }
 } finally { & pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner knyszyn-willow-0227 }
 'OK' | Set-Content artifacts/knyszyn-rynek-0227/willow-study-r4.done
} catch { $_ | Out-String | Set-Content artifacts/knyszyn-rynek-0227/willow-study-r4.done; exit 1 }



