$ErrorActionPreference='Stop'
if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'){throw 'Phone lock present'}
. "$PSScriptRoot/../../scripts/env.ps1"
. "$PSScriptRoot/capture-proof.ps1"
$truckStart=Get-Date
$truckLog=Join-Path $LogsDir 'before-near-pane-off.log'
$code=Invoke-UnityBatch -LogFile $truckLog -Arguments @('-executeMethod','Game.Editor.VisualQA.TruckPaintRound.RunBatch','-truckRound','before-near-pane-off','-truckCameras','truck-34,truck-at-gate,truck-front','-truckNoPane','windscreen','-truckEnvDirections','1')
Show-UnityLogErrors $truckLog
Confirm-TruckCapture -LogFile $truckLog -Round before-near-pane-off -Code $code -Started $truckStart
