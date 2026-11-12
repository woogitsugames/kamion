param([Parameter(Mandatory)][int]$ValidationProcessId)
$ErrorActionPreference='Stop'
$validation=Get-Process -Id $ValidationProcessId -ErrorAction Stop
$null=$validation.Handle
Write-Output "Waiting for own validation process $ValidationProcessId"
$validation.WaitForExit()
if($validation.ExitCode -ne 0){throw "Validation sequence failed: $($validation.ExitCode)"}
pwsh -NoProfile -File scripts/sbs-gate3.ps1 -ComposeOnly -IncludeDiagnostics -OutputRoot artifacts/sbs-r2/evidence *> artifacts/sbs-r2/compose-all.log
if($LASTEXITCODE -ne 0){throw 'Current composition failed'}
Write-Output 'Current composition and verified input snapshot OK'
pwsh -NoProfile -File artifacts/sbs-r2/run-heavy.ps1 -Task Audit *> artifacts/sbs-r2/audit-final.log
if($LASTEXITCODE -ne 0){throw 'R2 evidence audit failed'}
Write-Output 'Evidence audit OK'
uv run --project tools/refs python tools/refs/sbs_gate3.py report --runs artifacts/sbs-r2/history/sbs-r1/evidence artifacts/sbs-r2/evidence --output artifacts/sbs-gate3/latest --recognition Data/Regions/bialystok-industrial-c/sbs_recognition.json
if($LASTEXITCODE -ne 0){throw 'Offline report generation failed'}
Write-Output 'Offline report ready for manual review; no main delivery or full GIS performed yet.'
