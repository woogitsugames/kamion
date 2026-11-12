$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
function Save-Step([string]$Message,[string[]]$Files=@()) {
 Add-Content artifacts/life-r3/STATUS.md ("`nPo capture D ({0}): {1}. Następny krok według post-d.ps1, potem oględziny i wybór autora." -f (Get-Date -Format o),$Message)
 git add -f -- artifacts/life-r3/STATUS.md @Files
 if($LASTEXITCODE){throw 'Staging failed'}
 git commit -m "wip(life): $Message"
 if($LASTEXITCODE){throw 'WIP failed'}
}
$phase='wait-capture';$code=1
try {
 $jobs=@(Get-CimInstance Win32_Process -Filter "Name='pwsh.exe'"|Where-Object {$_.CommandLine -match '^.*pwsh.exe"? -NoProfile -File artifacts/life-r3/capture-exact.ps1 -Stage after-d\s*$'})
 if($jobs.Count -gt 1){throw 'Multiple D capture processes'}
 if($jobs.Count -eq 1){Wait-Process -Id $jobs[0].ProcessId -ErrorAction SilentlyContinue}
 if(Test-Path C:/Users/matma/Documents/Claude/kamion/artifacts/locks/unity-slots/gpt-life.slot){throw 'Own Unity still active; inspect existing process'}
 $phase='metadata'
 & uv run --project tools/worldgen python artifacts/life-r3/validate_exact.py after-d *> artifacts/life-r3/after-d-validation.log
 if($LASTEXITCODE){throw 'D capture metadata failed'}
 & uv run --project tools/worldgen python artifacts/life-r3/compare-exact.py before after-d d *> artifacts/life-r3/d-exact-comparison.log
 if($LASTEXITCODE){throw 'D integer/pose comparison failed'}
 & pwsh -NoProfile -File artifacts/life-r3/validate-native-b.ps1 *> artifacts/life-r3/native-d-b-material-validation.log
 if($LASTEXITCODE){throw 'D inherited B material contract failed'}
 Save-Step 'potwierdź pełne kadry i budżet D' @('artifacts/life-r3/after-d-inputs.json','artifacts/life-r3/after-d-validation.json','artifacts/life-r3/d-all-camera-budget.json','artifacts/life-r3/d-budget-summary.json')
 $phase='previews'
 & pwsh -NoProfile -File artifacts/life-r3/preview-focus.ps1 -Stage after-d
 if($LASTEXITCODE){throw 'D previews failed'}
 & pwsh -NoProfile -File artifacts/life-r3/measure-black.ps1 -Stage after-d
 if($LASTEXITCODE){throw 'D ROI failed'}
 & pwsh -NoProfile -File artifacts/life-r3/measure-black-rgb.ps1 -Stage after-d
 if($LASTEXITCODE){throw 'D RGB failed'}
 Save-Step 'przygotuj oględziny mocniejszego tyłu D' @('artifacts/life-r3/after-d-black-roi.json','artifacts/life-r3/after-d-black-rgb.json')
 $phase='gpu'
 & pwsh -NoProfile -File artifacts/life-r3/gpu-proof-d.ps1
 if($LASTEXITCODE){throw 'D GPU proof failed'}
 Save-Step 'potwierdź ograniczoną obwiednię D na GPU' @('artifacts/life-r3/gpu-d-result.json','artifacts/life-r3/gpu-d/instanced-film-gpu-proof.json','artifacts/life-r3/gpu-d/opacity-uv-proof.json')
 $phase='await-author-review';$code=0
} catch {
 Save-Step "zapisz przerwany etap po D $phase" @()
 throw
} finally {
 @{phase=$phase;exit_code=$code;finished=(Get-Date -Format o)}|ConvertTo-Json|Set-Content artifacts/life-r3/post-d-result.json
}


