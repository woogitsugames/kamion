$ErrorActionPreference='Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
$started=(Get-Date).ToUniversalTime()
& pwsh artifacts/landmarks-r3/heavy-step.ps1 -Step WorldWithFocusedGIS -Log artifacts/landmarks-r3/corrected-world.log
if($LASTEXITCODE -ne 0){throw 'EC generation/focused tests failed'}
$world=Get-Content "$PSScriptRoot/corrected-world.log" -Raw
if($world.Contains('fallback=True') -or -not $world.Contains('done')){throw 'EC generator incomplete or fallback'}
@{start_utc=$started.ToString('o');end_utc=(Get-Date).ToUniversalTime().ToString('o');world_exit=0;focused_exit=0} | ConvertTo-Json | Set-Content "$PSScriptRoot/corrected-world-result.json" -Encoding utf8
Add-Content "$PSScriptRoot/STATUS.md" "`nKrok 16: generator korekty i dwa osobno wykonane pliki testów EC/podpomostu zakończone; brak fallback=True. Następny krok: import i pełny zestaw czterech warunków after-corrected, bez zmiany kamer baseline."
git add -f artifacts/landmarks-r3/STATUS.md artifacts/landmarks-r3/corrected-world-result.json artifacts/landmarks-r3/corrected-world.log.units artifacts/landmarks-r3/corrected-world.log.focused artifacts/landmarks-r3/corrected-world.log.pier-units artifacts/landmarks-r3/corrected-world.log.pier-focused
git commit -m 'wip(landmarks): EC wygenerowane i sprawdzone na pojedynczym pliku testów'
if($LASTEXITCODE -ne 0){throw 'Candidate checkpoint failed'}
& pwsh artifacts/landmarks-r3/unity-step.ps1 -Step Import
if($LASTEXITCODE -ne 0){throw 'EC import failed'}
& pwsh artifacts/landmarks-r3/unity-step.ps1 -Step Capture -Phase after-corrected -Cameras all
if($LASTEXITCODE -ne 0){throw 'EC capture failed'}
@{complete=$true;import_exit=0;capture_exit=0;utc=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content "$PSScriptRoot/corrected-result.json" -Encoding utf8
exit 0
