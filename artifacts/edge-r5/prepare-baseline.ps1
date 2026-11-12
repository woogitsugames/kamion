$ErrorActionPreference='Stop'
$env:OMP_NUM_THREADS='1';$env:OPENBLAS_NUM_THREADS='1';$env:MKL_NUM_THREADS='1';$env:NUMEXPR_NUM_THREADS='1'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $root
$owner=(git branch --show-current).Trim()
if($owner -ne 'gpt-edge-r5'){throw 'Wrong round'}
$main='C:/Users/matma/Documents/Claude/kamion'
foreach($relative in @('Data/raw/cc0','art-source/world/cc0/_raw','art-source/world/megascans','Data/photos/nowe')){
    if(-not(Test-Path (Join-Path $main $relative))){throw "Missing source cache: $relative"}
    & robocopy (Join-Path $main $relative) (Join-Path $root $relative) /E /XJ /MT:1 /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
    if($LASTEXITCODE -ge 8){throw "Cache copy failed: $relative"}
}
function Save-Step([string]$message){
    Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) $message"
    git add -f artifacts/edge-r5/STATUS.md
    git commit -m "WIP edge r5: $message"
    if($LASTEXITCODE -ne 0){throw 'Checkpoint failed'}
}
Save-Step 'Odświeżono niezmienne cache i wejściowe fotografie materiałów; nie kopiowano aktywnych derived/scen main.'
$slot=Join-Path $main 'scripts/unity-slot.ps1'
$codes=@{Materials=0;World=1}
$started=Get-Date -Format o
foreach($task in @('World')){
    & pwsh -File $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 1 -StaleHours 100000
    if($LASTEXITCODE -ne 0){throw "Heavy acquisition failed: $task"}
    $acquired=Get-Date -Format o
    try{
        $env:PYTHONUNBUFFERED='1'
        if($task -eq 'Materials'){
            & uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py *> "$PSScriptRoot/build-materials.log"
        }else{
            & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$PSScriptRoot/build-world-baseline.log"
        }
        $codes[$task]=$LASTEXITCODE
        if($codes[$task] -ne 0){throw "Baseline $task failed: $($codes[$task])"}
    }finally{
        & pwsh -File $slot -Release -Pool heavy -Owner $owner -StaleHours 100000
        @{task=$task;owner=$owner;pool='heavy';acquired=$acquired;finished=(Get-Date -Format o);exit_code=$codes[$task]}|
            ConvertTo-Json|Set-Content "$PSScriptRoot/baseline-$task-receipt.json"
    }
    Save-Step "Zakończono bazowy $task pod osobnym slotem heavy; źródła innych dziedzin bez edycji."
}
if(Select-String -LiteralPath "$PSScriptRoot/build-world-baseline.log" -SimpleMatch 'fallback=True' -Quiet){throw 'Megascans fallback detected'}
Copy-Item Data/Regions/bialystok-industrial-c/generated/world_manifest.json "$PSScriptRoot/baseline-operational-world-manifest.json"
@{owner=$owner;pool='heavy';started=$started;finished=(Get-Date -Format o);materials_exit_code=$codes.Materials;world_exit_code=$codes.World}|
    ConvertTo-Json|Set-Content "$PSScriptRoot/baseline-preparation-receipt.json"
Save-Step 'Świat bazowy r5 gotowy bez fallback=True; następnie import Low/High i pełne Before, bez nowej zmiany produkcyjnej.'
