param([Parameter(Mandatory)][int]$WaitFor,[ValidatePattern('^[a-z0-9-]+$')][string]$Tag='a1')
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r4'){throw 'Wrong branch'}
$running=Get-CimInstance Win32_Process -Filter "ProcessId=$WaitFor"
if($running){
 if($running.Name -ne 'pwsh.exe' -or $running.CommandLine -notmatch " -NoProfile -File artifacts/life-r4/candidate-gen\.ps1 -Tag $Tag`$"){throw 'Wait target is not our candidate'}
 Wait-Process -Id $WaitFor -ErrorAction SilentlyContinue
}
$prefix="artifacts/life-r4/$Tag"
$done=Get-Content "$prefix-gen-result.json" -Raw|ConvertFrom-Json
if($done.phase -ne 'complete' -or $done.exit_code -ne 0){throw 'Inspect terminal candidate result before import'}
$proofPath="$prefix-generated-source-proof.json"
$proof=Get-Content $proofPath -Raw|ConvertFrom-Json
$baseline=Get-Content artifacts/life-r4/before-inputs.json -Raw|ConvertFrom-Json
foreach($entry in $baseline.source_sha.PSObject.Properties){
 if($entry.Name -ne 'tools/worldgen/streetscape/life_props.py' -and $proof.source_sha.($entry.Name) -ne $entry.Value){throw "Unrelated baseline source changed: $($entry.Name)"}
}
function Assert-Frozen {
 foreach($map in @($proof.source_sha,$proof.prepared_medium_textures,$proof.fixtures)){
  foreach($entry in $map.PSObject.Properties){if((Get-FileHash $entry.Name).Hash -ne $entry.Value){throw "Candidate input changed: $($entry.Name)"}}
 }
 if((Get-FileHash artifacts/life-r4/cameras.json).Hash -ne $baseline.cameras_sha){throw 'Camera packet changed'}
}
function Save-Step([string]$message,[string[]]$files=@()){
 Add-Content artifacts/life-r4/STATUS.md ("`nPo kandydacie {0} ({1}): {2}. Następny krok: oględziny przed decyzją, bez deklaracji finalnego PASS." -f $Tag,(Get-Date -Format o),$message)
 git add -f artifacts/life-r4/STATUS.md artifacts/life-r4/SOURCE-MODE.json @files
 git commit -m "wip(life): $message"
 if($LASTEXITCODE){throw 'WIP failed'}
}
$stage="after-$Tag";$phase='import';$code=1
if(Test-Path "artifacts/life-r4/$stage"){throw 'Candidate images already exist'}
try {
 Assert-Frozen
 & pwsh -NoProfile -File artifacts/life-r4/unity-phase.ps1 -Phase PreparedVerified -ProofPath $proofPath
 if($LASTEXITCODE){throw 'Candidate import failed'}
 Assert-Frozen
 $mode=Get-Content artifacts/life-r4/SOURCE-MODE.json -Raw|ConvertFrom-Json
 $mode.requires_reimport=$false
 $mode|ConvertTo-Json|Set-Content artifacts/life-r4/SOURCE-MODE.json
 Save-Step "zaimportuj geometrię felgi $Tag" @("$prefix-gen-result.json")
 $phase='capture'
 & pwsh -NoProfile -File artifacts/life-r4/capture-exact.ps1 -Stage $stage
 if($LASTEXITCODE){throw 'Candidate capture failed'}
 Assert-Frozen
 # Metadata only; no geometry, image decoding or pytest.
 & uv run --project tools/worldgen python artifacts/life-r4/validate_exact.py $stage *> "$prefix-validation.log"
 if($LASTEXITCODE){throw 'Candidate capture metadata mismatch'}
 Save-Step "potwierdź pełny capture felgi $Tag" @("artifacts/life-r4/$stage-inputs.json","artifacts/life-r4/$stage-validation.json")
 $phase='compare'
 if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/gpt-life-r4.slot'){throw 'Own heavy already held'}
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner gpt-life-r4 -StaleHours 1000000 -PollSeconds 1
 if($LASTEXITCODE){throw 'Comparison heavy unavailable'}
 try {
  Assert-Frozen
  & uv run --project tools/worldgen python artifacts/life-r4/compare.py --before before --after $stage --tag $Tag --exact --all-cameras *> "$prefix-compare.log"
  if($LASTEXITCODE){throw 'Candidate comparison failed'}
 } finally {
  & pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool heavy -Owner gpt-life-r4
 }
 Assert-Frozen
 $summary=Get-Content "$prefix-budget-summary.json" -Raw|ConvertFrom-Json
 $all=Get-Content "$prefix-all-camera-budget.json" -Raw|ConvertFrom-Json
 $expectedRoute=@((Get-Content artifacts/life-r4/route-camera-ids.json -Raw|ConvertFrom-Json).ids).Count
 $route=@{}
 foreach($condition in $summary.PSObject.Properties){
  $s=$condition.Value
  if($s.route_cameras -ne $expectedRoute -or $s.missing_route.Count -or $s.route_over_budget.Count -or $s.max_draw_delta -gt 0 -or $s.max_instance_draw_delta -gt 0){throw "Candidate budget failed: $($condition.Name)"}
  $rows=@($all.($condition.Name)|Where-Object is_route)
  $route[$condition.Name]=@{cameras=$rows.Count;max_tris_percent=($rows.total_tris_percent|Measure-Object -Maximum).Maximum}
 }
 @{conditions=$route;source_capture="$stage-inputs.json";all_camera_summary="$Tag-budget-summary.json"}|ConvertTo-Json -Depth 6|Set-Content "$prefix-route-budget.json"
 Save-Step "zapisz pełne budżety i pary felgi $Tag" @("$prefix-all-camera-budget.json","$prefix-budget-summary.json","$prefix-route-budget.json")
 $phase='await-author-inspection';$code=0
} catch {
 Save-Step "zapisz przerwany odbiór felgi $Tag na etapie $phase"
 throw
} finally {
 @{phase=$phase;exit_code=$code;finished=(Get-Date -Format o);source_capture="$stage-inputs.json"}|ConvertTo-Json|Set-Content "$prefix-post-result.json"
}
