param([string]$Round='before')
$ErrorActionPreference='Stop'
if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'){throw 'PHONE_RUN present'}
. "$PSScriptRoot/../../scripts/env.ps1"
$truckLog=Join-Path $LogsDir "truck-paint-$Round.log"
$code=Invoke-UnityBatch -LogFile $truckLog -Arguments @('-executeMethod','Game.Editor.VisualQA.TruckPaintRound.RunBatch','-truckRound',$Round)
Show-UnityLogErrors $truckLog
if($code -ne 0 -or -not(Select-String $truckLog -Pattern "TRUCK_ROUND_RESULT: OK $Round" -Quiet)){throw "Truck round failed $code"}
