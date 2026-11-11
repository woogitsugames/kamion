param([string]$Round='candidate1')
$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
foreach($step in @(@{id='truck';method='Game.Editor.Setup.TruckAssetBuilder.BuildBatch';result='TRUCK_RESULT: OK'},@{id='trailer';method='Game.Editor.Setup.TrailerAssetBuilder.BuildBatch';result='TRAILER_RESULT: OK'},@{id='install';method='Game.World.Import.WorldTruckInstaller.InstallBatch';result='TRUCK_RESULT: OK'},@{id='probe';method='Game.Editor.VisualQA.TruckPaintProbe.RunBatch';result='TINT_PROBE_RESULT: OK'})){
 while(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'){Write-Output 'PHONE_RUN present; waiting before Unity launch';Start-Sleep -Seconds 30}
 $log=Join-Path $LogsDir ("truck-paint-"+$Round+'-'+$step.id+'.log')
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod',$step.method,'-tintProbeOutput',(Join-Path $RepoRoot "artifacts/truck-paint-r1/$Round-lamp-probe.json"))
 Show-UnityLogErrors $log
 if($code -ne 0 -or -not(Select-String -Path $log -Pattern $step.result -Quiet)){throw "Vehicle step failed $($step.id) $code"}
}
while(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'){Write-Output 'PHONE_RUN present; waiting before capture';Start-Sleep -Seconds 30}
pwsh -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot/run-round.ps1" -Round $Round
if($LASTEXITCODE -ne 0){throw 'Candidate capture failed'}
uv run --project tools/worldgen python "$PSScriptRoot/preview.py" $Round
