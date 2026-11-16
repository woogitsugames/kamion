param([string]$Name, [string[]]$Steps)
$wt = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
& "$PSScriptRoot/run-steps.ps1" -Log "$wt/artifacts/logs/dk19-$Name.log" -Steps $Steps
