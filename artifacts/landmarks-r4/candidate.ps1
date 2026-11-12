$ErrorActionPreference='Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
& pwsh artifacts/landmarks-r4/heavy-step.ps1 -Step World -Log artifacts/landmarks-r4/candidate-world.log
if($LASTEXITCODE -ne 0){throw 'Candidate world failed'}
$world=Get-Content "$PSScriptRoot/candidate-world.log" -Raw
if($world.Contains('fallback=True') -or -not $world.Contains('done')){throw 'Candidate incomplete or fallback'}
& uv run --project tools/worldgen python artifacts/landmarks-r4/crown_asset_audit.py *> artifacts/landmarks-r4/crown-asset-audit.log
if($LASTEXITCODE -ne 0){throw 'Candidate changed protected hero geometry'}
Add-Content "$PSScriptRoot/STATUS.md" -Encoding utf8 "`nKrok 6: generator wariantu zakończony bez fallback=True; audyt GLB zaliczony. Następnie dwa pojedyncze pliki testów, każdy w osobnym heavy, bez trzymania heavy przez import/render."
& git add -f -- artifacts/landmarks-r4/STATUS.md artifacts/landmarks-r4/crown-asset-audit.json
& git commit -m 'wip(landmarks): wygenerowane korony r4 i kontrola reszty obiektu'
if($LASTEXITCODE -ne 0){throw 'Candidate audit checkpoint failed'}
& pwsh artifacts/landmarks-r4/heavy-step.ps1 -Step FocusedGIS -TestFile tests/gis/test_fire_station_r7.py -Log artifacts/landmarks-r4/focused-fire-station.log
if($LASTEXITCODE -ne 0){throw 'Candidate fire station tests failed'}
& pwsh artifacts/landmarks-r4/heavy-step.ps1 -Step FocusedGIS -TestFile tests/gis/test_hero_building.py -Log artifacts/landmarks-r4/focused-hero-building.log
if($LASTEXITCODE -ne 0){throw 'Candidate hero tests failed'}
Add-Content "$PSScriptRoot/STATUS.md" -Encoding utf8 "`nKrok 7: oba pojedyncze pliki testów zaliczone, sloty heavy zwolnione. Następny krok: import i16 diagnostycznych PNG remizy, nie pełny wynik końcowy."
& git add -f -- artifacts/landmarks-r4/STATUS.md
& git commit -m 'wip(landmarks): testy remizy i hero przed oceną wizualną r4'
if($LASTEXITCODE -ne 0){throw 'Candidate focused checkpoint failed'}
& pwsh artifacts/landmarks-r4/unity-step.ps1 -Step Import
if($LASTEXITCODE -ne 0){throw 'Candidate import failed'}
& pwsh artifacts/landmarks-r4/unity-step.ps1 -Step Capture -Phase after-crowns-focus -Cameras 'fire-station-ref7197,fire-station-abeam,fire-station-route,fire-station-above'
if($LASTEXITCODE -ne 0){throw 'Candidate diagnostic capture failed'}
@{complete=$true;scope='Diagnostic4 fire-station cameras only, full final capture still required';world_exit=0;focused_exit=0;capture_exit=0;utc=(Get-Date).ToUniversalTime().ToString('o')} |
    ConvertTo-Json | Set-Content "$PSScriptRoot/candidate-result.json" -Encoding utf8
exit 0
