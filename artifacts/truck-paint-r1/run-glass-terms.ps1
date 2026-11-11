$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
. "$PSScriptRoot/capture-proof.ps1"
# Pending NEW explicit root release. No polling or transient auto-resume.
foreach($step in @(
 @{round='candidate2-near-transmission';mode='near-transmission';extra=@('-truckLights','overcast','-qaRq','rq_post=0,rq_fsrsharp=0')},
 @{round='candidate2-near-radiance-off';mode='near-radiance-off';extra=@()}
)){
 if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity guard returned; stop'}
 $log=Join-Path $LogsDir ("truck-paint-"+$step.round+'.log');$started=Get-Date
 $args0=@('-executeMethod','Game.Editor.VisualQA.TruckPaintRound.RunBatch','-truckRound',$step.round,'-truckCameras','truck-34,truck-at-gate','-truckGlassProbe',$step.mode)+$step.extra
 $code=Invoke-UnityBatch -LogFile $log -Arguments $args0
 Show-UnityLogErrors $log
 Confirm-TruckCapture -LogFile $log -Round $step.round -Code $code -Started $started
}
