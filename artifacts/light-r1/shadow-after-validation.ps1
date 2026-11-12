param([Parameter(Mandatory)][int]$AfterProcessId)
$ErrorActionPreference = 'Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$prior = Get-CimInstance Win32_Process -Filter "ProcessId=$AfterProcessId"
if ($prior -and ($prior.Name -ne 'pwsh.exe' -or $prior.CommandLine -notlike '*-Task Analyze -Script artifacts/light-r1/review-matrices.py*')) {
    throw 'Odmowa: proces poprzedzający nie jest własnym wrapperem walidacji r1'
}
if ($prior) { Wait-Process -Id $AfterProcessId }
# The outer process has exited, including its finally/Release; this is never a reentrant acquisition.
& pwsh -NoProfile -File artifacts/light-r1/run-heavy.ps1 -Task Analyze -Script artifacts/light-r1/measure-shadow-midpoint.py
exit $LASTEXITCODE
