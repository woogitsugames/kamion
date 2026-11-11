param([Parameter(Mandatory)][int]$ImportProcess)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
while ($p = Get-CimInstance Win32_Process -Filter "ProcessId=$ImportProcess") {
    if ($p.CommandLine -notmatch 'artifacts[/\\]landmarks-r1[/\\]unity-step\.ps1\s+-Step\s+Import') {
        throw 'Import process identity changed; no capture started'
    }
    Start-Sleep -Seconds 5
}
$log = Get-Content "$PSScriptRoot/baseline-import-wrapper.log" -Raw
if (-not $log.Contains('IMPORT_RESULT: OK') -or -not $log.Contains('released gpt-landmarks')) {
    throw 'Import did not finish successfully with a released slot; no capture started'
}
& pwsh "$PSScriptRoot/unity-step.ps1" -Step Capture -Phase before -Cameras all
exit $LASTEXITCODE
