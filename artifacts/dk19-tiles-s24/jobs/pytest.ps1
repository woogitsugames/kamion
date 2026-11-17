$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s24'; Set-Location $wt
$st = "$wt\artifacts\dk19-tiles-s24\jobs\pytest.status"; "start $(Get-Date -Format s)" | Set-Content $st
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -MaxSlots 3 -Owner dk19-s24-pytest | Out-Null
uv run --project tools/worldgen pytest tests/gis -q -p no:cacheprovider *> "$wt\artifacts\logs\dk19-s24-pytest.log"
"pytest exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner dk19-s24-pytest | Out-Null
"DONE exit=0" | Add-Content $st
