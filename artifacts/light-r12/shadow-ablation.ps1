$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$variants=[ordered]@{
 'bias'='rq_shadowbias=0.4,rq_shadownormal=0.3'
 'splits'='rq_shadowsplit=0.2,rq_shadowsplit2=0.55'
 'combined'='rq_shadowbias=0.4,rq_shadownormal=0.3,rq_shadowsplit=0.2,rq_shadowsplit2=0.55'
}
foreach($v in $variants.GetEnumerator()) {
 foreach($light in @('clear','lowsun')) {
  if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'){throw 'Main PHONE_RUN lock'}
  & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC_High -Tier High -Lighting $light -Cameras stretch-05-docks,r10_hall_3,r10_block_3 -Gate3 Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json -OutputDir "artifacts/light-r12/shadow/$($v.Key)/$light" -Rq $v.Value
  if($LASTEXITCODE-ne0){throw "Failed $($v.Key) $light"}
  git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings
 }
}
