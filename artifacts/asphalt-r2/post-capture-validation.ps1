param([Parameter(Mandatory)][int]$AfterCaptureProcessId)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((& git branch --show-current).Trim() -ne 'gpt-asphalt-r2'){throw 'Wrong branch'}
$process=Get-CimInstance Win32_Process -Filter "ProcessId=$AfterCaptureProcessId"
if($process -and ($process.Name -notin @('powershell.exe','pwsh.exe') -or
 $process.CommandLine -notmatch 'run-heavy.ps1 -Stage World -Label candidate2' -or
 $process.CommandLine -notmatch 'run-unity-stage.ps1 -Stage Capture -Label candidate2')){throw 'Unexpected pipeline to await'}
if($process){Write-Output "Awaiting own world/import/capture pipeline PID $AfterCaptureProcessId";Wait-Process -Id $AfterCaptureProcessId -ErrorAction SilentlyContinue}
if((& git branch --show-current).Trim() -ne 'gpt-asphalt-r2'){throw 'Branch changed'}
if((Get-Content artifacts/asphalt-r2/STATUS.md -Raw) -notmatch 'zapisano artifacts/asphalt-r2/candidate2/High-clear'){throw 'Capture did not complete successfully'}
& pwsh artifacts/asphalt-r2/audit-camera-state.ps1 -After candidate2
if($LASTEXITCODE -ne 0){throw 'Camera/material state audit failed'}
& pwsh artifacts/asphalt-r2/audit-counters.ps1 -After candidate2
if($LASTEXITCODE -ne 0){throw 'Counter audit failed'}
& pwsh artifacts/asphalt-r2/run-heavy.ps1 -Stage GeometryAudit -Label candidate2
if($LASTEXITCODE -ne 0){throw 'Geometry audit failed'}
& pwsh artifacts/asphalt-r2/run-heavy.ps1 -Stage Compare -Label candidate2
if($LASTEXITCODE -ne 0){throw 'Image/counter comparison failed'}
& pwsh artifacts/asphalt-r2/build-material-review.ps1 -After candidate2
if($LASTEXITCODE -ne 0){throw 'Material sheets failed'}
& pwsh artifacts/asphalt-r2/build-reference-review.ps1 -After candidate2
if($LASTEXITCODE -ne 0){throw 'Reference sheets failed'}
Set-Content artifacts/asphalt-r2/CANDIDATE2-REVIEW-READY.txt (Get-Date -Format o)
Add-Content artifacts/asphalt-r2/STATUS.md "$(Get-Date -Format o): Scoped candidate2 ma pełne audyty pozy/flag, liczników i geometrii; porównanie obrazów exit 0. Arkusze gotowe do samokontroli i ponownej niezależnej oceny. Rozpoczynamy sekwencję testów końcowych; bez deklaracji końcowego PASS/publikacji."
git add -f artifacts/asphalt-r2/STATUS.md artifacts/asphalt-r2/CANDIDATE2-REVIEW-READY.txt artifacts/asphalt-r2/camera-state-audit-candidate2.json artifacts/asphalt-r2/counter-audit-candidate2.json artifacts/asphalt-r2/counter-audit-candidate2.csv artifacts/asphalt-r2/comparison-candidate2.json artifacts/asphalt-r2/counters-candidate2.csv artifacts/asphalt-r2/geometry-comparison-candidate2.json
git commit -m 'wip(asphalt): checkpoint scoped candidate ready for final visual review' 2> artifacts/asphalt-r2/git-checkpoint-warnings.log
if($LASTEXITCODE -ne 0){throw 'Checkpoint failed'}
& pwsh artifacts/asphalt-r2/end-validation.ps1 -Label candidate2
exit $LASTEXITCODE
