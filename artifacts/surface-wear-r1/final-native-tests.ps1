$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
function Guard {if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned; a new explicit ROOT release is required'}}
Guard
pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/surface-wear-r1/native-audit.ps1 -Stage final
if($LASTEXITCODE-ne0){throw 'Final native audit failed'}
uv run --project tools/worldgen python artifacts/surface-wear-r1/paint_uniform_proof.py final
if($LASTEXITCODE-ne0){throw 'Final actual paint uniform proof failed'}
Guard
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/test.ps1 -Platform EditMode
if($LASTEXITCODE-ne0){throw 'Full final EditMode failed'}
git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
