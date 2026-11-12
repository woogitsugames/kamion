$ErrorActionPreference='Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
$started=(Get-Date).ToUniversalTime()
& pwsh artifacts/landmarks-r3/heavy-step.ps1 -Step WorldWithFocusedGIS -Log artifacts/landmarks-r3/silhouette-world.log
if($LASTEXITCODE -ne 0){throw 'EC generation/focused tests failed'}
$world=Get-Content "$PSScriptRoot/silhouette-world.log" -Raw
if($world.Contains('fallback=True') -or -not $world.Contains('done')){throw 'EC generator incomplete or fallback'}
@{start_utc=$started.ToString('o');end_utc=(Get-Date).ToUniversalTime().ToString('o');world_exit=0;focused_exit=0} | ConvertTo-Json | Set-Content "$PSScriptRoot/silhouette-world-result.json" -Encoding utf8
Add-Content "$PSScriptRoot/STATUS.md" "`nKrok 12: generator EC i cały pojedynczy plik test_ec_chimneys.py zakończone; brak fallback=True. Następny krok: import i pełny zestaw czterech warunków after-silhouette, bez zmiany kamer baseline."
git add -f artifacts/landmarks-r3/STATUS.md artifacts/landmarks-r3/silhouette-world-result.json artifacts/landmarks-r3/silhouette-world.log.units artifacts/landmarks-r3/silhouette-world.log.focused
git commit -m 'wip(landmarks): EC wygenerowane i sprawdzone na pojedynczym pliku testów'
if($LASTEXITCODE -ne 0){throw 'Candidate checkpoint failed'}
& pwsh artifacts/landmarks-r3/unity-step.ps1 -Step Import
if($LASTEXITCODE -ne 0){throw 'EC import failed'}
& pwsh artifacts/landmarks-r3/unity-step.ps1 -Step Capture -Phase after-silhouette -Cameras all
if($LASTEXITCODE -ne 0){throw 'EC capture failed'}
@{complete=$true;import_exit=0;capture_exit=0;utc=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content "$PSScriptRoot/silhouette-result.json" -Encoding utf8
exit 0
