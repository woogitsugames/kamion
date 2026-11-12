param([Parameter(Mandatory)][int]$ImportProcess)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
$p = Get-Process -Id $ImportProcess -ErrorAction SilentlyContinue
if ($p) {
    if ($p.ProcessName -ne 'pwsh') { throw 'Unexpected import process type' }
    # The PID is verified by the caller. Pin its handle instead of repeatedly
    # querying WMI, which can cancel requests under concurrent Unity imports.
    $null = $p.Handle
    while (-not $p.HasExited) { Start-Sleep -Seconds 5 }
    $p.Dispose()
}
$log = Get-Content "$PSScriptRoot/baseline-import-wrapper.log" -Raw
if (-not $log.Contains('IMPORT_RESULT: OK') -or -not $log.Contains('released gpt-landmarks')) {
    throw 'Import did not finish successfully with a released slot; no capture started'
}
& pwsh "$PSScriptRoot/unity-step.ps1" -Step Capture -Phase before -Cameras all
exit $LASTEXITCODE
