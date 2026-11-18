<#
.SYNOPSIS
  Re-pin the GUIDs of the generated art prefabs (D84) in a checkout's Assets/_Generated, as text, before Unity opens it.
.DESCRIPTION
  Assets/_Generated is outside git. DrivingLab.unity (git) and the generated world scenes reference the TRAKT tractor and
  the curtainsider trailer by fixed GUIDs (DrivingVehiclePrefabs.TractorGuid / TrailerGuid). A checkout whose prefab was
  first built before the pin got a random GUID; DrivingVehiclePrefabs.PinGuid fixes it only when the asset builder runs
  again, and EnsureBuilt skips an existing prefab - so a stale .meta (main had cac16030... for the trailer, 18.11) was
  copied into every new agent worktree by new-agent-worktree.ps1 and failed ArtPrefabs_HavePinnedGuids there.
  This script does what PinGuid does, without Unity: rewrite the guid line of the prefab .meta and the references to the
  old GUID in the generated scenes (*.unity under Assets/_Generated/World). Run it only while no Unity has the project
  open (the AssetDatabase would keep the old GUID until the next refresh). GUIDs and paths are read from the C# sources,
  the single place they are defined. Exit 0 = all pinned (or nothing to pin), 1 = error.
.EXAMPLE
  pwsh scripts/repin-generated-guids.ps1 -Root .claude/worktrees/my-agent
#>
param(
    # Checkout root (repo root containing game/). Default: this repo.
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)
$ErrorActionPreference = 'Stop'
$game = Join-Path $Root 'game'
$setup = Join-Path $game 'Assets/_Project/Editor/Setup'
$src = Get-Content -Raw (Join-Path $setup 'DrivingVehiclePrefabs.cs')

function ConstOf([string]$text, [string]$name) {
    $m = [regex]::Match($text, "const string $name\s*=\s*`"([^`"]+)`"")
    if (-not $m.Success) { throw "const $name not found" }
    $m.Groups[1].Value
}
function PrefabPathOf([string]$file) {
    $t = Get-Content -Raw (Join-Path $setup $file)
    $root = ConstOf $t 'Root'
    $m = [regex]::Match($t, 'const string PrefabPath\s*=\s*Root\s*\+\s*"([^"]+)"')
    if (-not $m.Success) { throw "PrefabPath not found in $file" }
    $root + $m.Groups[1].Value
}

$pins = @(
    @{ Path = (PrefabPathOf 'TruckAssetBuilder.cs'); Guid = (ConstOf $src 'TractorGuid') },
    @{ Path = (PrefabPathOf 'TrailerAssetBuilder.cs'); Guid = (ConstOf $src 'TrailerGuid') }
)
$sceneRoot = Join-Path $game 'Assets/_Generated/World'
foreach ($p in $pins) {
    $meta = Join-Path $game ($p.Path + '.meta')
    if (-not (Test-Path $meta)) { "skip (not built): $($p.Path)"; continue }
    $text = [IO.File]::ReadAllText($meta)
    $m = [regex]::Match($text, '(?m)^guid: ([0-9a-f]{32})\s*$')
    if (-not $m.Success) { throw "no guid line in $meta" }
    $old = $m.Groups[1].Value
    if ($old -eq $p.Guid) { "ok $($p.Path) $old"; continue }
    [IO.File]::WriteAllText($meta, $text.Substring(0, $m.Groups[1].Index) + $p.Guid + $text.Substring($m.Groups[1].Index + 32))
    $scenes = 0
    if (Test-Path $sceneRoot) {
        foreach ($f in Get-ChildItem $sceneRoot -Recurse -Filter *.unity -File) {
            $t = [IO.File]::ReadAllText($f.FullName)
            if (-not $t.Contains("guid: $old")) { continue }
            [IO.File]::WriteAllText($f.FullName, $t.Replace("guid: $old", "guid: $($p.Guid)"))
            $scenes++
        }
    }
    "re-pinned $($p.Path): $old -> $($p.Guid) ($scenes generated scenes rewritten)"
}
