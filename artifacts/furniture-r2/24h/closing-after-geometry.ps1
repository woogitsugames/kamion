param([Parameter(Mandatory=$true)][int]$GeometryPid)
$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r2/24h'
$geometry=Get-CimInstance Win32_Process -Filter "ProcessId=$GeometryPid"
if($geometry){
    if($geometry.CommandLine -notmatch 'furniture-r2/24h/heavy-step.ps1.*-Step geometry'){throw 'Unexpected geometry process'}
    Wait-Process -Id $GeometryPid -ErrorAction SilentlyContinue
}
# Serial ownership: never acquire the same heavy owner while its geometry step is alive.
# Geometry failure is retained for review; it must not silently suppress required closing tests.
$results=[ordered]@{gis=$null;physics_gate3=$null;editmode=0;editmode_xml='test-results/editmode-20261112-094622.xml'}
foreach($step in @('gis','physics')){
    & pwsh "$ev/heavy-step.ps1" -Step $step -Phase final3
    $results[$(if($step -eq 'gis'){'gis'}else{'physics_gate3'})]=$LASTEXITCODE
    $results | ConvertTo-Json | Set-Content "$ev/closing-test-exits.json"
}
Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): końcowe Python zakończone:GIS=$($results.gis),physics/gate3=$($results.physics_gate3). Wcześniejsze EditMode340/340 pozostaje ważne, kod zamrożony. Odczytać pełne logi i porażki przed REPORT; nie utożsamiać wykonania z PASS."
Copy-Item "$ev/STATUS.md" artifacts/furniture-r2/STATUS.md
git add -f "$ev/STATUS.md" artifacts/furniture-r2/STATUS.md "$ev/closing-test-exits.json"
git commit -m 'wip(furniture): persist serial round closing Python exits'
