$ErrorActionPreference='Stop'
Set-Location 'C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/knyszyn-rynek-0227'
try {
 if ((Get-PSDrive C).Free -lt 60GB) { throw 'C below 60 GiB' }
 & pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner knyszyn-fidelity-0227
 if ($LASTEXITCODE -ne 0) { throw 'slot acquisition failed' }
 try {
  & uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c
  if ($LASTEXITCODE -ne 0) { throw "fidelity exit $LASTEXITCODE" }
  & uv run --project tools/worldgen python -m pytest tests/gis/test_road_fidelity.py -q
  if ($LASTEXITCODE -ne 0) { throw "pytest exit $LASTEXITCODE" }
 } finally { & pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner knyszyn-fidelity-0227 }
 'OK' | Set-Content artifacts/knyszyn-rynek-0227/fidelity-refresh.done
} catch { $_ | Out-String | Set-Content artifacts/knyszyn-rynek-0227/fidelity-refresh.done; exit 1 }
