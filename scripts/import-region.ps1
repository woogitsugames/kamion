<#
.SYNOPSIS
  Import a generated world region into Unity (glTFast) and build its drivable scene.
.EXAMPLE
  pwsh scripts/import-region.ps1 -Region bialystok-industrial-c
  pwsh scripts/import-region.ps1 -Region bialystok-industrial-c -Build      # also run the world generator first
  pwsh scripts/import-region.ps1 -Region bialystok-industrial-c -Tiers Low  # only the Low/Medium content (WorldC)
  pwsh scripts/import-region.ps1 -Region knyszyn-w -BuildTarget Win64        # checkout whose Library is imported for Windows
.NOTES
  Inputs : Data/Regions/<id>/generated/world_manifest.json (git), Data/raw/derived/<id>/world/chunk_*.glb, *.low.glb,
           instances_*.json (not in git), art-source/world/{props,vegetation,signs,textures} (git),
           Data/Regions/<id>/route_start.json (scripts/export-route.py; re-exported here when -Build or missing).
  Output : game/Assets/_Generated/World/<id>/ (gitignored): Meshes/{Low,High}/*.asset, Collision/*.asset, Materials/,
           Textures/, Instances.asset, WorldC.unity (Low/Medium content, in the build list), WorldC_High.unity (High
           content, shipped only with build-android.ps1 -WorldHigh). Memory report: artifacts/world/<id>-import.json.
  Baked ground lighting (ADR 0064): WorldGI_1m.asset / WorldGI_2m.asset + WorldSkyVisibility on both scenes (WorldSkyBake,
           ~20 s); alone: -executeMethod Game.World.Import.WorldSkyBake.BakeBatch -region <id>. Maps: artifacts/bake-r8/maps/.
  PBR texture sets (ADR 0022): art-source/world/materials/<set>/<tier>/*.png are not versioned; when any file listed in
  materials_spec.json that build_all.py writes is missing or older than _src/*.py for -MaterialTier (default Medium;
  decided by `build_all.py --check`, files it does not produce are ignored) the generator runs first (all
  tiers, deterministic, ~4-8 min), then Unity copies the tier into _Generated/.../Textures/PBR with ASTC per the spec.
  Decision records: docs/adr/0011-world-import-gltfast.md, docs/adr/0012-world-content-tiers-instancing.md,
  docs/adr/0022-world-pbr-materials.md.
  One Unity per project: fails if game/ is open elsewhere.
#>
param(
    [Parameter(Mandatory)] [string]$Region,
    [switch]$Build,
    [string]$Tiers = 'Low,High',
    [ValidateSet('High', 'Medium', 'Low')] [string]$MaterialTier = 'Medium',
    # Editor platform of the run. A checkout whose Library is imported for Win64 (scripts/build-windows.ps1) must import
    # with Win64, otherwise Unity switches back to Android and re-imports every asset (ADR 0261).
    [ValidateSet('Android', 'Win64')] [string]$BuildTarget = 'Android'
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

# CC0 scans (ADR 0063): fetch + sha256-verify the raw maps the scan-based sets are built from (not in git)
$cc0Man = Join-Path $RepoRoot 'art-source/world/cc0/cc0_manifest.json'
if (Test-Path $cc0Man) {
    & uv run --project (Join-Path $RepoRoot 'tools/worldgen') python (Join-Path $RepoRoot 'art-source/world/materials/_src/cc0_fetch.py')
    if ($LASTEXITCODE -ne 0) { throw "cc0_fetch.py failed ($LASTEXITCODE): scan files missing or sha256 mismatch" }
}

# PBR texture sets (ADR 0022): rebuild when a file build_all.py writes for the tier is missing or older than _src/*.py
# (r7: asphalt_worn 0.13 -> 0.08 was committed in _src but the old PNGs stayed in use). The decision lives in
# build_all.py --check (single list of outputs, pytest tests/gis/test_materials_freshness.py): files it does not
# write with the current inputs (asphalt_detail_photo without the owner photo, scan-only sets without CC0 scans) are
# skipped, so they no longer force the ~8 min rebuild before every region (D43). Exit 0 = fresh, 3 = rebuild.
$matRoot = Join-Path $RepoRoot 'art-source/world/materials'
$buildAll = Join-Path $matRoot '_src/build_all.py'
& uv run --project (Join-Path $RepoRoot 'tools/worldgen') python $buildAll --check --tier $MaterialTier
$check = $LASTEXITCODE
if ($check -eq 3) {
    Write-Host "PBR sets stale for $MaterialTier - running art-source/world/materials/_src/build_all.py"
    & uv run --project (Join-Path $RepoRoot 'tools/worldgen') python $buildAll
    if ($LASTEXITCODE -ne 0) { throw "build_all.py failed ($LASTEXITCODE)" }
} elseif ($check -ne 0) {
    throw "build_all.py --check failed ($check)"
}

# Cab interior LOD0 FBX is outside git: without it (and without the generated TRAKT prefab) the vehicle builders fall back
# to the graybox. Fail before Unity with the regeneration command (build-fix-s24).
& "$PSScriptRoot/cab-lod0.ps1"
if ($LASTEXITCODE -ne 0) { exit 2 }
$log = Join-Path $LogsDir "import-region-$Region-$(Get-Timestamp).log"
$unityArgs = @('-executeMethod', 'Game.World.Import.RegionImporter.ImportBatch', '-region', $Region, '-tiers', $Tiers, '-materialTier', $MaterialTier)
$code = Invoke-UnityBatch -LogFile $log -Arguments $unityArgs -BuildTarget $BuildTarget
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
