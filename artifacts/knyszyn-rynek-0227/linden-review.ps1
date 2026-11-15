$ErrorActionPreference='Stop'
Set-Location 'C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/knyszyn-rynek-0227'
try {
 if ((Get-PSDrive C).Free -lt 60GB) { throw 'C below 60 GiB' }
 & pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner knyszyn-linden-review-0227
 if ($LASTEXITCODE -ne 0) { throw 'slot acquisition failed' }
 try {
  & 'C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe' -b --factory-startup --python-exit-code 1 -P artifacts/knyszyn-rynek-0227/linden-review.py
  if ($LASTEXITCODE -ne 0) { throw "blender exit $LASTEXITCODE" }
  if ((Get-ChildItem artifacts/knyszyn-rynek-0227/linden-study/review -Filter '*.png').Count -ne 16) { throw 'incomplete review renders' }
 } finally { & pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner knyszyn-linden-review-0227 }
 'OK' | Set-Content artifacts/knyszyn-rynek-0227/linden-review.done
} catch { $_ | Out-String | Set-Content artifacts/knyszyn-rynek-0227/linden-review.done; exit 1 }
