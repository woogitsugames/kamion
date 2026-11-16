# c-regen2-s23 stage 2, step 0: data the bare `git worktree add` did not bring (scripts/new-agent-worktree.ps1 layout).
# Copies from main: Data/raw/derived (14.5 GB), game/Assets/_Generated (13.3 GB), game/Library. Disk IO only.
# Without Library every Unity step starts with a full import; without megascans the import falls back silently
# (megascans, cc0 and cc0/_raw were copied in stage 1 - verified below).
param([switch]$RegionsOnly)   # default: whole Data/raw/derived (14.5 GB; its root holds the layer caches *.pkl build_region reuses)
. "$PSScriptRoot/_common.ps1"
Init-Status "$Art/prep" 'prep.status'
function Copy-Dir([string]$rel) {
    $src = Join-Path $Main $rel; $dst = Join-Path $Wt $rel
    if (-not (Test-Path $src)) { "skip (missing in main) $rel" | Add-Content $St; return }
    robocopy $src $dst /E /MT:16 /R:1 /W:1 /NFL /NDL /NJH /NJS /NP *> "$O/robocopy-$($rel -replace '[\\/]', '_').log"
    "copy $rel robocopy=$LASTEXITCODE (0-7 ok, >=8 error) $(Get-Date -Format s)" | Add-Content $St
}
$derived = @(if (-not $RegionsOnly) { 'Data/raw/derived' } else { @('Data/raw/derived/cache') + @($Regions | ForEach-Object { "Data/raw/derived/$_" }) })
foreach ($d in @($derived) + @('game/Assets/_Generated', 'game/Library')) { Copy-Dir $d }   # @() - a lone string + array would concatenate text (lead s23 fix)
foreach ($j in 'gugik', 'osm', 'refs', 'mapillary', 'fab') {
    $p = "Data/raw/$j"; $ok = (Test-Path $p) -and ((Get-Item $p).Attributes -band [IO.FileAttributes]::ReparsePoint)
    "junction $p ok=$([bool]$ok)" | Add-Content $St
}
foreach ($c in 'art-source/world/megascans', 'art-source/world/cc0/_raw', 'Data/raw/cc0') { "present $c = $(Test-Path $c) files=$((Get-ChildItem $c -Recurse -File -ErrorAction SilentlyContinue).Count)" | Add-Content $St }
"free C: $([int]((Get-PSDrive C).Free / 1GB)) GB" | Add-Content $St
Finish 'prep.done'
