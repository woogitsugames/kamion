$ErrorActionPreference='Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
# The already queued focused run owns the same heavy identity. Do not acquire
# another job under that identity until its Python has ended and released it.
while (-not ((Get-Content "$PSScriptRoot/budget-fix-focusedgis-wrapper.log" -Raw).Contains('released gpt-landmarks-r1'))) { Start-Sleep -Seconds 2 }
if (-not ((Get-Content "$PSScriptRoot/budget-fix-focusedgis.log" -Raw).Contains('7 passed'))) { throw 'Initial focused budget test failed' }
& pwsh artifacts/landmarks-r1/heavy-step.ps1 -Step World -Log artifacts/landmarks-r1/budget-fix-world.log
if ($LASTEXITCODE -ne 0) { throw 'Budget-fix world generation failed' }
$meta=Get-Content art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2_meta.json -Raw | ConvertFrom-Json
if ($meta.tris[1] -gt 2828) { throw "Whole Low asset exceeds original budget: $($meta.tris[1])" }
if ((Get-Content "$PSScriptRoot/budget-fix-world.log" -Raw).Contains('fallback=True')) { throw 'Unexpected fallback' }
Add-Content -Encoding utf8 "$PSScriptRoot/STATUS.md" "`nKrok 37: regeneracja modelu i świata po naprawie budżetu: trójkąty $($meta.tris -join '/'), brak fallback=True. Następnie pojedyncze testy remizy i hero building."
& git add art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2.glb art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2_meta.json Data/Regions/bialystok-industrial-c/generated/landmarks/fire_station_jrg2.spec.json
& git add -f artifacts/landmarks-r1/STATUS.md
& git commit -m 'wip(landmarks): regeneracja remizy w oryginalnym budżecie Low'
if ($LASTEXITCODE -ne 0) { throw 'World checkpoint failed' }
foreach ($file in @('test_fire_station_r7.py','test_hero_building.py')) {
    & pwsh artifacts/landmarks-r1/heavy-step.ps1 -Step FocusedGIS -TestFile "tests/gis/$file" -Log "artifacts/landmarks-r1/budget-fix-$file.log"
    if ($LASTEXITCODE -ne 0) { throw "Focused failure: $file" }
}
Add-Content -Encoding utf8 "$PSScriptRoot/STATUS.md" "`nKrok 38: oba pojedyncze pliki remizy przeszły po regeneracji (heavy). Import i pełne 192 porównania w nowym katalogu after-budget, bez nadpisywania wcześniejszych dowodów."
& git add -f artifacts/landmarks-r1/STATUS.md
& git commit -m 'wip(landmarks): testy limitu całego hero po regeneracji'
if ($LASTEXITCODE -ne 0) { throw 'Focused checkpoint failed' }
& pwsh artifacts/landmarks-r1/unity-step.ps1 -Step Import
if ($LASTEXITCODE -ne 0) { throw 'Budget-fix import failed' }
& pwsh artifacts/landmarks-r1/unity-step.ps1 -Step Capture -Phase after-budget -Cameras all
if ($LASTEXITCODE -ne 0) { throw 'Budget-fix full camera capture failed' }
@{world_exit=0;focused_exit=0;import_exit=0;capture_exit=0;tris=$meta.tris} | ConvertTo-Json | Set-Content -Encoding utf8 "$PSScriptRoot/budget-fix-result.json"
exit 0
