$ErrorActionPreference='Continue'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r1/24h'
$results=[ordered]@{}
# Full GIS is intentionally run here, at round closure, after the visual candidate is frozen.
& pwsh "$ev/heavy-step.ps1" -Step gis -Phase final4
$results.gis=$LASTEXITCODE
& pwsh "$ev/heavy-step.ps1" -Step physics -Phase final4
$results.physics_gate3=$LASTEXITCODE
& pwsh "$ev/unity-step.ps1" -Step editmode -Phase final4
$results.editmode=$LASTEXITCODE
$results | ConvertTo-Json | Set-Content "$ev/closing-test-exits.json" -Encoding UTF8
Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): końcowe zestawy wykonane: GIS=$($results.gis), physics/gate3=$($results.physics_gate3), EditMode=$($results.editmode). NASTĘPNY KROK: odczytać pełne wyniki i każdą porażkę; nie utożsamiać samego wykonania z PASS."
Copy-Item "$ev/STATUS.md" artifacts/furniture-r1/STATUS.md
git add -f "$ev/STATUS.md" artifacts/furniture-r1/STATUS.md "$ev/closing-test-exits.json"
git commit -m 'wip(furniture): checkpoint round closing test exits'
if (@($results.Values | Where-Object {$_ -ne 0}).Count) { exit 1 }
exit 0
