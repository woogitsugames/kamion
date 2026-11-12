$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned'}
$log=Join-Path $RepoRoot 'artifacts/surface-wear-r1/p8-wearoff.log'
$material=Join-Path $RepoRoot 'game/Assets/_Generated/World/bialystok-industrial-c/Materials/M_marking_white.mat'
$before=(Get-FileHash -LiteralPath $material -Algorithm SHA256).Hash
$code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','SurfaceWearQA.PaintWearAblation.Run','-qaScene','WorldC_High','-qaTier','High','-qaGate3',(Join-Path $RepoRoot 'artifacts/surface-wear-r1/qa-final-field-cameras.json'),'-qaOutput',(Join-Path $RepoRoot 'artifacts/surface-wear-r1/p8-wearoff/High-overcast'))
Show-UnityLogErrors $log
if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'PAINT_ABLATION_RESTORED' -Quiet)){throw 'Paint ablation failed'}
if((Get-FileHash -LiteralPath $material -Algorithm SHA256).Hash-ne$before){throw 'Production material changed'}
git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
