# Truck + trailer asset rebuild, then DrivingLab (Win64). Inside a -Unity step.
. scripts/env.ps1
$ts = Get-Timestamp
foreach ($m in @(@('truck','Game.Editor.Setup.TruckAssetBuilder.BuildBatch','TRUCK_RESULT'), @('trailer','Game.Editor.Setup.TrailerAssetBuilder.BuildBatch','TRAILER_RESULT'))) {
  $log = Join-Path $LogsDir "nt-$($m[0])-$ts.log"
  $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod', $m[1]) -BuildTarget Win64
  $r = Select-String -Path $log -Pattern "$($m[2]):.*" | Select-Object -Last 1
  Write-Host "$($m[0]) exit=$code $($r.Line)"
  if ($code -ne 0 -or -not $r -or $r.Line -notmatch 'OK') { exit 1 }
}
pwsh scripts/build-lab.ps1 -SkipAudio -BuildTarget Win64
exit $LASTEXITCODE
