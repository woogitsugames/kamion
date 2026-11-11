param([string]$Round='before')
$ErrorActionPreference='Stop'
if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'){throw 'PHONE_RUN present'}
. "$PSScriptRoot/../../scripts/env.ps1"
$truckLog=Join-Path $LogsDir "truck-paint-$Round.log"
. "$PSScriptRoot/capture-proof.ps1"
$truckStart=Get-Date
$code=Invoke-UnityBatch -LogFile $truckLog -Arguments @('-executeMethod','Game.Editor.VisualQA.TruckPaintRound.RunBatch','-truckRound',$Round)
Show-UnityLogErrors $truckLog
Confirm-TruckCapture -LogFile $truckLog -Round $Round -Code $code -Started $truckStart
