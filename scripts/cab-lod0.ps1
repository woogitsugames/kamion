<#
.SYNOPSIS
  Preflight for the cab interior LOD0 FBX (art-source/truck/interior/export/SM_CabInterior_LOD0.fbx, ~8.6 MB, outside git:
  art-source/truck/interior/.gitignore). TruckAssetBuilder needs it to build the TRAKT prefab; without it a fresh checkout
  falls back to the graybox (DrivingLab / region scenes) or fails (TruckAssetBuilder.BuildBatch).
.DESCRIPTION
  Exit 0: the FBX is present, or the generated TRAKT prefab already exists (the builder will not run).
  Exit 2: both missing - prints the command that regenerates it (-Build).
  -Build: regenerates it with Blender (make_textures.py, then a6_export.py --lods 0 into a temp folder, copy the FBX);
  measured 8.5 min CPU on the s24 PC (artifacts/full-build-s24/STATUS.md). The committed textures stay byte-identical
  (make_textures.py is deterministic; build-fix-s24).
  -Require: exit 2 when the FBX is missing even if the prefab exists (before an explicit TRAKT rebuild).
.EXAMPLE
  pwsh scripts/cab-lod0.ps1            # check (setup-project.ps1, build-lab.ps1, import-region.ps1 call this)
  pwsh scripts/cab-lod0.ps1 -Build     # regenerate the FBX
#>
param([switch]$Build, [switch]$Require)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$fbx = Join-Path $root 'art-source/truck/interior/export/SM_CabInterior_LOD0.fbx'
$prefab = Join-Path $root 'game/Assets/_Generated/Truck/Tractor4x2_TRAKT.prefab'

if (Test-Path -LiteralPath $fbx) { Write-Host "[cab-lod0] OK $fbx"; exit 0 }
if (-not $Build) {
    if ((Test-Path -LiteralPath $prefab) -and -not $Require) {
        Write-Host "[cab-lod0] FBX missing, TRAKT prefab present (builder will not run): $prefab"
        exit 0
    }
    Write-Host "[cab-lod0] MISSING $fbx" -ForegroundColor Red
    Write-Host "  The cab interior LOD0 is generated outside git; without it TruckAssetBuilder fails and driving scenes get the graybox." -ForegroundColor Red
    Write-Host "  Regenerate (~9 min, Blender 4.2):  pwsh scripts/cab-lod0.ps1 -Build" -ForegroundColor Yellow
    exit 2
}

$blender = (Get-Command blender -ErrorAction SilentlyContinue).Source
if (-not $blender) {
    $blender = @("$env:ProgramFiles\Blender Foundation\Blender 4.2\blender.exe",
                 "$env:LOCALAPPDATA\Programs\Blender4.2\blender-4.2.9-windows-x64\blender.exe") |
        Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $blender) { throw "Blender 4.2 not found (PATH, Program Files, LOCALAPPDATA)" }
$tmp = Join-Path ([IO.Path]::GetTempPath()) "kamion-cab-lod0-$PID"
New-Item -ItemType Directory -Force $tmp | Out-Null
$logDir = Join-Path $root 'artifacts/logs'
New-Item -ItemType Directory -Force $logDir | Out-Null
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
Push-Location $root
try {
    # Untracked detail maps (*_var/_nrm/_orm, grime) that a6_export reads; committed PNGs are rewritten byte-identical.
    & uv run --no-project --with pillow --with numpy python tools/blender/truck/interior/make_textures.py *> (Join-Path $logDir "cab-lod0-textures-$ts.log")
    if ($LASTEXITCODE) { throw "make_textures.py failed ($LASTEXITCODE), log artifacts/logs/cab-lod0-textures-$ts.log" }
    $blog = Join-Path $logDir "cab-lod0-blender-$ts.log"
    & $blender -b --factory-startup --python tools/blender/truck/interior/a6_export.py -- --lods 0 --out $tmp --manifest (Join-Path $tmp 'cab_interior_manifest.json') *> $blog
    if ($LASTEXITCODE) { throw "a6_export.py failed ($LASTEXITCODE), log $blog" }
    $out = Join-Path $tmp 'SM_CabInterior_LOD0.fbx'
    if (-not (Test-Path -LiteralPath $out)) { throw "a6_export.py wrote no SM_CabInterior_LOD0.fbx, log $blog" }
    Copy-Item -LiteralPath $out -Destination $fbx -Force
    Write-Host "[cab-lod0] built $fbx ($([math]::Round((Get-Item $fbx).Length / 1MB, 1)) MB), log $blog"
    $changed = git status --porcelain -- art-source/truck/interior
    if ($changed) { Write-Host "[cab-lod0] WARNING tracked files changed by the regeneration:`n$changed" -ForegroundColor Yellow }
}
finally {
    Pop-Location
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
exit 0
