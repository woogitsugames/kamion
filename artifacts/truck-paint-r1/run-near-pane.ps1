param([string]$Round='before-near-pane-off')
$ErrorActionPreference='Stop'
if(((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD'))){throw 'Phone lock present'}
. "$PSScriptRoot/../../scripts/env.ps1"
. "$PSScriptRoot/capture-proof.ps1"
$truckStart=Get-Date
$truckLog=Join-Path $LogsDir ("truck-paint-"+$Round+".log")
$code=Invoke-UnityBatch -LogFile $truckLog -Arguments @('-executeMethod','Game.Editor.VisualQA.TruckPaintRound.RunBatch','-truckRound',$Round,'-truckCameras','truck-34,truck-at-gate,truck-front','-truckNoPane','windscreen','-truckEnvDirections','1')
Show-UnityLogErrors $truckLog
Confirm-TruckCapture -LogFile $truckLog -Round $Round -Code $code -Started $truckStart
