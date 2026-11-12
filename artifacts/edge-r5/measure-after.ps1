param([Parameter(Mandatory)][int]$AfterPid)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
while(Get-Process -Id $AfterPid -ErrorAction SilentlyContinue){Start-Sleep -Seconds 5}
if(-not(Test-Path "$PSScriptRoot/After.ready")){throw 'After stopped without frozen evidence; inspect its log'}
if((git branch --show-current).Trim() -ne 'gpt-edge-r5'){throw 'Wrong round'}
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:NUMEXPR_NUM_THREADS='1'
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
& pwsh -File $slot -Acquire -Pool heavy -Owner gpt-edge-r5 -PollSeconds 2 -StaleHours 100000
if($LASTEXITCODE -ne0){throw 'Measurement heavy acquisition failed'}
$acquired=Get-Date -Format o
$code=99
try {
    foreach($script in @('compare.py','audit_appearance.py')){
        & uv run --project tools/worldgen python "$PSScriptRoot/$script" *> "$PSScriptRoot/$script.log"
        if($LASTEXITCODE -ne0){throw "$script failed; inspect before proceeding"}
    }
    & uv run --project tools/worldgen python "$PSScriptRoot/audit_mesh.py" after *> "$PSScriptRoot/audit-mesh-after.log"
    if($LASTEXITCODE -ne0){throw 'Imported apron audit failed'}
    & uv run --project tools/worldgen python -m pytest tests/gis/test_far_field.py -q --junitxml "$PSScriptRoot/tests/far-field-after.xml" *> "$PSScriptRoot/far-field-after.log"
    if($LASTEXITCODE -ne0){throw 'Generated far-field single-file test failed'}
    $code=0
} finally {
    & pwsh -File $slot -Release -Pool heavy -Owner gpt-edge-r5 -StaleHours 100000
    @{owner='gpt-edge-r5';pool='heavy';acquired=$acquired;finished=(Get-Date -Format o);exit_code=$code} |
        ConvertTo-Json | Set-Content "$PSScriptRoot/after-measurements-receipt.json"
}
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Ukończono pod jednym szeregowym heavy porównanie obu macierzy, audyt surowych/Unity buforów i apron oraz pojedynczy test wygenerowanych far-field. Wyniki w JSON/CSV/logach; ocena wizualna nadal wymagana przed GIS na koniec rundy."
git add -f artifacts/edge-r5/STATUS.md artifacts/edge-r5/after-measurements-receipt.json artifacts/edge-r5/appearance-geometry-audit.json artifacts/edge-r5/all-cameras.csv artifacts/edge-r5/measurements.json
git commit -m 'WIP edge r5: measure all captures and generated imported geometry'
if($LASTEXITCODE -ne0){throw 'Measurement checkpoint failed'}
(Get-Date -Format o)|Set-Content "$PSScriptRoot/Measurements.ready"
