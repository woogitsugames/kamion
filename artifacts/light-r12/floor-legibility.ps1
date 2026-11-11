$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
foreach($value in @('0.75','0')) {
 if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'){throw 'Main PHONE_RUN lock'}
 & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC_High -Tier High -Lighting clear -Cameras cab-dash,driver-andersa-to-putry,r10_block_3 -Gate3 Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json -RenderScale 0.70 -Rq "rq_scale=1,rq_fsrsharp=$value" -OutputDir "artifacts/light-r12/floor/rcas-$value"
 if($LASTEXITCODE-ne0){throw "Failed floor sharp$value"}
 git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat
}
