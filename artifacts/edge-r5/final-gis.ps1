# Call only once the measured and visual reviews are complete. This script does
# not scope or accept generated outputs: inspect failures and hashes afterward.
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-edge-r5'){throw 'Wrong round'}
foreach($marker in @('After.ready','Measurements.ready')){
    if(-not(Test-Path "$PSScriptRoot/$marker")){throw "Required: $marker"}
}
$budget=Get-Content "$PSScriptRoot/budget-summary.json" -Raw|ConvertFrom-Json
if($budget.pairs -ne472 -or $budget.low_pairs -ne236 -or @($budget.low_failures).Count){throw 'All measured Low budgets must pass first'}
$edit=Get-Content "$PSScriptRoot/editmode-result.json" -Raw|ConvertFrom-Json
if($edit.result -ne 'Passed' -or $edit.failed -ne0 -or $edit.passed -ne340){throw 'Expected verified EditMode'}
$review=Get-Content "$PSScriptRoot/visual-review.json" -Raw|ConvertFrom-Json
if(@($review.observed_hall_pairs).Count -ne4 -or -not$review.native_observations){throw 'Actual image review required'}
$files=[ordered]@{}
foreach($name in @('far_field.glb','far_field.low.glb','far_field_apron.json','far_field_gis_cache.json')){
    $files["Data/raw/derived/bialystok-industrial-c/world/$name"]="$PSScriptRoot/after-source/$name"
}
$files['Data/Regions/bialystok-industrial-c/generated/far_field_qa.json']="$PSScriptRoot/after-far-field-qa.json"
$files['Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json']="$PSScriptRoot/after-far-field-source-manifest.json"
$before=[ordered]@{}
foreach($path in $files.Keys){
    $hash=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    if($hash -ne (Get-FileHash -LiteralPath $files[$path] -Algorithm SHA256).Hash){throw "Own output differs from rendered After: $path"}
    $before[$path]=$hash
}
Copy-Item Data/Regions/bialystok-industrial-c/generated/world_manifest.json "$PSScriptRoot/pre-gis-world-manifest.json"
$before|ConvertTo-Json|Set-Content "$PSScriptRoot/pre-gis-own-sha.json"
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:NUMEXPR_NUM_THREADS='1'
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
& pwsh -File $slot -Acquire -Pool heavy -Owner gpt-edge-r5 -PollSeconds 2 -StaleHours 100000
if($LASTEXITCODE -ne0){throw 'Final GIS acquisition failed'}
$acquired=Get-Date -Format o
$code=99
try{
    & uv run --project tools/worldgen python -m pytest tests/gis -q --junitxml "$PSScriptRoot/tests/gis-final.xml" *> "$PSScriptRoot/gis-final.log"
    $code=$LASTEXITCODE
}finally{
    & pwsh -File $slot -Release -Pool heavy -Owner gpt-edge-r5 -StaleHours 100000
    @{owner='gpt-edge-r5';pool='heavy';task='GisFinal';acquired=$acquired;finished=(Get-Date -Format o);exit_code=$code}|
        ConvertTo-Json|Set-Content "$PSScriptRoot/gis-final-receipt.json"
}
Copy-Item Data/Regions/bialystok-industrial-c/generated/world_manifest.json "$PSScriptRoot/post-gis-world-manifest.json"
$after=[ordered]@{}
$unchanged=$true
foreach($path in $files.Keys){
    $after[$path]=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    if($after[$path] -ne $before[$path]){$unchanged=$false}
}
@{before=$before;after=$after;all_own_outputs_unchanged=$unchanged;pytest_exit_code=$code}|
    ConvertTo-Json -Depth 5|Set-Content "$PSScriptRoot/post-gis-own-integrity.json"
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Pełny GIS na końcu rundy ukończony pod heavy: exit=$code, własne pliki zgodne z After=$unchanged. Nie interpretować niezerowego exit jako PASS; szczegóły JUnit/log i SHA wymagają oceny przed scope/REPORT."
git add -f artifacts/edge-r5/STATUS.md artifacts/edge-r5/gis-final-receipt.json artifacts/edge-r5/pre-gis-own-sha.json artifacts/edge-r5/post-gis-own-integrity.json
git commit -m 'WIP edge r5: preserve complete final GIS result and own output integrity'
if($LASTEXITCODE -ne0){throw 'Final GIS checkpoint failed'}
if(-not$unchanged){throw 'GIS changed rendered edge outputs; do not scope or deliver before investigation'}
(Get-Date -Format o)|Set-Content "$PSScriptRoot/Gis.finished"
exit $code
