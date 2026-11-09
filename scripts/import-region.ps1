<#
.SYNOPSIS
  Import a generated world region into Unity (glTFast) and build its drivable scene.
.EXAMPLE
  pwsh scripts/import-region.ps1 -Region bialystok-industrial-c
  pwsh scripts/import-region.ps1 -Region bialystok-industrial-c -Build      # also run the world generator first
  pwsh scripts/import-region.ps1 -Region bialystok-industrial-c -Tiers Low  # only the Low/Medium content (WorldC)
.NOTES
  Inputs : Data/Regions/<id>/generated/world_manifest.json (git), Data/raw/derived/<id>/world/chunk_*.glb, *.low.glb,
           instances_*.json (not in git), art-source/world/{props,vegetation,signs,textures} (git),
           Data/Regions/<id>/route_start.json (scripts/export-route.py; re-exported here when -Build or missing).
  Output : game/Assets/_Generated/World/<id>/ (gitignored): Meshes/{Low,High}/*.asset, Collision/*.asset, Materials/,
           Textures/, Instances.asset, WorldC.unity (Low/Medium content, in the build list), WorldC_High.unity (High
           content, shipped only with build-android.ps1 -WorldHigh). Memory report: artifacts/world/<id>-import.json.
  Decision records: docs/adr/0011-world-import-gltfast.md, docs/adr/0012-world-content-tiers-instancing.md.
  One Unity per project: fails if game/ is open elsewhere.
#>
param(
    [Parameter(Mandatory)] [string]$Region,
    [switch]$Build,
    [string]$Tiers = 'Low,High'
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"

$glbDir = Join-Path $RepoRoot "Data/raw/derived/$Region/world"
if ($Build -or -not (Test-Path (Join-Path $glbDir 'chunk_0_0.glb'))) {
    Write-Host "world chunks missing or -Build: running the generator"
    & uv run --project (Join-Path $RepoRoot 'tools/worldgen') (Join-Path $RepoRoot 'tools/worldgen/roads/build_world.py') --region $Region
    if ($LASTEXITCODE -ne 0) { throw "build_world.py failed ($LASTEXITCODE)" }
}
$route = Join-Path $RepoRoot "Data/Regions/$Region/route_start.json"
if ($Build -or -not (Test-Path $route)) {
    & uv run --project (Join-Path $RepoRoot 'tools/worldgen') python (Join-Path $RepoRoot 'scripts/export-route.py') --region $Region
    if ($LASTEXITCODE -ne 0) { throw "export-route.py failed ($LASTEXITCODE)" }
}

$log = Join-Path $LogsDir "import-region-$Region-$(Get-Timestamp).log"
$unityArgs = @('-executeMethod', 'Game.World.Import.RegionImporter.ImportBatch', '-region', $Region, '-tiers', $Tiers)
$code = Invoke-UnityBatch -LogFile $log -Arguments $unityArgs
$result = Select-String -Path $log -Pattern 'IMPORT_RESULT:.*' | Select-Object -Last 1
if ($code -ne 0 -or -not $result -or $result.Line -notmatch 'IMPORT_RESULT: OK') {
    Write-Host "import FAILED (exit $code), log: $log" -ForegroundColor Red
    Show-UnityLogErrors $log
    exit ([Math]::Max(1, $code))
}
Write-Host $result.Line
Select-String -Path $log -Pattern '(WORLD_MEMORY|WORLD_TERRAIN_BAND): .*' | ForEach-Object { Write-Host $_.Matches[0].Value }
Write-Host "log: $log"
exit 0
