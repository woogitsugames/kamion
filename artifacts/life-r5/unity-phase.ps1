param([ValidateSet('Import','PreparedImport','PreparedVerified','EditMode')][string]$Phase,[string]$ProofPath='')
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if ($Phase -eq 'PreparedImport') {
 # Maps were generated canonically and source switches change mtimes without
 # changing their content. Validate every actual map and raw product instead of
 # rebuilding all unrelated sets solely because git restore touched a .py file.
 $stamp=Get-Date -Format yyyyMMdd-HHmmss
 & pwsh artifacts/life-r5/heavy.ps1 -Task Script -Tag "prepared-proof-$stamp" -ScriptPath artifacts/life-r5/source-proof.py -ScriptArguments "prepared-import-$stamp"
 if ($LASTEXITCODE -ne 0) { throw 'Prepared input verification failed' }
}
if ($Phase -eq 'PreparedVerified') {
 # A future generation batch can produce the proof while it already owns heavy.
 # Recheck actual files using streaming PowerShell hashes instead of queuing
 # another Python process solely for the same metadata verification.
 $full=[IO.Path]::GetFullPath($ProofPath)
 $allowed=[IO.Path]::GetFullPath('artifacts/life-r5')+[IO.Path]::DirectorySeparatorChar
 if(!$full.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Proof must belong to life r5'}
 $proof=Get-Content -LiteralPath $full -Raw|ConvertFrom-Json
 if($proof.raw_count -ne 192 -or $proof.mismatches -ne 0 -or $proof.fab_ready -ne 15){throw 'Incomplete prepared proof'}
 foreach($map in @($proof.source_sha,$proof.prepared_medium_textures,$proof.fixtures)) {
  foreach($entry in $map.PSObject.Properties) {
   if((Get-FileHash -LiteralPath $entry.Name).Hash.ToLowerInvariant() -ne $entry.Value.ToLowerInvariant()){throw "Prepared file changed: $($entry.Name)"}
  }
 }
 foreach($product in $proof.products) {
  if((Get-FileHash -LiteralPath $product.file).Hash.ToLowerInvariant() -ne $product.actual.ToLowerInvariant()){throw "Prepared raw changed: $($product.file)"}
 }
 if((Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash.ToLowerInvariant() -ne $proof.manifest_sha.ToLowerInvariant()){throw 'Prepared manifest changed'}
 $stamp=Get-Date -Format yyyyMMdd-HHmmss
 Copy-Item -LiteralPath $full -Destination "artifacts/life-r5/prepared-import-$stamp-source-proof.json"
}
& pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-life -StaleHours 1000000
if($LASTEXITCODE -ne 0){throw 'Brak slotu Unity'}
try {
 if($Phase -in @('PreparedImport','PreparedVerified')) {
  . scripts/env.ps1
  $log=[IO.Path]::GetFullPath("artifacts/life-r5/prepared-import-$stamp.log")
  $result=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.World.Import.RegionImporter.ImportBatch','-region','bialystok-industrial-c','-tiers','Low,High','-materialTier','Medium')
  if ($result -ne 0 -or !(Select-String -Path $log -Pattern 'IMPORT_RESULT: OK' -Quiet)) { throw "Import failed: $log" }
 } elseif($Phase -eq 'Import') {
  & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> artifacts/life-r5/import-wrapper.log
 } else {
  & pwsh scripts/test.ps1 -Platform EditMode *> artifacts/life-r5/editmode-wrapper.log
 }
 if($Phase -notin @('PreparedImport','PreparedVerified')) { $result=$LASTEXITCODE }
} finally {
 & pwsh scripts/unity-slot.ps1 -Release -Owner gpt-life
 git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
if($result -ne 0){throw "Niepowodzenie $Phase ($result)"}

