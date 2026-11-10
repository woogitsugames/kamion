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
  Baked ground lighting (ADR 0064): WorldGI_1m.asset / WorldGI_2m.asset + WorldSkyVisibility on both scenes (WorldSkyBake,
           ~20 s); alone: -executeMethod Game.World.Import.WorldSkyBake.BakeBatch -region <id>. Maps: artifacts/bake-r8/maps/.
  PBR texture sets (ADR 0022): art-source/world/materials/<set>/<tier>/*.png are not versioned; when any file listed in
  materials_spec.json is missing for -MaterialTier (default Medium) the generator _src/build_all.py runs first (all
  tiers, deterministic, ~4 min), then Unity copies the tier into _Generated/.../Textures/PBR with ASTC per the spec.
  Decision records: docs/adr/0011-world-import-gltfast.md, docs/adr/0012-world-content-tiers-instancing.md,
  docs/adr/0022-world-pbr-materials.md.
  One Unity per project: fails if game/ is open elsewhere.
#>
param(
    [Parameter(Mandatory)] [string]$Region,
    [switch]$Build,
    [string]$Tiers = 'Low,High',
    [ValidateSet('High', 'Medium', 'Low')] [string]$MaterialTier = 'Medium'
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

# PBR texture sets (ADR 0022): build when any file of the spec is missing for the tier
$matRoot = Join-Path $RepoRoot 'art-source/world/materials'
$spec = Get-Content (Join-Path $matRoot 'materials_spec.json') -Raw | ConvertFrom-Json
$missing = 0; $stale = 0
# The PNGs are generated and outside git: a changed generator (_src/*.py) must rebuild them, not only missing files
# (r7: asphalt_worn 0.13 -> 0.08 was committed in _src but the old PNGs stayed in use).
$srcTime = (Get-ChildItem (Join-Path $matRoot '_src') -Filter *.py | Measure-Object LastWriteTimeUtc -Maximum).Maximum
foreach ($p in $spec.sets.PSObject.Properties) {
    $f = $p.Value.files.$MaterialTier
    if (-not $f) { continue }
    foreach ($n in $f.files) {
        $png = Join-Path $matRoot "$($f.dir)/$n"
        if (-not (Test-Path $png)) { $missing++ } elseif ((Get-Item $png).LastWriteTimeUtc -lt $srcTime) { $stale++ }
    }
}
if ($missing -gt 0 -or $stale -gt 0) {
    Write-Host "PBR sets: $missing missing, $stale older than _src for $MaterialTier - running art-source/world/materials/_src/build_all.py"
    & uv run --project (Join-Path $RepoRoot 'tools/worldgen') python (Join-Path $matRoot '_src/build_all.py')
    if ($LASTEXITCODE -ne 0) { throw "build_all.py failed ($LASTEXITCODE)" }
}

$log = Join-Path $LogsDir "import-region-$Region-$(Get-Timestamp).log"
$unityArgs = @('-executeMethod', 'Game.World.Import.RegionImporter.ImportBatch', '-region', $Region, '-tiers', $Tiers, '-materialTier', $MaterialTier)
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
