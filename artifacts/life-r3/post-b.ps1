$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
function Save-Step([string]$Message,[string[]]$Files=@()) {
 Add-Content artifacts/life-r3/STATUS.md ("`nPo budowie B ({0}): {1}. Następny etap w post-b.ps1; po kompletach oględziny i decyzja." -f (Get-Date -Format o),$Message)
 git add -f -- artifacts/life-r3/STATUS.md @Files
 if($LASTEXITCODE){throw 'Staging failed'}
 git commit -m "wip(life): $Message"
 if($LASTEXITCODE){throw 'WIP failed'}
}
$phase='wait-build';$code=1
try {
 if(!(Test-Path artifacts/life-r3/candidate-b-build-result.json)) {
  $jobs=@(Get-CimInstance Win32_Process -Filter "Name='pwsh.exe'"|Where-Object {$_.CommandLine -match '^.*pwsh.exe"? -NoProfile -File artifacts/life-r3/candidate-build.ps1 -Stage b(?: -ReviewStage a)?\s*$'})
  if($jobs.Count -ne 1){throw 'Cannot identify the existing B build; do not duplicate'}
  Wait-Process -Id $jobs[0].ProcessId -ErrorAction SilentlyContinue
 }
 $build=Get-Content artifacts/life-r3/candidate-b-build-result.json -Raw|ConvertFrom-Json
 if($build.exit_code -ne 0 -or $build.phase -ne 'complete'){throw 'B build incomplete'}
 $phase='import'
 & pwsh -NoProfile -File artifacts/life-r3/unity-phase.ps1 -Phase PreparedVerified -ProofPath artifacts/life-r3/candidate-b-source-proof.json
 if($LASTEXITCODE){throw 'B import failed'}
 & pwsh -NoProfile -File artifacts/life-r3/validate-native-b.ps1 *> artifacts/life-r3/native-b-validation.log
 if($LASTEXITCODE){throw 'B native material scope failed'}
 @{mode='candidate-b-native-imported';requires_generation=$false;requires_reimport=$false;imported=(Get-Date -Format o)}|ConvertTo-Json|Set-Content artifacts/life-r3/SOURCE-MODE.json
 Save-Step 'potwierdź natywną zmianę tylko odbicia czerni B' @('artifacts/life-r3/SOURCE-MODE.json','artifacts/life-r3/candidate-b-build-result.json','artifacts/life-r3/native-b-validation.json')
 $phase='capture'
 & pwsh -NoProfile -File artifacts/life-r3/capture-exact.ps1 -Stage after-b
 if($LASTEXITCODE){throw 'B capture failed'}
 & uv run --project tools/worldgen python artifacts/life-r3/validate_exact.py after-b *> artifacts/life-r3/after-b-validation.log
 if($LASTEXITCODE){throw 'B capture metadata failed'}
 & uv run --project tools/worldgen python artifacts/life-r3/compare-exact.py before after-b b *> artifacts/life-r3/b-exact-comparison.log
 if($LASTEXITCODE){throw 'B integer/pose comparison failed'}
 Save-Step 'zapisz 492 kadry i budżet czerni B' @('artifacts/life-r3/after-b-inputs.json','artifacts/life-r3/after-b-validation.json','artifacts/life-r3/b-all-camera-budget.json','artifacts/life-r3/b-budget-summary.json')
 $phase='previews'
 & pwsh -NoProfile -File artifacts/life-r3/preview-focus.ps1 -Stage after-b
 if($LASTEXITCODE){throw 'B previews failed'}
 & pwsh -NoProfile -File artifacts/life-r3/measure-black.ps1 -Stage after-b
 if($LASTEXITCODE){throw 'B ROI failed'}
 & pwsh -NoProfile -File artifacts/life-r3/measure-black-rgb.ps1 -Stage after-b
 if($LASTEXITCODE){throw 'B RGB failed'}
 Save-Step 'zmierz barwę i kontrast czerni B' @('artifacts/life-r3/after-b-black-roi.json','artifacts/life-r3/after-b-black-rgb.json')
 $phase='await-author-review';$code=0
} catch {
 Save-Step "zapisz przerwany etap po B $phase" @()
 throw
} finally {
 @{phase=$phase;exit_code=$code;finished=(Get-Date -Format o)}|ConvertTo-Json|Set-Content artifacts/life-r3/post-b-result.json
}
