$ErrorActionPreference='Stop'
$env:OMP_NUM_THREADS='1';$env:OPENBLAS_NUM_THREADS='1';$env:MKL_NUM_THREADS='1';$env:NUMEXPR_NUM_THREADS='1'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-edge-r5' -or -not(Test-Path "$PSScriptRoot/Baseline.ready")){throw 'Complete frozen r5 baseline required'}
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
& pwsh -File $slot -Acquire -Pool heavy -Owner gpt-edge-r5 -PollSeconds 1 -StaleHours 100000
if($LASTEXITCODE -ne0){throw 'Baseline checks acquisition failed'}
$code=99
try{
    & uv run --project tools/worldgen python "$PSScriptRoot/identify_hall.py"
    $code=$LASTEXITCODE
    @{task='IdentifyHall';owner='gpt-edge-r5';pool='heavy';exit_code=$code;finished=(Get-Date -Format o)}|
        ConvertTo-Json|Set-Content "$PSScriptRoot/hall-identification-receipt.json"
    if($code -ne0){throw 'Hall identification failed; no Red or production edits allowed'}
    Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Geometria C061 dopasowana pod heavy; wynik i nakładka gotowe do obejrzenia, to nie identyfikacja fotograficzna."
    git add -f artifacts/edge-r5/STATUS.md artifacts/edge-r5/hall-identification.json artifacts/edge-r5/hall-identification-receipt.json
    git commit -m 'WIP edge r5: identify source hall in frozen production geometry'
    if($LASTEXITCODE -ne0){throw 'Identification checkpoint failed'}
    (Get-Date -Format o)|Set-Content "$PSScriptRoot/Identification.ready"
    & pwsh -File "$PSScriptRoot/test-facade.ps1" -Phase Red -HeavyAlreadyHeld
    $code=$LASTEXITCODE
    if($code -ne0){throw 'Unexpected Red result; inspect the tests before editing production'}
}finally{
    & pwsh -File $slot -Release -Pool heavy -Owner gpt-edge-r5 -StaleHours 100000
    @{task='IdentifyThenRed';owner='gpt-edge-r5';pool='heavy';exit_code=$code;finished=(Get-Date -Format o)}|
        ConvertTo-Json|Set-Content "$PSScriptRoot/baseline-checks-receipt.json"
}
