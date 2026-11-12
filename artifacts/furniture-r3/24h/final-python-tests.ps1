$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r3/24h'
$owner=(& git branch --show-current).Trim()
if($owner -ne 'gpt-furniture-r3'){throw 'Wrong round branch'}
# Invoke manually only after the final visual review; never race the same-owner consumers.
$other=@(Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -match 'furniture-r3/24h/(candidate3|review-sheets|photo-shelter-captures)\.ps1'
})
if($other.Count){throw 'Candidate or dependent consumers are still running'}
$budget=@(Get-Content "$ev/iteration3/frame-budget.json" -Raw|ConvertFrom-Json)
$low=@($budget|Where-Object tier -eq 'Low')
if($budget.Count -ne 236 -or $low.Count -ne 118){throw 'Final frame coverage incomplete'}
if(@($low|Where-Object {$_.total_draw_delta -gt 0 -or $null -eq $_.tris_delta_exact_percent -or $_.tris_delta_exact_percent -gt 2}).Count){
    throw 'Final Low budget is not proven; continue the quality loop before end-of-round tests'
}
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$acquired=$false
for($attempt=1;$attempt -le 3;$attempt++){
    & pwsh $slot -Acquire -Pool heavy -Owner $owner -StaleHours 876000 -PollSeconds 10
    if($LASTEXITCODE -eq 0){$acquired=$true;break}
    if($attempt -lt 3){Start-Sleep -Seconds 1}
}
if(!$acquired){throw 'Heavy acquisition failed; no final tests started'}
$result=[ordered]@{head=(& git rev-parse HEAD);owner=$owner;pool='heavy';started_at=(Get-Date -Format o);gis_exit=$null;physics_gate3_exit=$null}
function Checkpoint([string]$message){
    Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): $message"
    Copy-Item "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md
    $result|ConvertTo-Json|Set-Content "$ev/final-python-results.json"
    git add -f "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md "$ev/final-python-results.json" "$ev/final-python-tests.ps1"
    foreach($file in @('pytest-gis-final.log','pytest-physics-gate3.log','pytest-gis-final.xml','pytest-physics-gate3.xml')){
        if(Test-Path "$ev/$file"){git add -f "$ev/$file"}
    }
    git commit -m 'wip(furniture): checkpoint end-of-round Python validation' --quiet
}
try{
    # Preserve the verified product before pytest fixtures can rewrite manifest paths.
    Copy-Item Data/Regions/bialystok-industrial-c/generated/world_manifest.json "$ev/manifest-verified-before-final-tests.json"
    & uv run --project tools/worldgen python -m pytest tests/gis -q --junitxml="$ev/pytest-gis-final.xml" *> "$ev/pytest-gis-final.log"
    $result.gis_exit=$LASTEXITCODE
    Checkpoint "Końcowy pełny GIS zakończony, exit=$($result.gis_exit). Nie zmienia to oceny renderów; następnie fizyka/gate3 sekwencyjnie w tym samym heavy."
    & uv run --project tools/worldgen python -m pytest tests/physics tests/gate3 -q --junitxml="$ev/pytest-physics-gate3.xml" *> "$ev/pytest-physics-gate3.log"
    $result.physics_gate3_exit=$LASTEXITCODE
}finally{
    & pwsh $slot -Release -Pool heavy -Owner $owner
    $result.finished_at=Get-Date -Format o
    Checkpoint "Końcowy pakiet Python zakończony, heavy zwolniony. GIS exit=$($result.gis_exit), physics/gate3 exit=$($result.physics_gate3_exit). NASTĘPNY KROK: odczytać rzeczywiste wyniki, sprawdzić skutki uboczne fixture i testy Unity."
}
if($result.gis_exit -ne 0 -or $result.physics_gate3_exit -ne 0){throw 'Inspect actual end-of-round failures; do not report PASS'}
