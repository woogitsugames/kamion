$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
foreach($name in @('before','bias','combined')) {
 foreach($light in @('clear','lowsun')) {
  if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'){throw 'Main PHONE_RUN lock'}
  $qa=@('-Scene','WorldC','-Tier','Medium','-Lighting',$light,'-Cameras','stretch-05-docks,r10_hall_3,r10_block_3','-Gate3','Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json','-OutputDir',"artifacts/light-r12/shadow/Medium-$name/$light")
  if($name-ne'before') {
   $rq='rq_shadowbias=0.4,rq_shadownormal=0.3'
   if($name-eq'combined'){$rq+=',rq_shadowsplit=0.55'}
   $qa+=@('-Rq',$rq)
  }
  & pwsh -NoProfile -File scripts/visual-qa.ps1 @qa
  if($LASTEXITCODE-ne0){throw "Failed $name $light"}
  git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings
 }
}
