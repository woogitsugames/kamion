$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
foreach($probe in @(@{name='before-no-pane';flag='-truckNoPane'},@{name='before-no-coat';flag='-truckCoatOff'})){
 if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'){throw 'PHONE_RUN present'}
 $log=Join-Path $LogsDir ($probe.name+'.log')
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.TruckPaintRound.RunBatch','-truckRound',$probe.name,'-truckCameras','truck-34,truck-at-gate,truck-front',$probe.flag,'1','-qaEnvDump','1')
 Show-UnityLogErrors $log
 if($code -ne 0 -or -not(Select-String $log -Pattern "TRUCK_ROUND_RESULT: OK $($probe.name)" -Quiet)){throw "Ablation failed $code"}
}
