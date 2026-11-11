$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
. "$PSScriptRoot/capture-proof.ps1"
function Guard {
 if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity guard returned; stop, no auto-resume'}
}
# CanonicalTruck/Install already succeeded before hold; resume tests/captures, not another fixture rebuild.
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
