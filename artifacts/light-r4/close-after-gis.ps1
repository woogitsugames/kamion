param([Parameter(Mandatory)][int]$GisProcessId,[Parameter(Mandatory)][string]$GisLog)
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$identity=Get-CimInstance Win32_Process -Filter "ProcessId=$GisProcessId"
if($null -eq $identity -or $identity.Name -ne 'pwsh.exe' -or
    $identity.CommandLine -notmatch '-File artifacts/light-r4/run-heavy\.ps1 -Task GisFinal -RoundEnd\s*$') {
    throw 'Not the expected live round4 GIS controller'
}
$process=Get-Process -Id $GisProcessId
$null=$process.Handle # Hold the real process handle so the exit code remains observable after termination.
Write-Output "Waiting for actual GIS process $GisProcessId, created $($identity.CreationDate); no additional Python or Unity."
while(-not $process.WaitForExit(1000)) { }
$code=$process.ExitCode
if($null -eq $code){throw 'Real GIS process exit code is unavailable; inspect the original tool handle explicitly'}
if($code -ne 0){throw "GIS controller terminated with code$code; do not close a failed round"}
Write-Output "Actual GIS process terminated0; checking complete summary, tests, budget and delivery guards."
& pwsh -NoProfile -File "$PSScriptRoot/close-round.ps1" -GisExitCode $code -GisLog $GisLog
if($LASTEXITCODE){throw 'Guarded round close failed; inspect state without repeating completed mutations'}
Write-Output "ROUND4_HANDOFF_RESULT: OK; branch=$((git branch --show-current).Trim()); head=$((git rev-parse HEAD).Trim())"

