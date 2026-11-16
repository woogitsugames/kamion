Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bialystok-t3-0208'; $A='artifacts/bialystok-t3-0208'
"final start $(Get-Date -Format s) $(git rev-parse --short HEAD)" | Set-Content $A/final.status
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner bialystok-t3-0208-pytest | Out-Null
uv run --project tools/worldgen python -m pytest tests/gis -q --no-header -p no:cacheprovider *> $A/pytest-final.log
"pytest exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $A/final.status
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner bialystok-t3-0208-pytest | Out-Null
git status --short | Add-Content $A/final.status
"FINAL DONE $(Get-Date -Format s)" | Add-Content $A/final.status
