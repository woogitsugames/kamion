$ErrorActionPreference = 'Stop'
# The fire-station-only generator has already produced current textures. The standard
# import wrapper treats ANY _src mtime change as invalidating ALL sets; avoid rebuilding
# untouched sets, but validate every Medium input file before the identical Unity entry.
if (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') { throw 'PHONE_RUN present' }
. "$PSScriptRoot/../../scripts/env.ps1"
$spec = Get-Content (Join-Path $RepoRoot 'art-source/world/materials/materials_spec.json') -Raw | ConvertFrom-Json
foreach ($set in $spec.sets.PSObject.Properties) {
 $info=$set.Value.files.Medium
 if (-not $info) { continue }
 foreach ($file in $info.files) {
  $full = Join-Path $RepoRoot "art-source/world/materials/$($info.dir)/$file"
  if (-not (Test-Path -LiteralPath $full)) { throw "Missing current PBR input $full" }
 }
}
$log=Join-Path $LogsDir 'tint-calibrated-import.log'
$code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.World.Import.RegionImporter.ImportBatch','-region','bialystok-industrial-c','-tiers','Low,High','-materialTier','Medium')
Show-UnityLogErrors $log
if ($code -ne 0 -or -not (Select-String -Path $log -Pattern 'IMPORT_RESULT: OK' -Quiet)) { throw "Import failed exit=$code" }
Select-String -Path $log -Pattern 'sha256 mismatches|IMPORT_RESULT|WORLD_MEMORY' | ForEach-Object { Write-Output $_.Line }
