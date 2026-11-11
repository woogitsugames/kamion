$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
. "$PSScriptRoot/capture-proof.ps1"
foreach($step in @(@{round='candidate1-env-directions';extra=@('-truckLights','overcast','-truckEnvDirections','1')},@{round='candidate1-capture256';extra=@('-truckTiers','High','-truckLights','clear','-qaRq','rq_envcap=256,rq_envcap_lod=0.25')})){
 if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity guard returned; stop'}
 $log=Join-Path $LogsDir ("truck-paint-"+$step.round+'.log');$started=Get-Date
 $args0=@('-executeMethod','Game.Editor.VisualQA.TruckPaintRound.RunBatch','-truckRound',$step.round,'-truckCameras','truck-at-gate')+$step.extra
 $code=Invoke-UnityBatch -LogFile $log -Arguments $args0
 Show-UnityLogErrors $log
 Confirm-TruckCapture -LogFile $log -Round $step.round -Code $code -Started $started
}
