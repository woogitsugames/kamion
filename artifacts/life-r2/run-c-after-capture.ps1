$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
function Save-Step([string]$Label,[string]$Detail,[string[]]$Files=@()){
 if((git branch --show-current).Trim() -ne 'gpt-life-r2'){throw 'Wrong branch'}
 Add-Content artifacts/life-r2/STATUS.md ("`nIteracja C ({0}): {1}" -f (Get-Date -Format o),$Detail)
 git add -f -- artifacts/life-r2/STATUS.md @Files
 if($LASTEXITCODE -ne 0){throw 'Staging failed'}
 git commit -m "wip(life): $Label"
 if($LASTEXITCODE -ne 0){throw 'Checkpoint failed'}
}
$phase='capture-c';$code=1
try {
 $jobs=@(Get-CimInstance Win32_Process -Filter "Name='pwsh.exe'"|Where-Object {$_.CommandLine -like '*-File artifacts/life-r2/capture-exact.ps1 -Stage after-c-exact*'})
 if($jobs.Count -gt 1){throw 'Multiple C capture processes'}
 if($jobs.Count -eq 1){Wait-Process -Id $jobs[0].ProcessId -ErrorAction SilentlyContinue}
 $inputProof=Get-Content artifacts/life-r2/after-c-exact-inputs.json -Raw|ConvertFrom-Json
 foreach($p in $inputProof.source_sha.PSObject.Properties){if((Get-FileHash -LiteralPath $p.Name).Hash -ne $p.Value){throw "Changed C source: $($p.Name)"}}
 if((Get-FileHash art-source/world/props/street_props.glb).Hash -ne $inputProof.library_sha){throw 'Changed C library'}
 & uv run --project tools/worldgen python artifacts/life-r2/validate-native-b.py c
 if($LASTEXITCODE -ne 0){throw 'Native C validation failed'}
 & uv run --project tools/worldgen python artifacts/life-r2/compare-exact.py before-exact after-c-exact exact-c
 if($LASTEXITCODE -ne 0){throw 'C exact comparison failed'}
 Save-Step 'potwierdź 456 renderów i natywny budżet C' 'Capture C, siedem SHA źródeł, natywny payload/materiały i wszystkie liczniki zweryfikowane. Brak odbioru wizualnego; następna kontrola plansz.' @('artifacts/life-r2/after-c-exact-inputs.json','artifacts/life-r2/native-c-validation.json','artifacts/life-r2/exact-c-all-camera-budget.json','artifacts/life-r2/exact-c-budget-summary.json')
 $phase='wait-compare-b'
 $result='artifacts/life-r2/compare-b-result.json'
 if(!(Test-Path $result)){
  $jobs=@(Get-CimInstance Win32_Process -Filter "Name='pwsh.exe'"|Where-Object {$_.CommandLine -like '*-File artifacts/life-r2/heavy.ps1 -Task Script -Tag compare-b *'})
  if($jobs.Count -ne 1){throw 'Cannot identify existing compare-b; do not overlap heavy jobs'}
  Wait-Process -Id $jobs[0].ProcessId -ErrorAction SilentlyContinue
 }
 if(!(Test-Path $result) -or (Get-Content $result -Raw|ConvertFrom-Json).exit_code -ne 0){throw 'Compare B unsuccessful'}
 Save-Step 'zachowaj plansze i kontrolę osobówek B' 'Compare B zakończony 0 pod heavy; wynik ramek osobówek w passenger-car-frame-check-b.json.' @('artifacts/life-r2/b-all-camera-budget.json','artifacts/life-r2/b-budget-summary.json','artifacts/life-r2/passenger-car-frame-check-b.json','artifacts/life-r2/compare-b-result.json')
 $phase='compare-c'
 & pwsh -NoProfile -File artifacts/life-r2/heavy.ps1 -Task Script -Tag compare-c -ScriptPath artifacts/life-r2/render-compare-b.py -ScriptArguments c
 if($LASTEXITCODE -ne 0){throw 'C image comparison failed'}
 Save-Step 'zapisz plansze i kontrolę osobówek C' 'Compare C zakończony 0 pod heavy. Następne: oględziny autora; jeśli C wybrany, pełny GIS i EditMode na koniec rundy. REPORT jeszcze nie powstał.' @('artifacts/life-r2/c-all-camera-budget.json','artifacts/life-r2/c-budget-summary.json','artifacts/life-r2/passenger-car-frame-check-c.json','artifacts/life-r2/compare-c-result.json')
 $phase='await-author-review';$code=0
} catch {
 Add-Content artifacts/life-r2/STATUS.md ("`nC przerwane na etapie {0}: {1}. Nie restartować generatora ani capture; sprawdzić konkretny etap." -f $phase,$_.Exception.Message)
 git add -f -- artifacts/life-r2/STATUS.md
 git commit -m "wip(life): zapisz przerwany etap C $phase"
 throw
} finally {
 @{phase=$phase;exit_code=$code;finished=(Get-Date -Format o)}|ConvertTo-Json|Set-Content artifacts/life-r2/post-c-result.json
}
