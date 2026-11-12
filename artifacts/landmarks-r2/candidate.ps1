$ErrorActionPreference='Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
& pwsh artifacts/landmarks-r2/heavy-step.ps1 -Step World -Log artifacts/landmarks-r2/candidate-world.log
if($LASTEXITCODE -ne 0){throw 'Candidate world generation failed'}
$world=Get-Content "$PSScriptRoot/candidate-world.log" -Raw
if($world.Contains('fallback=True') -or -not $world.Contains('done')){throw 'Candidate incomplete or using fallback'}
& pwsh artifacts/landmarks-r2/heavy-step.ps1 -Step FocusedGIS -Log artifacts/landmarks-r2/candidate-focused-gis.log
if($LASTEXITCODE -ne 0){throw 'Candidate underdeck tests failed'}
Add-Content -Encoding utf8 "$PSScriptRoot/STATUS.md" "`nKrok 7: świat kandydata wygenerowany pod heavy bez fallback=True, pojedynczy plik test_viaduct_underdeck.py zakończony powodzeniem (szczegóły w candidate-focused-gis.log). NASTĘPNY KROK: import Low+High i 58 kamer w czterech kombinacjach do after. Wynik wizualny i budżet jeszcze UNVERIFIED."
& git add -f artifacts/landmarks-r2/STATUS.md
& git commit -m 'wip(landmarks): regeneracja kandydata i testy części podmostowej'
if($LASTEXITCODE -ne 0){throw 'Candidate checkpoint failed'}
& pwsh artifacts/landmarks-r2/unity-step.ps1 -Step Import
if($LASTEXITCODE -ne 0){throw 'Candidate import failed'}
& pwsh artifacts/landmarks-r2/unity-step.ps1 -Step Capture -Phase after -Cameras all
if($LASTEXITCODE -ne 0){throw 'Candidate capture failed'}
@{complete=$true;world_exit=0;focused_exit=0;import_exit=0;capture_exit=0} | ConvertTo-Json | Set-Content -Encoding utf8 "$PSScriptRoot/candidate-result.json"
exit 0
