$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned'}
$log=Join-Path $RepoRoot 'artifacts/surface-wear-r1/lane-components.log'
$code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','SurfaceWearQA.LaneFieldAudit.Run')
Show-UnityLogErrors $log
if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'LANE_COMPONENT_AUDIT: OK' -Quiet)){throw 'Actual lane component audit failed'}
git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
