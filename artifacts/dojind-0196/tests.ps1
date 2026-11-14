# dojind-0196: full pytest tests/gis (heavy slot) then EditMode (unity slot). Status: tests.status, end: tests.done
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dojind-0196'
Set-Location $wt
$a = "artifacts/dojind-0196"
Remove-Item "$a/tests.done" -ErrorAction SilentlyContinue
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner dojind-0196-pytest | Out-Null
"pytest start $(Get-Date -Format s)" | Add-Content "$a/tests.status"
uv run --project tools/worldgen --with pillow pytest tests/gis -q -p no:cacheprovider *> "$a/pytest-gis.log"
"pytest exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content "$a/tests.status"
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner dojind-0196-pytest | Out-Null
# pytest rebuilds region C in place: its generated files are not part of this branch
git checkout -- Data/Regions/bialystok-industrial-c Data/SourceManifests 2>$null
while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Owner dojind-0196 | Out-Null
"editmode start $(Get-Date -Format s)" | Add-Content "$a/tests.status"
pwsh scripts/test.ps1 -Platform EditMode *> "$a/editmode.log"
"editmode exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content "$a/tests.status"
pwsh scripts/unity-slot.ps1 -Release -Owner dojind-0196 | Out-Null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
"done $(Get-Date -Format s)" | Set-Content "$a/tests.done"
