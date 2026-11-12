param([ValidatePattern('^[a-z0-9-]+$')][string]$Tag='final',[switch]$SkipImages,[switch]$RefreshFidelity)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$owner=(git branch --show-current).Trim()
if($owner -ne 'gpt-life-r3'){throw 'Wrong branch'}
$selection=Get-Content artifacts/life-r3/C-SELECTED.json -Raw|ConvertFrom-Json
if(!$selection.selected){throw 'Inspect and select C before end-of-round tests'}
$proof=Get-Content artifacts/life-r3/after-c-inputs.json -Raw|ConvertFrom-Json
function Assert-Frozen {
 foreach($p in $proof.source_sha.PSObject.Properties){if((Get-FileHash $p.Name).Hash -ne $p.Value){throw "C source changed: $($p.Name)"}}
 if((Get-FileHash art-source/world/props/street_props.glb).Hash -ne $proof.library_sha){throw 'C library changed'}
 if((Get-FileHash art-source/world/props/props_meta.json).Hash -ne $proof.meta_sha){throw 'C metadata changed'}
 if((Get-FileHash artifacts/life-r3/cameras.json).Hash -ne $proof.cameras_sha){throw 'C cameras changed'}
}
function Save-Step([string]$Message,[string[]]$Files=@()) {
 Add-Content artifacts/life-r3/STATUS.md ("`nKońcowy heavy ({0}): {1}. Następny krok: odczyt wyników, oględziny pełnych plansz, EditMode, REPORT/kopia, potem r4." -f (Get-Date -Format o),$Message)
 git add -f -- artifacts/life-r3/STATUS.md @Files
 git commit -m "wip(life): $Message"
 if($LASTEXITCODE){throw 'WIP failed'}
}
Assert-Frozen
$prefix="artifacts/life-r3/$Tag"
if(Test-Path "$prefix-gis.log"){throw 'Evidence already exists'}
if($SkipImages -and !(Test-Path artifacts/life-r3/final-c-images-budget-summary.json)){throw 'Original image evidence missing'}
if($RefreshFidelity) {
 $prior=Get-Content artifacts/life-r3/final-heavy-result.json -Raw|ConvertFrom-Json
 $failure=Get-Content artifacts/life-r3/final-gis.log -Raw
 if($prior.phase -ne 'gis' -or $prior.exit_code -ne 1 -or $failure -notmatch '1 failed,' -or $failure -notmatch 'test_report_not_stale'){throw 'Inspect the actual GIS failure before refreshing fidelity'}
}
if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/$owner.slot"){throw 'Own heavy already held'}
& pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $owner -StaleHours 1000000 -PollSeconds 1
if($LASTEXITCODE){throw 'Acquire failed'}
$phase='images';$code=1
try {
 Assert-Frozen
 if(!$SkipImages) {
  & uv run --project tools/worldgen python artifacts/life-r3/compare.py --before before --after after-c --tag "$Tag-c-images" --exact --all-cameras *> "$prefix-images.log"
  if($LASTEXITCODE){throw 'Full image pages failed'}
  Save-Step 'przygotuj wszystkie pary obrazów C do kontroli' @("$prefix-c-images-all-camera-budget.json","$prefix-c-images-budget-summary.json")
 }
 if($RefreshFidelity) {
  $phase='fidelity'
  Copy-Item Data/Regions/bialystok-industrial-c/generated/fidelity_qa.json "$prefix-fidelity-before.json"
  & uv run --project tools/worldgen python -u tools/worldgen/fidelity/run.py --region bialystok-industrial-c --art "$prefix-fidelity" *> "$prefix-fidelity.log"
  if($LASTEXITCODE){throw 'Fidelity refresh failed'}
  git add Data/Regions/bialystok-industrial-c/generated/fidelity_qa.json
  Save-Step 'odśwież raport fidelity po dołączeniu main' @("$prefix-fidelity/fidelity_summary.json")
  & uv run --project tools/worldgen python -m pytest tests/gis/test_road_fidelity.py -q *> "$prefix-test-road-fidelity.log"
  if($LASTEXITCODE){throw 'Refreshed fidelity test failed'}
  Assert-Frozen
  Save-Step 'sprawdź pojedynczy test odświeżonego fidelity' @("$prefix-test-road-fidelity.log")
 }
 $phase='gis'
 & uv run --project tools/worldgen python -m pytest tests/gis -q *> "$prefix-gis.log"
 $gisCode=$LASTEXITCODE
 Assert-Frozen
 @{exit_code=$gisCode;source_capture='after-c-inputs.json';finished=(Get-Date -Format o)}|ConvertTo-Json|Set-Content "$prefix-gis-result.json"
 Save-Step 'zapisz końcowy GIS osobówek C' @("$prefix-gis.log","$prefix-gis-result.json")
 if($gisCode){throw 'Final GIS failed'}
 $phase='proof'
 & uv run --project tools/worldgen python artifacts/life-r3/source-proof.py "$Tag-after-tests" *> "$prefix-after-tests-proof.log"
 if($LASTEXITCODE){throw 'Post-test source proof failed'}
 & pwsh -NoProfile -File artifacts/life-r3/validate-native-b.ps1 *> "$prefix-native-materials.log"
 if($LASTEXITCODE){throw 'Post-test native material contract failed'}
 Assert-Frozen
 Save-Step 'potwierdź zamrożone wejścia C po GIS' @("$prefix-after-tests-source-proof.json")
 $phase='complete';$code=0
} catch {
 Save-Step "zapisz przerwany końcowy heavy $phase" @()
 throw
} finally {
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool heavy -Owner $owner
 @{phase=$phase;exit_code=$code;finished=(Get-Date -Format o);source_commit=(git rev-parse HEAD)}|ConvertTo-Json|Set-Content "$prefix-heavy-result.json"
}
