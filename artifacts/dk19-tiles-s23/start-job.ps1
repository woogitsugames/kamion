# Detached job launcher: writes artifacts/dk19-tiles-s23/jobs/<name>.ps1 with the steps and starts it hidden.
param([Parameter(Mandatory)][string]$Name, [Parameter(Mandatory)][string[]]$Steps)
$wt = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$jobs = Join-Path $PSScriptRoot 'jobs'; New-Item -ItemType Directory -Force $jobs | Out-Null
$list = ($Steps | ForEach-Object { "  '" + $_.Replace("'", "''") + "'" }) -join ",`n"
$body = "& `"$PSScriptRoot/run-steps.ps1`" -Log `"$wt/artifacts/logs/dk19-$Name.log`" -Steps @(`n$list)`n"
$f = Join-Path $jobs "$Name.ps1"; Set-Content $f $body -Encoding utf8
(Start-Process pwsh -ArgumentList '-NoProfile','-File',$f -WindowStyle Hidden -PassThru -RedirectStandardError "$wt/artifacts/logs/dk19-$Name.err" -RedirectStandardOutput "$wt/artifacts/logs/dk19-$Name.out").Id
