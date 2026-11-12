$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r2/24h'
if (!(Test-Path "$ev/protected-geometry-before.json")) { throw 'Capture baseline geometry before candidate generation' }
foreach ($file in @('tests/gis/test_furniture_signs_0120.py','tests/gis/test_furniture_0120.py','tests/gis/test_furniture_r1.py')) {
    & pwsh "$ev/heavy-step.ps1" -Step focused -Phase candidate1 -TestFile $file
    if ($LASTEXITCODE -ne 0) { throw "Focused file failed: $file; inspect before generating" }
}
& pwsh "$ev/heavy-step.ps1" -Step world -Phase after1
if ($LASTEXITCODE -ne 0) { throw 'Candidate world failed' }
if (Select-String -Path "$ev/build-after1.log" -SimpleMatch 'fallback=True') { throw 'Candidate source fallback' }
& pwsh "$ev/heavy-step.ps1" -Step geometry -Phase after
if ($LASTEXITCODE -ne 0) { throw 'Candidate protected geometry mismatch' }
Write-Output 'Candidate built and protected payloads verified; inspect before importing.'
