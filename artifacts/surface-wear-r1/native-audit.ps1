param([string]$Stage='before')
$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned; noauto-resume'}
$log=Join-Path $RepoRoot ("artifacts/surface-wear-r1/native-$Stage.log")
$code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','SurfaceWearQA.SurfaceWearAudit.Run','-surfaceAuditOut',(Join-Path $RepoRoot "artifacts/surface-wear-r1/native-$Stage.json"))
Show-UnityLogErrors $log
if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'SURFACE_NATIVE_AUDIT: OK' -Quiet)){throw "Nativeactualmeshauditfailed$Stage$code"}
git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
