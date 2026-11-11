$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Shared Unity guard active'}
try {
 & pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene WorldC_High -Tier High -Lighting overcast -Gate3 artifacts/car-paint-r1/r1-cameras.json -Cameras g_dirt_level_0,g_dirt_level_1,g_dirt_level_2,g_dirt_level_3,r10b_black_05,g_current_black_wheel_02 -OutputDir artifacts/car-paint-r1/r2-focused/High-overcast
 if($LASTEXITCODE-ne0){throw 'Focused R2 failed'}
} finally { git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting }
