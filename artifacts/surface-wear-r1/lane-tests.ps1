$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned; explicit ROOT release required'}
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/test.ps1 -Platform EditMode -Filter 'Game.Tests.RoadPaintLaneFieldTests;Game.Tests.RoadWearUvContractTests'
if($LASTEXITCODE-ne0){throw 'Lane/sentinel tests failed'}
git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
