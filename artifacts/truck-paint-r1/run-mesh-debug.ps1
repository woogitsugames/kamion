$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
. "$PSScriptRoot/capture-proof.ps1"
foreach($mode in @('mask','fresnel','env')){
 if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity guard returned; await explicit release'}
 $round="candidate1-debug-$mode";$started=Get-Date;$log=Join-Path $LogsDir ("truck-paint-$round.log")
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.TruckPaintRound.RunBatch','-truckRound',$round,'-truckCameras','truck-34','-truckLights','overcast','-truckMeshProbe',$mode,'-qaRq','rq_post=0,rq_fsrsharp=0')
 Show-UnityLogErrors $log
 Confirm-TruckCapture -LogFile $log -Round $round -Code $code -Started $started
}
