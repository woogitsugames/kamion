$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-edge-r6'){throw 'Wrong round'}
foreach($marker in @('Baseline.ready','After.ready','ContactBefore.ready','OwnershipDiagnostics.ready')){
    if(-not(Test-Path "$PSScriptRoot/$marker")){throw "Required evidence missing: $marker"}
}
if(Test-Path "$PSScriptRoot/Measurements.ready"){throw 'Measurements already frozen; preserve before a deliberate new attempt'}
$env:OMP_NUM_THREADS='1';$env:OPENBLAS_NUM_THREADS='1';$env:MKL_NUM_THREADS='1';$env:NUMEXPR_NUM_THREADS='1'
& pwsh -File "$PSScriptRoot/acquire-slot.ps1" -Pool heavy -Owner gpt-edge-r6
if($LASTEXITCODE -ne0){throw 'Measurement heavy acquisition failed'}
$acquired=Get-Date -Format o
$code=99
$sources=@{};foreach($name in @('compare.py','audit_round_geometry.py','audit_mesh.py','audit_contact.py','segment_contact.py','unity_mesh_audit.py')){
    $sources[$name]=(Get-FileHash "$PSScriptRoot/$name" -Algorithm SHA256).Hash
}
try{
    foreach($name in @('compare.py','audit_round_geometry.py')){
        & uv run --project tools/worldgen python "$PSScriptRoot/$name" *> "$PSScriptRoot/$name.log"
        if($LASTEXITCODE -ne0){throw "Measurement failed: $name"}
    }
    foreach($phase in @('before','after')){
        & uv run --project tools/worldgen python "$PSScriptRoot/audit_mesh.py" $phase *> "$PSScriptRoot/audit-mesh-$phase.log"
        if($LASTEXITCODE -ne0){throw "Asphalt clearance failed: $phase"}
    }
    & uv run --project tools/worldgen python "$PSScriptRoot/audit_contact.py" after *> "$PSScriptRoot/contact-after.log"
    if($LASTEXITCODE -ne0){throw 'Actual After contact audit failed'}
    foreach($name in $sources.Keys){if((Get-FileHash "$PSScriptRoot/$name" -Algorithm SHA256).Hash -ne $sources[$name]){throw 'Audit source drifted'}}
    $code=0
}finally{
    & pwsh -File 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1' -Release -Pool heavy -Owner gpt-edge-r6 -StaleHours 100000
    @{owner='gpt-edge-r6';pool='heavy';acquired=$acquired;finished=(Get-Date -Format o);exit_code=$code;audit_sources_sha256=$sources}|
        ConvertTo-Json -Depth 5|Set-Content "$PSScriptRoot/after-measurements-receipt.json"
}
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Ukończono rzeczywisty pomiar obu macierzy, niezależność far-field/buforów, zakres przesunięcia pierścienia, prześwit wszystkich trójkątów stuba w obu fazach i pełne dolne krawędzie kurtyn After. Wszystko pod jednym szeregowym heavy, bez pełnego GIS w trakcie rundy; ocena obrazu nadal wymagana."
git add -f artifacts/edge-r6/STATUS.md artifacts/edge-r6/after-measurements-receipt.json artifacts/edge-r6/round-geometry-audit.json artifacts/edge-r6/budget-summary.json artifacts/edge-r6/contact-after.json artifacts/edge-r6/mesh-clearance-before.json artifacts/edge-r6/mesh-clearance-after.json artifacts/edge-r6/all-cameras.csv
git commit -m 'WIP edge r6: measure actual ring geometry contact and complete capture budgets'
if($LASTEXITCODE -ne0){throw 'Measurement checkpoint failed'}
(Get-Date -Format o)|Set-Content "$PSScriptRoot/Measurements.ready"
(Get-Date -Format o)|Set-Content "$PSScriptRoot/ContactAfter.ready"
