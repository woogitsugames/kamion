$ErrorActionPreference = 'Continue'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bialystok-dk65-t2-0206'
$n = 'bialystok-dk65-t2-0206'; $st = "artifacts/$n/final.status"
"final start $(Get-Date -Format s)" | Add-Content $st
while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Owner $n | Out-Null
pwsh scripts/test.ps1 -Platform EditMode *> "artifacts/$n/editmode-final.log"
"editmode exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
pwsh scripts/unity-slot.ps1 -Release -Owner $n | Out-Null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner "$n-pytest" | Out-Null
uv run --project tools/worldgen python -m pytest tests/gis -q --no-header -p no:cacheprovider *> "artifacts/$n/pytest-final.log"
"pytest exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner "$n-pytest" | Out-Null
git checkout -- Data/Regions/bialystok-industrial-c Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json
"FINAL DONE $(Get-Date -Format s)" | Add-Content $st
