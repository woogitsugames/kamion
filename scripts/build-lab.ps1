<#
.SYNOPSIS
  Regenerate the DrivingLab scene, vehicle prefabs and data assets from code (Unity batchmode), then import the
  generated vehicle audio when tools/audio's WAVs are present.
.EXAMPLE
  pwsh scripts/build-lab.ps1
.NOTES
  Entry points: Game.Editor.Setup.DrivingLabSceneBuilder.BuildBatch, Game.Editor.Audio.VehicleAudioImporter.ImportBatch.
  Logs: artifacts/logs/build-lab-<ts>.log, artifacts/logs/audio-import-<ts>.log. Exit 0 = both OK.
#>
param([switch]$SkipAudio)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
$ts = Get-Timestamp

$log = Join-Path $LogsDir "build-lab-$ts.log"
$code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod', 'Game.Editor.Setup.DrivingLabSceneBuilder.BuildBatch')
$r = Select-String -Path $log -Pattern 'DRIVINGLAB_RESULT:.*' | Select-Object -Last 1
if ($code -ne 0 -or -not $r -or $r.Line -notmatch 'OK') {
    Write-Host "DrivingLab build FAILED (exit $code), log: $log" -ForegroundColor Red
    Show-UnityLogErrors $log
    exit ([Math]::Max(1, $code))
}
Write-Host $r.Line
if ($SkipAudio) { exit 0 }

$alog = Join-Path $LogsDir "audio-import-$ts.log"
$code = Invoke-UnityBatch -LogFile $alog -Arguments @('-executeMethod', 'Game.Editor.Audio.VehicleAudioImporter.ImportBatch')
$r = Select-String -Path $alog -Pattern 'AUDIOIMPORT_RESULT:.*' | Select-Object -Last 1
if ($code -ne 0 -or -not $r) {
    Write-Host "audio import FAILED (exit $code), log: $alog" -ForegroundColor Red
    Show-UnityLogErrors $alog
    exit ([Math]::Max(1, $code))
}
Write-Host $r.Line
exit 0
