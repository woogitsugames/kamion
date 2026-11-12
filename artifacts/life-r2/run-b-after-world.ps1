$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
function Save-Step([string]$Label,[string]$Detail,[string[]]$Evidence=@()) {
 if((git branch --show-current).Trim() -ne 'gpt-life-r2'){throw 'Wrong branch'}
 Add-Content artifacts/life-r2/STATUS.md ("`nIteracja B ({0}): {1} Następne etapy w run-b-after-world.ps1, REPORT po oględzinach i testach końcowych." -f (Get-Date -Format o),$Detail)
 git add -u -- Data/Regions/bialystok-industrial-c/generated art-source/world/props
 if($LASTEXITCODE -ne 0){throw 'Staging generated outputs failed'}
 git add -f -- artifacts/life-r2/STATUS.md @Evidence
 if($LASTEXITCODE -ne 0){throw 'Staging evidence failed'}
 git commit -m "wip(life): $Label"
 if($LASTEXITCODE -ne 0){throw 'WIP failed'}
}
function Heavy([string]$Task,[string]$Tag,[string]$Path='', [string[]]$Arguments=@()) {
 if($Task -eq 'Script'){& pwsh -NoProfile -File artifacts/life-r2/heavy.ps1 -Task Script -Tag $Tag -ScriptPath $Path -ScriptArguments @Arguments}
 elseif($Task -eq 'TestFile'){& pwsh -NoProfile -File artifacts/life-r2/heavy.ps1 -Task TestFile -Tag $Tag -TestPath $Path}
 else{throw 'Unexpected task'}
 if($LASTEXITCODE -ne 0){throw "Heavy failed: $Tag"}
}
$phase='wait-world';$code=1
try {
 $result='artifacts/life-r2/world-b-result.json'
 if(!(Test-Path -LiteralPath $result)){
  $jobs=@(Get-CimInstance Win32_Process -Filter "Name='pwsh.exe'" | Where-Object {$_.CommandLine -like '*-File artifacts/life-r2/heavy.ps1 -Task World -Tag world-b*'})
  if($jobs.Count -ne 1){throw 'Cannot identify existing world-b process; do not duplicate'}
  Wait-Process -Id $jobs[0].ProcessId -ErrorAction SilentlyContinue
 }
 if(!(Test-Path $result) -or (Get-Content $result -Raw|ConvertFrom-Json).exit_code -ne 0){throw 'World B unsuccessful'}
 if(Select-String artifacts/life-r2/world-b.log -Pattern 'fallback=True' -Quiet){throw 'World B fallback detected'}
 @{mode='candidate-b-generated';native_library='baseline';requires_candidate_reimport=$true;source_commit=(git rev-parse HEAD)}|ConvertTo-Json|Set-Content artifacts/life-r2/SOURCE-MODE.json
 Save-Step 'wygeneruj świat B r2' 'World B zakończony 0, brak fallback=True. Następna kontrola zakresu i prototypów.' @($result,'artifacts/life-r2/SOURCE-MODE.json')
 $phase='scope'
 Heavy 'Script' 'scope-b' 'artifacts/life-r2/check-nonlife.py' @('b')
 Save-Step 'sprawdź zakres GLB B' 'Audyt zakresu B i 192 produktów raw zakończony 0.' @('artifacts/life-r2/nonlife-glb-audit-b.json','artifacts/life-r2/scope-b-result.json')
 $phase='prototypes'
 Heavy 'Script' 'prototypes-b' 'artifacts/life-r2/audit-prototypes.py' @('b')
 Save-Step 'potwierdź geometrię prototypów B' 'Audyt prototypów B zakończony 0, grupy i kolizje zgodne z baseline.' @('artifacts/life-r2/prototype-b.json','artifacts/life-r2/prototypes-b-result.json')
 $phase='streetscape-test'
 Heavy 'TestFile' 'pytest-streetscape-b' 'tests/gis/test_streetscape.py'
 Save-Step 'sprawdź pojedynczy test streetscape B' 'Test_streetscape zakończony 0. Pełny GIS nadal dopiero po końcowych oględzinach.' @('artifacts/life-r2/pytest-streetscape-b.log','artifacts/life-r2/pytest-streetscape-b-result.json')
 $phase='import'
 & pwsh -NoProfile -File artifacts/life-r2/unity-phase.ps1 -Phase PreparedImport
 if($LASTEXITCODE -ne 0){throw 'Import B failed'}
 @{mode='candidate-b-native-imported';requires_candidate_reimport=$false;imported=(Get-Date -Format o)}|ConvertTo-Json|Set-Content artifacts/life-r2/SOURCE-MODE.json
 Save-Step 'zaimportuj materiały i siatki B' 'PreparedImport B zakończony 0 pod Unity; native library B.' @('artifacts/life-r2/SOURCE-MODE.json')
 $phase='capture'
 & pwsh -NoProfile -File artifacts/life-r2/capture-exact.ps1 -Stage after-b-exact
 if($LASTEXITCODE -ne 0){throw 'Capture B failed'}
 $phase='native-validation'
 & uv run --project tools/worldgen python artifacts/life-r2/validate-native-b.py
 if($LASTEXITCODE -ne 0){throw 'Native material/payload validation failed'}
 Save-Step 'zapisz 456 renderów i natywny dowód B' 'Capture i walidacja native materiałów/Half2 zakończone 0. Plansze jeszcze nie obejrzane.' @('artifacts/life-r2/native-b-validation.json','artifacts/life-r2/after-b-exact-inputs.json')
 $phase='comparison'
 & uv run --project tools/worldgen python artifacts/life-r2/compare-exact.py before-exact after-b-exact exact-b
 if($LASTEXITCODE -ne 0){throw 'Exact comparison B failed'}
 Heavy 'Script' 'compare-b' 'artifacts/life-r2/render-compare-b.py'
 Save-Step 'zapisz dokładny budżet i plansze B' 'Porównanie wszystkich 114 kamer × 4 gotowe. Następne: oględziny autora i decyzja o poprawkach, potem pełny GIS i EditMode.' @('artifacts/life-r2/exact-b-all-camera-budget.json','artifacts/life-r2/exact-b-budget-summary.json','artifacts/life-r2/b-all-camera-budget.json','artifacts/life-r2/b-budget-summary.json')
 $phase='await-author-review';$code=0
} catch {
 Add-Content artifacts/life-r2/STATUS.md ("`nB przerwane na etapie {0}: {1}. Sprawdzić istniejący log; nie restartować całego ciągu." -f $phase,$_.Exception.Message)
 git add -f -- artifacts/life-r2/STATUS.md
 git commit -m "wip(life): zapisz przerwany etap B $phase"
 throw
} finally {
 @{phase=$phase;exit_code=$code;finished=(Get-Date -Format o)}|ConvertTo-Json|Set-Content artifacts/life-r2/post-b-result.json
}
