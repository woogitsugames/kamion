# dojfix-0202: full pytest tests/gis (heavy slot) then EditMode (unity slot). Status: tests.status, end: tests.done
param([string]$Only = 'pytest,editmode')
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dojfix-0202'
Set-Location $wt
$a = "artifacts/dojfix-0202"
Remove-Item "$a/tests-$Only.done" -ErrorAction SilentlyContinue
if ($Only -match 'pytest') {
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner dojfix-0202-pytest | Out-Null
"pytest start $(Get-Date -Format s)" | Add-Content "$a/tests.status"
uv run --project tools/worldgen --with pillow pytest tests/gis -q -p no:cacheprovider *> "$a/pytest-gis.log"
"pytest exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content "$a/tests.status"
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner dojfix-0202-pytest | Out-Null
# pytest rebuilds region C in place: its generated files are not part of this branch
git status --short Data/Regions/bialystok-industrial-c Data/SourceManifests *> "$a/pytest-regionC-touched.log"
git checkout -- Data/Regions/bialystok-industrial-c Data/SourceManifests 2>$null
}
if ($Only -match 'editmode') {
while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Owner dojfix-0202 | Out-Null
"editmode start $(Get-Date -Format s)" | Add-Content "$a/tests.status"
pwsh scripts/test.ps1 -Platform EditMode *> "$a/editmode.log"
"editmode exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content "$a/tests.status"
pwsh scripts/unity-slot.ps1 -Release -Owner dojfix-0202 | Out-Null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
}
"done $(Get-Date -Format s)" | Set-Content "$a/tests-$Only.done"
