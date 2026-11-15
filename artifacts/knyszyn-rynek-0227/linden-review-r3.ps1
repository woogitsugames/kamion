$ErrorActionPreference='Stop'
Set-Location 'C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/knyszyn-rynek-0227'
try {
 if ((Get-PSDrive C).Free -lt 60GB) { throw 'C below 60 GiB' }
 & pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner knyszyn-linden-r3-0227
 if ($LASTEXITCODE -ne 0) { throw 'slot acquisition failed' }
 try {
  & 'C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe' -b --factory-startup --python-exit-code 1 -P tools/blender/world/make_trees.py -- --park-linden-study-r3 --out artifacts/knyszyn-rynek-0227/linden-study-r3
  if ($LASTEXITCODE -ne 0) { throw "export exit $LASTEXITCODE" }
  & 'C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe' -b --factory-startup --python-exit-code 1 -P artifacts/knyszyn-rynek-0227/linden-review-r3.py
  if ($LASTEXITCODE -ne 0) { throw "review exit $LASTEXITCODE" }
  if ((Get-ChildItem artifacts/knyszyn-rynek-0227/linden-study-r3/review -Filter '*.png').Count -ne 16) { throw 'incomplete review renders' }
 } finally { & pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner knyszyn-linden-r3-0227 }
 'OK' | Set-Content artifacts/knyszyn-rynek-0227/linden-review-r3.done
} catch { $_ | Out-String | Set-Content artifacts/knyszyn-rynek-0227/linden-review-r3.done; exit 1 }
