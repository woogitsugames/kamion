$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
. "$PSScriptRoot/capture-proof.ps1"
# Prepared during phone hold. Execute only after a NEW explicit root release.
foreach($step in @(
 @{round='candidate2-boxmip';extra=@('-truckGlassAudit','1')},
 @{round='candidate2-far-glass-mask';extra=@('-truckTiers','High','-truckLights','clear','-truckNoPane','windscreen','-truckGlassProbe','mask','-truckGlassAudit','1','-qaRq','rq_post=0,rq_fsrsharp=0')}
)){
 if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity guard returned; stop'}
 $log=Join-Path $LogsDir ("truck-paint-"+$step.round+'.log');$started=Get-Date
 $args0=@('-executeMethod','Game.Editor.VisualQA.TruckPaintRound.RunBatch','-truckRound',$step.round,'-truckCameras','truck-34,truck-at-gate,truck-front')+$step.extra
 $code=Invoke-UnityBatch -LogFile $log -Arguments $args0
 Show-UnityLogErrors $log
 Confirm-TruckCapture -LogFile $log -Round $step.round -Code $code -Started $started
}
