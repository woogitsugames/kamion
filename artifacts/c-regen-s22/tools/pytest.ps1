$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\c-regen-s22'; Set-Location $wt
$o = 'artifacts/c-regen-s22/regen'; $st = "$o/pytest.status"
"start $(Get-Date -Format s)" | Set-Content $st
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner c-regen-s22-pytest | Out-Null
uv run --project tools/worldgen pytest tests/gis -v -p no:cacheprovider -o faulthandler_timeout=600 *> "$o/pytest.log"
"pytest exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner c-regen-s22-pytest | Out-Null
"DONE" | Add-Content $st
