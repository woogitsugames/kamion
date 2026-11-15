$ErrorActionPreference='Stop'
Set-Location 'C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/knyszyn-rynek-0227'
try {
 if ((Get-PSDrive C).Free -lt 60GB) { throw 'C below 60 GiB' }
 & pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner knyszyn-gis-0227
 if ($LASTEXITCODE -ne 0) { throw 'slot acquisition failed' }
 try {
  & uv run --project tools/worldgen python -m pytest tests/gis -q
  if ($LASTEXITCODE -ne 0) { throw "pytest exit $LASTEXITCODE" }
 } finally { & pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner knyszyn-gis-0227 }
 'OK' | Set-Content artifacts/knyszyn-rynek-0227/gis-r6.done
} catch { $_ | Out-String | Set-Content artifacts/knyszyn-rynek-0227/gis-r6.done; exit 1 }
