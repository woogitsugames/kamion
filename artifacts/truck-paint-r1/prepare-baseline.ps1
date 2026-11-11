$ErrorActionPreference='Stop'
if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'){throw 'PHONE_RUN present'}
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/import-region.ps1 -Region bialystok-industrial-c
if($LASTEXITCODE -ne 0){throw 'Region import failed'}
. "$PSScriptRoot/../../scripts/env.ps1"
foreach($step in @(@{id='truck';method='Game.Editor.Setup.TruckAssetBuilder.BuildBatch';result='TRUCK_RESULT: OK'},@{id='trailer';method='Game.Editor.Setup.TrailerAssetBuilder.BuildBatch';result='TRAILER_RESULT: OK'},@{id='install';method='Game.World.Import.WorldTruckInstaller.InstallBatch';result='TRUCK_RESULT: OK'},@{id='probe';method='Game.Editor.VisualQA.TruckPaintProbe.RunBatch';result='TINT_PROBE_RESULT: OK'})){
 if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'){throw 'PHONE_RUN present'}
 $log=Join-Path $LogsDir ("truck-paint-baseline-"+$step.id+'.log')
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod',$step.method)
 Show-UnityLogErrors $log
 if($code -ne 0 -or -not(Select-String $log -Pattern $step.result -Quiet)){throw "Canonical/probe step failed $($step.id) $code"}
}
