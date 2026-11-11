$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
foreach($v in @(@('control','rq_glassshadow=0'),@('realtime-off','rq_shadow=0'),@('baked-off','rq_worldsun=0'))) {
 if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'){throw 'Main PHONE_RUN lock'}
 & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Medium -Lighting clear -Cameras stretch-05-docks -OutputDir "artifacts/light-r12/shadow/component-$($v[0])/clear" -Rq $v[1]
 if($LASTEXITCODE-ne0){throw "Failed $($v[0])"}
 git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat
}
