$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
. "$PSScriptRoot/capture-proof.ps1"
function Guard {
 if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity guard returned; stop, no auto-resume'}
}
# NEW explicit root release required. Run pending run-glass-terms.ps1 first against C2 fixture (no crown tags yet).
foreach($step in @(@{id='truck';method='Game.Editor.Setup.TruckAssetBuilder.BuildBatch';result='TRUCK_RESULT: OK'},@{id='install';method='Game.World.Import.WorldTruckInstaller.InstallBatch';result='TRUCK_RESULT: OK'})){
 Guard
 $log=Join-Path $LogsDir ("truck-paint-candidate3-"+$step.id+'.log')
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod',$step.method)
 Show-UnityLogErrors $log
 if($code -ne 0 -or -not(Select-String -Path $log -SimpleMatch $step.result -Quiet)){throw "Canonical crown fixture failed $($step.id) $code"}
}
Guard
pwsh -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot/../../scripts/test.ps1" -Platform EditMode -Filter TruckDoorCrownTests
if($LASTEXITCODE -ne 0){throw 'Actual crown GPU/fixture tests failed; do not continue to visual adoption'}
foreach($step in @(
 @{round='candidate3-crown-off';extra=@('-truckCrownOff','1')},
 @{round='candidate3-crown-on';extra=@()},
 @{round='candidate3-crown-mask';extra=@('-truckLights','overcast','-truckMeshProbe','crown','-qaRq','rq_post=0,rq_fsrsharp=0')}
)){
 Guard
 $log=Join-Path $LogsDir ("truck-paint-"+$step.round+'.log');$started=Get-Date
 $args0=@('-executeMethod','Game.Editor.VisualQA.TruckPaintRound.RunBatch','-truckRound',$step.round,'-truckCameras','truck-34,truck-at-gate,truck-side')+$step.extra
 $code=Invoke-UnityBatch -LogFile $log -Arguments $args0
 Show-UnityLogErrors $log
 Confirm-TruckCapture -LogFile $log -Round $step.round -Code $code -Started $started
}
uv run --project tools/worldgen python "$PSScriptRoot/measure_contract.py" candidate3-crown-off candidate3-crown-on
uv run --project tools/worldgen python "$PSScriptRoot/preview.py" candidate3-crown-on
