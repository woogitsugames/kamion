$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
$material=Join-Path $RepoRoot 'game/Assets/_Generated/World/bialystok-industrial-c/Materials/M_marking_white.mat'
$before=(Get-FileHash -LiteralPath $material -Algorithm SHA256).Hash
foreach($tier in @('Low','High')) {foreach($light in @('clear','overcast')) {
 if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned; explicitROOTrelease required'}
 $scene=if($tier-eq'High'){'WorldC_High'}else{'WorldC'}
 $log=Join-Path $RepoRoot "artifacts/surface-wear-r1/paint-half-$tier-$light.log"
 $output=Join-Path $RepoRoot "artifacts/surface-wear-r1/paint-half/$tier-$light"
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','SurfaceWearQA.PaintWearAblation.Run','-qaScene',$scene,'-qaTier',$tier,'-qaLighting',$light,'-qaPaintWheel','0.425','-qaCameras','d_field_p8_turn,d_wear_crossing','-qaGate3',(Join-Path $RepoRoot 'artifacts/surface-wear-r1/qa-paint-half-cameras.json'),'-qaOutput',$output)
 Show-UnityLogErrors $log
 if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'PAINT_ABLATION_RESTORED' -Quiet)){throw "Paint half failed$tier$light"}
 if((Get-FileHash -LiteralPath $material -Algorithm SHA256).Hash-ne$before){throw 'Production material changed'}
 git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
}}
