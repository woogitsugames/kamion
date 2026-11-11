if (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') { throw 'PHONE_RUN present; Unity not started' }
. "$PSScriptRoot/../../scripts/env.ps1"
$tintLog = Join-Path $LogsDir 'tint-probe-before.log'
$tintExit=Invoke-UnityBatch -LogFile $tintLog -Arguments @('-executeMethod','Game.Editor.VisualQA.WorldPbrTintProbe.RunBatch')
Write-Output "TINT_PROBE_EXIT=$tintExit"
Show-UnityLogErrors $tintLog
exit $tintExit
