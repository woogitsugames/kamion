param([Parameter(Mandatory)][int]$WaitFor)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r4'){throw 'Wrong branch'}
$running=Get-CimInstance Win32_Process -Filter "ProcessId=$WaitFor"
if($running){
 if($running.Name -ne 'pwsh.exe' -or $running.CommandLine -notmatch ' -NoProfile -File artifacts/life-r4/final-editmode\.ps1$'){throw 'Wait target is not our EditMode'}
 Wait-Process -Id $WaitFor -ErrorAction SilentlyContinue
}
$edit=Get-Content artifacts/life-r4/final-editmode-result.json -Raw|ConvertFrom-Json
if($edit.exit_code -ne 0 -or $edit.failed -ne 0){throw 'Inspect terminal EditMode before GIS'}
. artifacts/life-r4/assert-selected.ps1
if(Test-Path artifacts/life-r4/final-gis.log){throw 'GIS evidence exists'}
if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/gpt-life-r4.slot'){throw 'Own heavy already held'}
& pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner gpt-life-r4 -StaleHours 1000000 -PollSeconds 1
if($LASTEXITCODE){throw 'Acquire failed'}
$phase='focused-tests';$code=1
function Save-Step([string]$message,[string[]]$files=@()){
 Add-Content artifacts/life-r4/STATUS.md ("`nKońcowy heavy ({0}): {1}. Następny krok: odczyt rzeczywistych wyników, ADR/REPORT i kopia, potem r5 palety." -f (Get-Date -Format o),$message)
 git add -f artifacts/life-r4/STATUS.md @files
 git commit -m "wip(life): $message"
 if($LASTEXITCODE){throw 'WIP failed'}
}
try {
 Assert-LifeSelected
 foreach($file in @('test_streetscape','test_world_v31')){
  & uv run --project tools/worldgen python -m pytest "tests/gis/$file.py" -q *> "artifacts/life-r4/final-$file.log"
  if($LASTEXITCODE){throw "Inspect changed test file: $file"}
 }
 Save-Step 'sprawdź oba pliki lokalnych budżetów po pomiarach trasy' @('artifacts/life-r4/final-test_streetscape.log','artifacts/life-r4/final-test_world_v31.log')
 $phase='gis'
 & uv run --project tools/worldgen python -m pytest tests/gis -q *> artifacts/life-r4/final-gis.log
 $gis=$LASTEXITCODE
 Assert-LifeSelected
 @{exit_code=$gis;finished=(Get-Date -Format o);source_capture=$lifeSelection.source_capture}|ConvertTo-Json|Set-Content artifacts/life-r4/final-gis-result.json
 Save-Step 'zapisz końcowy GIS kół placowych' @('artifacts/life-r4/final-gis.log','artifacts/life-r4/final-gis-result.json')
 if($gis){throw 'Final GIS failed'}
 $phase='proof'
 & uv run --project tools/worldgen python artifacts/life-r4/source-proof.py final-after-tests *> artifacts/life-r4/final-source-proof.log
 if($LASTEXITCODE){throw 'Final source proof failed'}
 & uv run --project tools/worldgen python artifacts/life-r4/audit-wheel-scope.py final *> artifacts/life-r4/final-scope.log
 if($LASTEXITCODE){throw 'Final wheel scope failed'}
 & pwsh -NoProfile -File artifacts/life-r4/validate-native-materials.ps1 -Tag final-heavy *> artifacts/life-r4/final-native-materials.log
 if($LASTEXITCODE){throw 'Final native materials changed'}
 Assert-LifeSelected
 Save-Step 'potwierdź zamrożone koła, bieżnik, raw i materiały po testach' @('artifacts/life-r4/final-after-tests-source-proof.json','artifacts/life-r4/final-wheel-scope.json','artifacts/life-r4/final-heavy-native-materials.json')
 $phase='complete';$code=0
} catch {
 Save-Step "zapisz przerwany końcowy heavy $phase"
 throw
} finally {
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool heavy -Owner gpt-life-r4
 @{phase=$phase;exit_code=$code;finished=(Get-Date -Format o)}|ConvertTo-Json|Set-Content artifacts/life-r4/final-heavy-result.json
}
