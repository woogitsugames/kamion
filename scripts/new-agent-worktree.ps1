<#
.SYNOPSIS
  Create an agent worktree from main with the standard data layout (AGENT-RULES):
  copies of Data/raw/derived, Data/raw/cc0, art-source/world/cc0/_raw, art-source/world/megascans,
  game/Assets/_Generated, game/Library; junctions Data/raw/{gugik,osm,refs,mapillary,fab} -> main.
  Before removing such a worktree: unlink junctions (cmd /c rmdir), then git worktree remove --force --force.
.EXAMPLE
  pwsh scripts/new-agent-worktree.ps1 -Name g3b-r2
#>
param(
    [Parameter(Mandatory)][string]$Name,
    [string]$Base = 'main',
    [switch]$NoLibrary
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$wt = Join-Path $root ".claude/worktrees/$Name"
if (Test-Path $wt) { throw "worktree exists: $wt" }
git -C $root worktree add -q $wt -b $Name $Base
if ($LASTEXITCODE) { throw "git worktree add failed" }

$copies = @('Data/raw/derived', 'Data/raw/cc0', 'art-source/world/cc0/_raw', 'art-source/world/megascans', 'game/Assets/_Generated')
if (-not $NoLibrary) { $copies += 'game/Library' }
foreach ($c in $copies) {
    $src = Join-Path $root $c
    if (-not (Test-Path $src)) { "skip (missing in main): $c"; continue }
    $dst = Join-Path $wt $c
    robocopy $src $dst /E /MT:16 /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE): $c" }
    "copied $c"
}
foreach ($j in 'gugik', 'osm', 'refs', 'mapillary', 'fab') {
    $src = Join-Path $root "Data/raw/$j"
    if (-not (Test-Path $src)) { "skip junction (missing): $j"; continue }
    $dst = Join-Path $wt "Data/raw/$j"
    if (Test-Path $dst) { cmd /c rmdir /s /q "$dst" | Out-Null }
    New-Item -ItemType Junction -Path $dst -Target $src | Out-Null
    "junction Data/raw/$j"
}
"READY $wt (branch $Name from $Base)"
