<# .SYNOPSIS
Prepare locally acquired, reviewed Fab assets without downloading or launching Unity.
All licensed products remain ignored. Clean clones retain their previous world.
#>
param(
    [string]$Blender = 'C:\Users\matma\AppData\Local\Programs\Blender4.2\blender-4.2.9-windows-x64\blender.exe',
    [switch]$RefreshTextures,
    [switch]$UpdateHashInventory
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
$prep = @('run', '--project', (Join-Path $RepoRoot 'tools/worldgen'), 'python', (Join-Path $RepoRoot 'tools/worldgen/fab/prepare.py'))
if (Test-Path -LiteralPath $Blender) { $prep += @('--blender', $Blender) }
if ($RefreshTextures) { $prep += '--refresh-textures' }
& uv @prep
if ($LASTEXITCODE -ne 0) { throw 'Fab preparation failed; do not import partial output' }
foreach ($script in @('tools/worldgen/fab_tree_surfaces.py', 'tools/worldgen/fab/drainage_atlas.py')) {
    & uv run --project (Join-Path $RepoRoot 'tools/worldgen') python (Join-Path $RepoRoot $script)
    if ($LASTEXITCODE -ne 0) { throw "$script failed" }
}
if ($UpdateHashInventory) {
    & uv run --project (Join-Path $RepoRoot 'tools/worldgen') python (Join-Path $RepoRoot 'tools/worldgen/fab/audit_inventory.py')
    if ($LASTEXITCODE -ne 0) { throw 'Fab hash-only inventory update failed' }
}
Write-Host 'Prepared local licensed products. Next: uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c'
