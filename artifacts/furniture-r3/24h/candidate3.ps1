$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r3/24h'
$owner=(& git branch --show-current).Trim()
if($owner -ne 'gpt-furniture-r3'){throw 'Wrong round branch'}
if(!(Select-String -LiteralPath "$ev/shelter-material-probe-candidate3sky.log" -SimpleMatch '18 total, 18 passed, 0 failed, 0 skipped')){throw 'Actual GPU/factory/sky contracts have not passed'}
$sourceFiles=@('tools/worldgen/streetscape/props.py','tools/worldgen/streetscape/materials.py','tools/worldgen/streetscape/furniture.py','tools/worldgen/streetscape/fab_details.py','game/Assets/_Project/Rendering/Shaders/WorldSurface.shader','game/Assets/_Project/World/Import/WorldPbrMaterials.cs','game/Assets/_Project/Editor/Furniture/FurnitureShelterPolicySave.cs')
$fingerprint=@{}
foreach($file in $sourceFiles){$fingerprint[$file]=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash}
$fingerprint|ConvertTo-Json|Set-Content "$ev/candidate3-source-fingerprint.json"
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$acquired=$false
for($attempt=1;$attempt -le 3;$attempt++){
    & pwsh $slot -Acquire -Pool heavy -Owner $owner -StaleHours 876000 -PollSeconds 1
    if($LASTEXITCODE -eq 0){$acquired=$true;break}
    # Retry only after a terminal Acquire error, e.g. the observed queue-file sharing race.
    if($attempt -lt 3){Start-Sleep -Seconds 1}
}
if(!$acquired){throw 'Heavy acquisition failed; no Python job was started'}
$ok=$false
$stage='source verification'
function Checkpoint([string]$message,[string[]]$evidence){
    Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): $message"
    Copy-Item "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md
    git add -f "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md
    if($evidence.Count){git add -f -- $evidence}
    git commit -m "wip(furniture): candidate3 $stage checkpoint" --quiet
}
try{
    foreach($file in $sourceFiles){if((Get-FileHash -LiteralPath $file).Hash -ne $fingerprint[$file]){throw "Frozen source changed while queued: $file"}}
    $stage='focused geometry contracts'
    & uv run --project tools/worldgen python -m pytest tests/gis/test_furniture_shelters_0120.py -q *> "$ev/pytest-shelters-candidate3.log"
    if($LASTEXITCODE -ne 0){throw 'Shelter geometry contracts failed'}
    Checkpoint 'Focused test geometrii/palety przeszedł w heavy. Następny etap to generator w tym samym slocie, bez równoległego Pythona.' @("$ev/pytest-shelters-candidate3.log","$ev/candidate3-source-fingerprint.json")
    $stage='world after3'
    [ordered]@{phase='after3';head=(& git rev-parse HEAD);started_at=(Get-Date -Format o);owner=$owner;pool='heavy'}|ConvertTo-Json|Set-Content "$ev/world-context-after3.json"
    & uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$ev/build-after3.log"
    if($LASTEXITCODE -ne 0){throw 'Candidate3 world failed'}
    Checkpoint 'Generator after3 zakończony. Slot nadal obejmuje wyłącznie sekwencyjny skan chronionej geometrii, nie Unity.' @("$ev/build-after3.log","$ev/world-context-after3.json")
    $stage='protected geometry after3'
    & uv run --project tools/worldgen python "$ev/snapshot_geometry.py" after *> "$ev/geometry-after3.log"
    if($LASTEXITCODE -ne 0){throw 'Protected payloads changed'}
    & uv run --project tools/worldgen python "$ev/audit_shelter_instances.py" after *> "$ev/instances-after3.log"
    if($LASTEXITCODE -ne 0){throw 'Instance identity changed'}
    $ok=$true
}finally{
    & pwsh $slot -Release -Pool heavy -Owner $owner
    Checkpoint "Pakiet heavy candidate3 zakończony; etap=$stage, sukces=$ok, slot zwolniony. Następny krok: normalny import i faktyczne pomiary, bez deklaracji budżetu z liczby slotów." @("$ev/candidate3.ps1")
}
if(!$ok){throw 'Candidate3 heavy batch incomplete'}
& pwsh "$ev/unity-step.ps1" -Step import -Phase candidate3
if($LASTEXITCODE -ne 0){throw 'Candidate3 import failed'}
& uv run --project tools/worldgen python "$ev/audit_shelter_policy.py" after3 *> "$ev/shelter-policy-after3.log"
if($LASTEXITCODE -ne 0){throw 'Candidate3 family visibility audit failed'}
& pwsh "$ev/candidate2.ps1" -Phase after3
if($LASTEXITCODE -ne 0){throw 'Candidate3 captures or counters failed'}
