# ADR0101: material-coverage masks (magenta) for ROI verification, Low (WorldC) overcast. One Unity run per material.
# Usage: pwsh artifacts/tint-r2/run-masks.ps1 -Materials 'kp_wall,noise_panel_dark' [-Cameras 'a,b']
param([string]$Materials, [string]$Cameras = '', [string]$Scene = 'WorldC', [string]$Tier = 'Low')
$ErrorActionPreference = 'Stop'
$repo = Resolve-Path "$PSScriptRoot/../.."
foreach ($m in $Materials.Split(',')) {
  while ((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')) { Start-Sleep 60 }
  $out = Join-Path $repo "artifacts/tint-r2/masks$(if($Scene -ne 'WorldC'){'-'+$Scene})/$m"
  $a = @{ Scene = $Scene; Tier = $Tier; Lighting = 'overcast'; OutputDir = $out; Mask = ":M_$m"; Gate3 = (Join-Path $repo 'artifacts/tint-r2/cameras_r2.json') }
  if ($Cameras) { $a.Cameras = $Cameras }
  & "$repo/scripts/visual-qa.ps1" @a
  Push-Location $repo
  git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
  Pop-Location
  Write-Output "MASK_DONE $m"
}
