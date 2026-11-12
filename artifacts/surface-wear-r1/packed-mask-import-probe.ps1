$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned; a new explicit ROOT release is required'}
$log=Join-Path $RepoRoot 'artifacts/surface-wear-r1/packed-mask-import-probe.log'
$code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','SurfaceWearQA.PackedMaskQA.ImportProbe')
Show-UnityLogErrors $log
if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'PACKED_MASK_IMPORT_PROBE: OK' -Quiet)){throw "Packed mask import/GPU probe failed with exit $code"}
git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
