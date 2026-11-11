$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
. "$PSScriptRoot/capture-proof.ps1"
foreach($probe in @(@{name='before-no-pane-fixed';flag='-truckNoPane'},@{name='before-coat-radiance-off';flag='-truckCoatRadianceOff'})){
 if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'){throw 'PHONE_RUN present'}
 $log=Join-Path $LogsDir ($probe.name+'.log')
 $truckStart=Get-Date
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.TruckPaintRound.RunBatch','-truckRound',$probe.name,'-truckCameras','truck-34,truck-at-gate,truck-front',$probe.flag,'1','-qaEnvDump','1')
 Show-UnityLogErrors $log
 Confirm-TruckCapture -LogFile $log -Round $probe.name -Code $code -Started $truckStart
}
