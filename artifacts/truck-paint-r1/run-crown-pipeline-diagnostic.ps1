$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
. "$PSScriptRoot/capture-proof.ps1"
if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned'}
$round='candidate3-layer-pipeline-diagnostic';$started=Get-Date;$log=Join-Path $LogsDir 'truck-paint-candidate3-layer-pipeline-diagnostic.log'
$code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.TruckPaintRound.RunBatch','-truckRound',$round,'-truckCameras','truck-34,truck-side','-truckLights','overcast','-truckMeshProbe','crown','-qaRq','rq_post=0,rq_fsrsharp=0')
Show-UnityLogErrors $log
Confirm-TruckCapture -LogFile $log -Round $round -Code $code -Started $started
