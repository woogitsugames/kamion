$ErrorActionPreference='Stop'
function Guard {
 if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity guard returned; stop, no auto-resume'}
}
# Root retained the bounded3.6mm candidate; overall owner quality remains partial/FAIL.
Guard
pwsh -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot/rebuild-candidate.ps1" -Round candidate3-final
if($LASTEXITCODE -ne 0){throw 'Final canonical/render validation stopped'}
. "$PSScriptRoot/../../scripts/env.ps1"
. "$PSScriptRoot/capture-proof.ps1"
Guard
$round='candidate3-final-coat-radiance-off';$started=Get-Date;$log=Join-Path $LogsDir 'truck-paint-candidate3-final-coat-radiance-off.log'
$code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.TruckPaintRound.RunBatch','-truckRound',$round,'-truckCameras','truck-34','-truckLights','overcast','-truckCoatRadianceOff','1')
Show-UnityLogErrors $log
Confirm-TruckCapture -LogFile $log -Round $round -Code $code -Started $started
Guard
pwsh -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot/../../scripts/test.ps1" -Platform EditMode
if($LASTEXITCODE -ne 0){throw 'Final fullEditMode failed; inspect actualXML/log'}
uv run --project tools/worldgen python "$PSScriptRoot/measure_contract.py" candidate3-final
uv run --project tools/worldgen python "$PSScriptRoot/compare_fixture.py" candidate3-final
