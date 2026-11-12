$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
function Save-Step([string]$Message,[string[]]$Files=@()) {
 Add-Content artifacts/life-r3/STATUS.md ("`nPo budowie A ({0}): {1}. Następny etap w post-a.ps1; po kompletach obejrzeć obrazy i zdecydować o kolejnej ablacji." -f (Get-Date -Format o),$Message)
 git add -f -- artifacts/life-r3/STATUS.md @Files
 if($LASTEXITCODE){throw 'Staging failed'}
 git commit -m "wip(life): $Message"
 if($LASTEXITCODE){throw 'WIP failed'}
}
$phase='wait-build';$code=1
try {
 if(!(Test-Path artifacts/life-r3/candidate-a-build-result.json)) {
  $jobs=@(Get-CimInstance Win32_Process -Filter "Name='pwsh.exe'"|Where-Object {$_.CommandLine -match '^.*pwsh.exe"? -NoProfile -File artifacts/life-r3/candidate-build.ps1 -Stage a\s*$'})
  if($jobs.Count -ne 1){throw 'Cannot identify the existing candidate build; do not duplicate'}
  Wait-Process -Id $jobs[0].ProcessId -ErrorAction SilentlyContinue
 }
 $build=Get-Content artifacts/life-r3/candidate-a-build-result.json -Raw|ConvertFrom-Json
 if($build.exit_code -ne 0 -or $build.phase -ne 'complete'){throw 'Candidate A build incomplete'}
 @{mode='candidate-a-generated';native_library='baseline';requires_generation=$false;requires_reimport=$true;source_commit=(git rev-parse HEAD)}|ConvertTo-Json|Set-Content artifacts/life-r3/SOURCE-MODE.json
 $phase='import'
 & pwsh -NoProfile -File artifacts/life-r3/unity-phase.ps1 -Phase PreparedVerified -ProofPath artifacts/life-r3/candidate-a-source-proof.json
 if($LASTEXITCODE){throw 'Candidate A import failed'}
 @{mode='candidate-a-native-imported';requires_generation=$false;requires_reimport=$false;imported=(Get-Date -Format o)}|ConvertTo-Json|Set-Content artifacts/life-r3/SOURCE-MODE.json
 Save-Step 'zaimportuj spójny natywny kandydat A' @('artifacts/life-r3/SOURCE-MODE.json','artifacts/life-r3/candidate-a-build-result.json')
 $phase='capture'
 & pwsh -NoProfile -File artifacts/life-r3/capture-exact.ps1 -Stage after-a
 if($LASTEXITCODE){throw 'Candidate A capture failed'}
 & uv run --project tools/worldgen python artifacts/life-r3/validate_exact.py after-a *> artifacts/life-r3/after-a-validation.log
 if($LASTEXITCODE){throw 'Candidate A capture metadata failed'}
 & uv run --project tools/worldgen python artifacts/life-r3/compare-exact.py before after-a a *> artifacts/life-r3/a-exact-comparison.log
 if($LASTEXITCODE){throw 'Candidate A integer/pose comparison failed'}
 Save-Step 'zapisz 492 kontrolowane kadry i budżet A' @('artifacts/life-r3/after-a-inputs.json','artifacts/life-r3/after-a-validation.json','artifacts/life-r3/a-all-camera-budget.json','artifacts/life-r3/a-budget-summary.json')
 $phase='previews'
 & pwsh -NoProfile -File artifacts/life-r3/preview-focus.ps1 -Stage after-a
 if($LASTEXITCODE){throw 'A previews failed'}
 & pwsh -NoProfile -File artifacts/life-r3/measure-black.ps1 -Stage after-a
 if($LASTEXITCODE){throw 'A ROI failed'}
 Save-Step 'przygotuj podglądy i pomiar czerni A' @('artifacts/life-r3/after-a-black-roi.json')
 $phase='gpu-proof'
 & pwsh -NoProfile -File artifacts/life-r3/gpu-proof-a.ps1
 if($LASTEXITCODE){throw 'Candidate A GPU proof failed'}
 Save-Step 'potwierdź natywne UV1 i osad A na GPU edytora' @('artifacts/life-r3/gpu-a-result.json','artifacts/life-r3/gpu-a/instanced-film-gpu-proof.json','artifacts/life-r3/gpu-a/opacity-uv-proof.json')
 $phase='await-author-review';$code=0
} catch {
 Save-Step "zapisz przerwany etap po A $phase" @()
 throw
} finally {
 @{phase=$phase;exit_code=$code;finished=(Get-Date -Format o)}|ConvertTo-Json|Set-Content artifacts/life-r3/post-a-result.json
}
