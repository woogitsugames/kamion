$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Main PHONE_RUN/GPT_UNITY_HOLD active; no Unity launch'}
$log=[IO.Path]::GetFullPath('artifacts/car-paint-r1/pearl-probe.log')
$code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.WorldPbrPearlProbe.RunBatch')
git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting
if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'PEARL_PROBE_RESULT: OK' -Quiet)){throw "Pearl probe failed $code"}
