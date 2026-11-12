$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
function Save-Step([string]$Message,[string[]]$Files=@()) {
 Add-Content artifacts/life-r3/STATUS.md ("`nPrzed zmianą ({0}): {1}. Następny krok według post-baseline.ps1; po capture obejrzeć kadry i dopiero zmienić produkcję." -f (Get-Date -Format o),$Message)
 git add -f -- artifacts/life-r3/STATUS.md @Files
 if($LASTEXITCODE){throw 'Staging failed'}
 git commit -m "wip(life): $Message"
 if($LASTEXITCODE){throw 'WIP failed'}
}
$phase='wait-generation';$code=1
try {
 if(!(Test-Path artifacts/life-r3/baseline-gen-result.json)) {
  $jobs=@(Get-CimInstance Win32_Process -Filter "Name='pwsh.exe'" | Where-Object {$_.CommandLine -match '^.*pwsh.exe"? -NoProfile -File artifacts/life-r3/baseline-gen.ps1\s*$'})
  if($jobs.Count -ne 1){throw 'Cannot identify the existing baseline generation; do not duplicate'}
  Wait-Process -Id $jobs[0].ProcessId -ErrorAction SilentlyContinue
 }
 if(!(Test-Path artifacts/life-r3/baseline-gen-result.json) -or (Get-Content artifacts/life-r3/baseline-gen-result.json -Raw|ConvertFrom-Json).exit_code -ne 0){throw 'Baseline generation incomplete'}
 $phase='cameras'
 & pwsh -NoProfile -File artifacts/life-r3/heavy.ps1 -Task Script -Tag prepare-cameras -ScriptPath artifacts/life-r3/prepare-cameras.py
 if($LASTEXITCODE){throw 'Camera preparation failed'}
 Save-Step 'wybierz rzeczywiste kadry tyłu i floty r3' @('artifacts/life-r3/cameras.json','artifacts/life-r3/camera-targets.json','artifacts/life-r3/prepare-cameras-result.json','artifacts/life-r3/baseline-generated-source-proof.json','artifacts/life-r3/baseline-gen-result.json')
 $phase='import'
 & pwsh -NoProfile -File artifacts/life-r3/unity-phase.ps1 -Phase PreparedImport
 if($LASTEXITCODE){throw 'Baseline import failed'}
 Save-Step 'zaimportuj świeży baseline r3' @()
 $phase='capture'
 & pwsh -NoProfile -File artifacts/life-r3/capture-exact.ps1 -Stage before
 if($LASTEXITCODE){throw 'Baseline capture failed'}
 & uv run --project tools/worldgen python artifacts/life-r3/validate_exact.py before *> artifacts/life-r3/before-validation.log
 if($LASTEXITCODE){throw 'Baseline capture validation failed'}
 Save-Step 'zapisz kontrolowany baseline osobówek r3' @('artifacts/life-r3/before-inputs.json','artifacts/life-r3/before-validation.json')
 $phase='await-author-inspection';$code=0
} catch {
 Save-Step ("zapisz przerwany baseline przed zmianą r3 na etapie $phase")
 throw
} finally {
 @{phase=$phase;exit_code=$code;finished=(Get-Date -Format o)}|ConvertTo-Json|Set-Content artifacts/life-r3/post-baseline-result.json
}
