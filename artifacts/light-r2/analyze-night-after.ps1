param([Parameter(Mandatory)][int]$AfterProcessId)
$ErrorActionPreference = 'Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$prior = Get-CimInstance Win32_Process -Filter "ProcessId=$AfterProcessId"
if ($prior -and ($prior.Name -ne 'pwsh.exe' -or $prior.CommandLine -notlike '*-File artifacts/light-r2/regenerate-import-night.ps1*')) {
    throw 'Nie jest to własny pipeline generatora/importu r2'
}
if ($prior) { Wait-Process -Id $AfterProcessId }
$images = @(Get-ChildItem artifacts/light-r2/night-ablation,artifacts/light-r2/fresh-dusk -Recurse -Filter '*.png')
if ($images.Count -ne 60) { throw "Niepełna ablacja Night: $($images.Count)/60" }
& pwsh -NoProfile -File artifacts/light-r2/run-heavy.ps1 -Task Analyze -Script artifacts/light-r2/measure-night.py
exit $LASTEXITCODE
