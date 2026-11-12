$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r3'){throw 'Wrong branch'}
$old=Get-Content artifacts/life-r3/post-baseline-result.json -Raw|ConvertFrom-Json
if($old.phase -ne 'import' -or $old.exit_code -ne 1){throw 'Unexpected previous stop'}
if(Test-Path artifacts/life-r3/before){throw 'Capture already exists; inspect before resuming'}
Copy-Item artifacts/life-r3/post-baseline-result.json artifacts/life-r3/post-baseline-cancelled-proof-result.json
$phase='import';$code=1
function Save-Step([string]$Message,[string[]]$Files=@()) {
 Add-Content artifacts/life-r3/STATUS.md ("`nWznowienie baseline ({0}): {1}. Następny krok: capture i oględziny; produkcja bez zmian." -f (Get-Date -Format o),$Message)
 git add -f -- artifacts/life-r3/STATUS.md @Files
 git commit -m "wip(life): $Message"
 if($LASTEXITCODE){throw 'WIP failed'}
}
try {
 & pwsh -NoProfile -File artifacts/life-r3/unity-phase.ps1 -Phase PreparedVerified -ProofPath artifacts/life-r3/baseline-generated-source-proof.json
 if($LASTEXITCODE){throw 'Validated import failed'}
 Save-Step 'zaimportuj baseline r3 po ponownej kontroli SHA' @()
 $phase='capture'
 & pwsh -NoProfile -File artifacts/life-r3/capture-exact.ps1 -Stage before
 if($LASTEXITCODE){throw 'Baseline capture failed'}
 & uv run --project tools/worldgen python artifacts/life-r3/validate_exact.py before *> artifacts/life-r3/before-validation.log
 if($LASTEXITCODE){throw 'Capture metadata validation failed'}
 Save-Step 'zapisz komplet kontrolowanych kadrów baseline r3' @('artifacts/life-r3/before-inputs.json','artifacts/life-r3/before-validation.json')
 $phase='await-author-inspection';$code=0
} catch {
 Save-Step "zapisz przerwany wznowiony baseline r3 $phase" @()
 throw
} finally {
 @{phase=$phase;exit_code=$code;finished=(Get-Date -Format o);cancelled_redundant_proof='post-baseline-cancelled-proof-result.json'}|ConvertTo-Json|Set-Content artifacts/life-r3/post-baseline-result.json
}
