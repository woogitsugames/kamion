$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned; no auto-resume'}
$log=Join-Path $RepoRoot 'artifacts/surface-wear-r1/gate-install.log'
$code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.World.Import.WorldTruckInstaller.InstallBatch')
Show-UnityLogErrors $log
if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'TRUCK_RESULT: OK' -Quiet)){throw 'Bus world canonical vehicle install failed'}
git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
