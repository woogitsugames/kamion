$ErrorActionPreference='Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
& pwsh artifacts/landmarks-r4/heavy-step.ps1 -Step World -Log artifacts/landmarks-r4/candidate-b-world.log
if($LASTEXITCODE -ne 0){throw 'B world failed'}
$log=Get-Content "$PSScriptRoot/candidate-b-world.log" -Raw
if($log.Contains('fallback=True') -or -not $log.Contains('done')){throw 'B incomplete or fallback'}
foreach($script in @('source_scope.py','crown_asset_audit.py','world_scope.py')){
    & uv run --project tools/worldgen python "artifacts/landmarks-r4/$script" *> "$PSScriptRoot/b-$script.log"
    if($LASTEXITCODE -ne 0){throw "B audit failed: $script"}
}
Add-Content "$PSScriptRoot/STATUS.md" -Encoding utf8 "`nKrok 10: World B i wszystkie3 audyty zaliczone; brak fallback=True. Trwa zapis modelu i podgląd8 PNG przed decyzją wizualną. Żaden pełny GIS nie został jeszcze uruchomiony w r4."
& git add -- Data/Regions/bialystok-industrial-c/generated/landmarks/fire_station_jrg2.spec.json Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json Data/Regions/bialystok-industrial-c/generated/world_manifest.json art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2.glb art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2_meta.json
& git add -f -- artifacts/landmarks-r4/STATUS.md artifacts/landmarks-r4/crown-asset-audit.json artifacts/landmarks-r4/source-scope.json artifacts/landmarks-r4/world-scope.json
& git commit -m 'wip(landmarks): wygenerowany wariant B i zapisane dowody zakresu'
if($LASTEXITCODE -ne 0){throw 'B generated checkpoint failed'}
& pwsh artifacts/landmarks-r4/preview-b.ps1
if($LASTEXITCODE -ne 0){throw 'B diagnostic preview failed'}
@{complete=$true;scope='Variant B diagnostic8 PNG only; tests and full camera capture still required';utc=(Get-Date).ToUniversalTime().ToString('o')} |
    ConvertTo-Json | Set-Content "$PSScriptRoot/candidate-b-result.json" -Encoding utf8
exit 0
