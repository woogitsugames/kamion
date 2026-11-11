$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
. "$PSScriptRoot/capture-proof.ps1"
if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity guard returned; stop'}
$round='candidate2-glass-layer-audit';$started=Get-Date;$log=Join-Path $LogsDir 'truck-paint-candidate2-glass-layer-audit.log'
$code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.TruckPaintRound.RunBatch','-truckRound',$round,'-truckCameras','truck-at-gate','-truckTiers','High','-truckLights','clear','-truckGlassAudit','1')
Show-UnityLogErrors $log
Confirm-TruckCapture -LogFile $log -Round $round -Code $code -Started $started
