$Phase='Import'
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
function Guard { if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Unity hold returned; explicit ROOT release required'} }
if($Phase-eq'Import') {
 Guard
 $log=Join-Path $RepoRoot 'artifacts/surface-wear-r1/gate-first-import.log'
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.World.Import.RegionImporter.ImportBatch','-region','bialystok-industrial-c','-tiers','Low,High','-materialTier','Medium')
 Show-UnityLogErrors $log
 if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'IMPORT_RESULT: OK' -Quiet)){throw "Sentinel import failed exit $code"}
 git restore -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings/QualitySettings.asset
}
