param()
$ErrorActionPreference='Stop'
$repo='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-life'
Set-Location -LiteralPath $repo
function Assert-Branch {
 if((git branch --show-current).Trim() -ne 'gpt-life-r2'){throw 'Unexpected branch; stop follow-up'}
}
function Save-Step([string]$Label,[string]$Detail,[string[]]$Evidence=@()) {
 Assert-Branch
 Add-Content artifacts/life-r2/STATUS.md ("`nEtap po generatorze ({0}): {1} Następne etapy wykonuje run-after-world.ps1; REPORT dopiero po oględzinach autora i końcowych testach." -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'),$Detail)
 & git add -u -- Data/Regions/bialystok-industrial-c/generated art-source/world/props
 if($LASTEXITCODE -ne 0){throw 'Could not stage own generated outputs'}
 & git add -f -- artifacts/life-r2/STATUS.md @Evidence
 if($LASTEXITCODE -ne 0){throw 'Could not stage evidence'}
 & git commit -m "wip(life): $Label"
 if($LASTEXITCODE -ne 0){throw 'WIP commit failed'}
}
function Run-Heavy([string]$Task,[string]$Tag,[string]$Path='') {
 Assert-Branch
 if($Task -eq 'Script') { & pwsh -NoProfile -File artifacts/life-r2/heavy.ps1 -Task Script -Tag $Tag -ScriptPath $Path }
 elseif($Task -eq 'TestFile') { & pwsh -NoProfile -File artifacts/life-r2/heavy.ps1 -Task TestFile -Tag $Tag -TestPath $Path }
 else { & pwsh -NoProfile -File artifacts/life-r2/heavy.ps1 -Task $Task -Tag $Tag }
 if($LASTEXITCODE -ne 0){throw "Heavy stage failed: $Tag"}
}
$phase='wait-world'; $code=1
try {
 Assert-Branch
 $result='artifacts/life-r2/world-candidate-result.json'
 if(!(Test-Path -LiteralPath $result)) {
  $jobs=@(Get-CimInstance Win32_Process -Filter "Name='pwsh.exe'" | Where-Object {$_.CommandLine -like '*-File artifacts/life-r2/heavy.ps1 -Task World -Tag world-candidate*'})
  if($jobs.Count -ne 1){throw 'Cannot identify exactly one existing world wrapper; do not restart it'}
  Write-Host "Waiting for existing world wrapper $($jobs[0].ProcessId)"
  Wait-Process -Id $jobs[0].ProcessId -ErrorAction SilentlyContinue
 }
 if(!(Test-Path -LiteralPath $result)){throw 'World wrapper ended without result; inspect existing session'}
 $world=Get-Content -LiteralPath $result -Raw | ConvertFrom-Json
 if($world.exit_code -ne 0){throw 'World generation failed'}
 if(Select-String -LiteralPath artifacts/life-r2/world-candidate.log -Pattern 'fallback=True' -Quiet){throw 'World log contains fallback=True; inspect before import'}
 $phase='world-complete'
 Save-Step 'ukończ regenerację świata r2' 'world-candidate zakończony kodem 0; slot heavy zwolniony. Następne: kontrola zakresu GLB i niezmienności 192 produktów raw.' @('artifacts/life-r2/world-candidate-result.json')
 $phase='scope-audit'
 Run-Heavy 'Script' 'nonlife-glb' 'artifacts/life-r2/check-nonlife.py'
 Save-Step 'potwierdź zakres biblioteki i danych świata' 'Audyt rzeczywistego GLB i 192 produktów raw przeszedł; szczegóły w nonlife-glb-audit.json. Nie dowodzi to jeszcze jakości obrazu ani kosztu GPU.' @('artifacts/life-r2/nonlife-glb-audit.json','artifacts/life-r2/nonlife-glb-result.json')
 $phase='streetscape-tests'
 Run-Heavy 'TestFile' 'pytest-streetscape' 'tests/gis/test_streetscape.py'
 Save-Step 'potwierdź pojedynczy test_streetscape r2' 'Pojedynczy test_streetscape.py zakończony 0 na świeżych generatach; liczba testów w pytest-streetscape.log. Pełny GIS pozostaje na koniec rundy.' @('artifacts/life-r2/pytest-streetscape.log','artifacts/life-r2/pytest-streetscape-result.json')
 $phase='fidelity'
 Run-Heavy 'Fidelity' 'fidelity-candidate'
 Save-Step 'odśwież raport fidelity po świecie r2' 'Fidelity zakończone kodem 0 pod heavy; raporty odświeżone. Następne: weryfikacja wejść i import Unity.' @('artifacts/life-r2/fidelity-candidate-result.json')
 $phase='prepared-import'
 & pwsh -NoProfile -File artifacts/life-r2/unity-phase.ps1 -Phase PreparedImport
 if($LASTEXITCODE -ne 0){throw 'PreparedImport failed'}
 Save-Step 'zaimportuj świat kandydata r2' 'PreparedImport zakończony kodem 0; helper zweryfikował wejścia pod heavy, potem osobno importował w Unity gpt-life. Następne: AFTER przy zamrożonych kamerach.'
 $phase='after-capture'
 $baseline=Get-Content artifacts/life-r2/baseline-complete.json -Raw | ConvertFrom-Json
 if((Get-FileHash artifacts/life-r2/cameras.json).Hash -ne $baseline.camera_packet_sha){throw 'Frozen camera packet changed'}
 & pwsh -NoProfile -File artifacts/life-r2/capture.ps1 -Stage after
 if($LASTEXITCODE -ne 0){throw 'AFTER capture failed'}
 foreach($condition in $baseline.conditions) {
  $count=@(Get-ChildItem (Join-Path artifacts/life-r2/after $condition.condition) -Filter '*.png').Count
  if($count -ne $condition.pngs){throw "AFTER camera count mismatch: $($condition.condition)"}
 }
 Save-Step 'ukończ 456 renderów AFTER r2' 'AFTER zakończony kodem 0, liczby PNG zgodne z baseline (114 × 4); każdy Unity miał osobny slot gpt-life, zwolniony po wywołaniu. Następne: porównanie CPU i plansze.'
 $phase='compare'
 Run-Heavy 'Script' 'compare-r2' 'artifacts/life-r2/compare.py'
 Save-Step 'zapisz porównanie wszystkich kamer r2' 'compare.py zakończony 0; all-camera-budget.json i budget-summary.json obejmują wszystkie kamery i draws instancji osobno. Plansze jeszcze wymagają oględzin autora; nie ma odbioru wizualnego ani REPORT.' @('artifacts/life-r2/all-camera-budget.json','artifacts/life-r2/budget-summary.json','artifacts/life-r2/compare-r2-result.json')
 $phase='await-visual-review'; $code=0
} catch {
 Add-Content artifacts/life-r2/STATUS.md ("`nPrzerwano run-after-world.ps1 na etapie {0}: {1}. Nie uruchamiać ponownie całego ciągu; najpierw sprawdzić log i terminalny wynik danego etapu." -f $phase,$_.Exception.Message)
 if((git branch --show-current).Trim() -eq 'gpt-life-r2') {
  & git add -f -- artifacts/life-r2/STATUS.md
  & git commit -m "wip(life): zapisz przerwany etap $phase"
 }
 throw
} finally {
 @{exit_code=$code;phase=$phase;finished=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content artifacts/life-r2/post-world-result.json
}
