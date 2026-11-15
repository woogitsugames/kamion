$ErrorActionPreference='Stop'
Set-Location 'C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/knyszyn-rynek-0227'
try {
 if ((Get-PSDrive C).Free -lt 60GB) { throw 'C below 60 GiB' }
 & pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner knyszyn-willow-0227
 if ($LASTEXITCODE -ne 0) { throw 'slot acquisition failed' }
 try {
  & 'C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe' -b --python tools/blender/world/make_trees.py -- --quick tree_willow_0 --out artifacts/knyszyn-rynek-0227/willow-study
  if ($LASTEXITCODE -ne 0) { throw "Blender exit $LASTEXITCODE" }
 } finally { & pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner knyszyn-willow-0227 }
 'OK' | Set-Content artifacts/knyszyn-rynek-0227/willow-study.done
} catch { $_ | Out-String | Set-Content artifacts/knyszyn-rynek-0227/willow-study.done; exit 1 }
