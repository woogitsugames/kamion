param([ValidatePattern('^[a-z0-9-]+$')][string]$Tag='pytest-gis-final')
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$owner=(git branch --show-current).Trim()
if($owner -ne 'gpt-life-r2'){throw 'Wrong branch'}
$selection=Get-Content artifacts/life-r2/C-SELECTED.json -Raw|ConvertFrom-Json
if(!$selection.selected){throw 'Author must choose frozen C before final GIS'}
$proof=Get-Content artifacts/life-r2/after-c-exact-inputs.json -Raw|ConvertFrom-Json
function Assert-Frozen {
 foreach($p in $proof.source_sha.PSObject.Properties){if((Get-FileHash -LiteralPath $p.Name).Hash -ne $p.Value){throw "Changed C source: $($p.Name)"}}
 if((Get-FileHash art-source/world/props/street_props.glb).Hash -ne $proof.library_sha){throw 'Changed C GLB'}
 if((Get-FileHash art-source/world/props/props_meta.json).Hash -ne $proof.meta_sha){throw 'Changed C metadata'}
}
Assert-Frozen
$log="artifacts/life-r2/$Tag.log"
$resultPath="artifacts/life-r2/$Tag-result.json"
if(Test-Path $log){throw 'Final GIS evidence exists; inspect instead of overwriting'}
if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/$owner.slot"){throw 'Do not overlap own heavy jobs'}
& pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $owner -StaleHours 1000000 -PollSeconds 1
if($LASTEXITCODE -ne 0){throw 'Heavy acquire failed'}
$code=1
try {
 & uv run --project tools/worldgen python -m pytest tests/gis -q *> $log
 $code=$LASTEXITCODE
 Assert-Frozen
 if($code -eq 0){
  & uv run --project tools/worldgen python artifacts/life-r2/validate-native-b.py c *> artifacts/life-r2/native-c-post-tests.log
  if($LASTEXITCODE -ne 0){$code=$LASTEXITCODE}
 }
} catch {
 $code=1
 throw
} finally {
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool heavy -Owner $owner
 @{exit_code=$code;owner=$owner;pool='heavy';finished=(Get-Date -Format o);selection='C';source_capture='after-c-exact-inputs.json';log=$log}|ConvertTo-Json|Set-Content $resultPath
 Add-Content artifacts/life-r2/STATUS.md ("`nKońcowy GIS ({0}) zakończony kodem {1}, heavy zwolnione. Liczby w {2}; REPORT i kopia do main dopiero po sprawdzeniu wyniku. Następny krok: odczytać log/wynik, uzupełnić ADR i REPORT, robocopy artefaktów bez .cache, następnie gpt-life-r3 i git merge main do własnej gałęzi." -f (Get-Date -Format o),$code,$log)
 git add -f -- artifacts/life-r2/STATUS.md $log $resultPath
 git commit -m "wip(life): zapisz końcowy GIS zamrożonego wariantu C"
}
if($code -ne 0){throw "Final GIS/guard failed: $code"}
