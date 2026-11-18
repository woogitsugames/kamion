<#
.SYNOPSIS
  Re-apply project configuration as code (player settings, URP quality tiers, Boot scene).
  Idempotent. Runs Game.Editor.Setup.ProjectSetup.ApplyAll in Unity batchmode.
.EXAMPLE
  pwsh scripts/setup-project.ps1
#>
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
# Cab interior LOD0 FBX is outside git: without it (and without the generated TRAKT prefab) the vehicle builders fall back
# to the graybox. Fail before Unity with the regeneration command (build-fix-s24).
& "$PSScriptRoot/cab-lod0.ps1"
if ($LASTEXITCODE -ne 0) { exit 2 }
$log = Join-Path $LogsDir "setup-$(Get-Timestamp).log"
$code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod', 'Game.Editor.Setup.ProjectSetup.ApplyAll')
$ok = Select-String -Path $log -Pattern 'SETUP_RESULT: OK' -Quiet
if ($code -ne 0 -or -not $ok) { Write-Host "setup FAILED (exit $code), log $log" -ForegroundColor Red; Show-UnityLogErrors $log; exit ([Math]::Max(1, $code)) }
Select-String -Path $log -Pattern '\[SETUP\]' | ForEach-Object { Write-Host $_.Line }
Write-Host "setup OK, log $log"
exit 0
