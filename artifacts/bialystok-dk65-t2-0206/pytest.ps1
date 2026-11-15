$ErrorActionPreference = 'Continue'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bialystok-dk65-t2-0206'
$n = 'bialystok-dk65-t2-0206'
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner "$n-pytest" | Out-Null
uv run --project tools/worldgen python -m pytest tests/gis -q --no-header -p no:cacheprovider *> "artifacts/$n/pytest.log"
"pytest exit=$LASTEXITCODE $(Get-Date -Format s)" | Set-Content "artifacts/$n/pytest.status"
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner "$n-pytest" | Out-Null
