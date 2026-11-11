param([switch]$SkipVisual)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
function Assert-PhoneSlot {
 if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'){throw 'Main PHONE_RUN lock'}
}
# Last matched visual proofs use the same vehicle cache as their before frames.
foreach($light in $(if($SkipVisual){@()}else{@('clear','lowsun')})) {
 Assert-PhoneSlot
 & pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 -Scene WorldC -Tier Medium -Lighting $light -Cameras stretch-05-docks,r10_hall_3,r10_block_3 -Gate3 Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json -OutputDir "artifacts/light-r12/after/Medium-$light"
 if($LASTEXITCODE-ne0){throw "Medium capture failed $light"}
 git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat
}
# Refresh known copied-cache missing-door-glass fixture only AFTER the matched matrix.
foreach($method in @('Game.Editor.Setup.TruckAssetBuilder.BuildBatch','Game.Editor.Setup.TrailerAssetBuilder.BuildBatch','Game.World.Import.WorldTruckInstaller.InstallBatch')) {
 Assert-PhoneSlot
 $tag=($method.Split('.')[-2])
 $log=[IO.Path]::GetFullPath("artifacts/light-r12/fixture-$tag.log")
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod',$method)
 if($code-ne0 -or (Select-String -Path $log -Pattern 'RESULT: FAILED|error CS\d+' -Quiet)){throw "Fixture refresh failed $method"}
 git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat
}
Assert-PhoneSlot
& pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/test.ps1 -Platform EditMode
if($LASTEXITCODE-ne0){throw 'EditMode failed'}
git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat
