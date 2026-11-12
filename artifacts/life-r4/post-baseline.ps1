param([Parameter(Mandatory)][int]$WaitFor)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r4'){throw 'Wrong branch'}
$running=Get-CimInstance Win32_Process -Filter "ProcessId=$WaitFor"
if($running){
 if($running.Name -ne 'pwsh.exe' -or $running.CommandLine -notmatch ' -NoProfile -File artifacts/life-r4/baseline-gen\.ps1$'){throw 'Wait target is not our baseline'}
 Wait-Process -Id $WaitFor -ErrorAction SilentlyContinue
}
$baseline=Get-Content artifacts/life-r4/baseline-gen-result.json -Raw|ConvertFrom-Json
if($baseline.phase -ne 'complete' -or $baseline.exit_code -ne 0){throw 'Inspect the terminal baseline result before import'}
if(Test-Path artifacts/life-r4/before){throw 'Baseline images already exist; inspect before any repeat'}
$phase='import';$code=1
function Save-Step([string]$message,[string[]]$files=@()){
 Add-Content artifacts/life-r4/STATUS.md ("`nPo baseline ({0}): {1}. Następny krok: kanoniczny capture, diagnostyka LOD, oględziny; produkcja bez zmian przed oceną." -f (Get-Date -Format o),$message)
 git add -f artifacts/life-r4/STATUS.md artifacts/life-r4/SOURCE-MODE.json @files
 git commit -m "wip(life): $message"
 if($LASTEXITCODE){throw 'WIP failed'}
}
try {
 & pwsh -NoProfile -File artifacts/life-r4/unity-phase.ps1 -Phase PreparedVerified -ProofPath artifacts/life-r4/baseline-generated-source-proof.json
 if($LASTEXITCODE){throw 'Baseline import failed'}
 $mode=Get-Content artifacts/life-r4/SOURCE-MODE.json -Raw|ConvertFrom-Json
 $mode.requires_reimport=$false
 $mode|ConvertTo-Json|Set-Content artifacts/life-r4/SOURCE-MODE.json
 Save-Step 'zaimportuj świeży baseline r4' @('artifacts/life-r4/baseline-gen-result.json')
 $phase='capture'
 & pwsh -NoProfile -File artifacts/life-r4/capture-exact.ps1 -Stage before
 if($LASTEXITCODE){throw 'Baseline capture failed'}
 # Metadata-only: no geometry build, image decode or test suite.
 & uv run --project tools/worldgen python artifacts/life-r4/validate_exact.py before *> artifacts/life-r4/before-validation.log
 if($LASTEXITCODE){throw 'Baseline capture metadata mismatch'}
 $mode.requires_shader_compile=$false
 $mode|ConvertTo-Json|Set-Content artifacts/life-r4/SOURCE-MODE.json
 Save-Step 'potwierdź pełny baseline r4 w czterech warunkach' @('artifacts/life-r4/before-inputs.json','artifacts/life-r4/before-validation.json')
 $phase='native-lod'
 & pwsh -NoProfile -File artifacts/life-r4/diagnose-lod.ps1
 if($LASTEXITCODE){throw 'Native LOD diagnostic failed; inspect evidence'}
 Save-Step 'zapisz diagnostykę natywnego LOD przed oględzinami' @('artifacts/life-r4/baseline-lod-result.json','artifacts/life-r4/yard-native-targets.json')
 $phase='await-author-inspection';$code=0
} catch {
 Save-Step "zapisz przerwany etap r4 $phase"
 throw
} finally {
 @{phase=$phase;exit_code=$code;finished=(Get-Date -Format o)}|ConvertTo-Json|Set-Content artifacts/life-r4/post-baseline-result.json
}
