<#
.SYNOPSIS
  ADR 0140: one command for the SBS review set on the current checkout: Low overcast + clear, render-only, all SBS
  cameras (sbs_cameras.json), then photo | render pairs <= 960 px per lighting.
.EXAMPLE
  pwsh scripts/sbs-low-pairs.ps1                                    # artifacts/sbs-low/<sha>/{renders,pairs}/Low-<light>
  pwsh scripts/sbs-low-pairs.ps1 -Before artifacts/sbs-low/<oldsha> # pairs show photo|before over photo|after
  pwsh scripts/sbs-low-pairs.ps1 -SkipRender -OutputRoot <dir>      # re-compose pairs only
.NOTES
  Rendering goes through scripts/sbs-gate3.ps1 -RenderOnly (Unity slot per aspect group, PHONE_RUN wait inside the
  slot script, capture json with input hashes, Unity side effects restored). The preflight refuses a stale world
  (derived GLB sizes vs the committed world_manifest, overrides.yaml hash, Unity import older than the GLBs);
  -SkipPreflight only for a deliberate historical render. Pair composition is light PIL work (no heavy slot).
#>
param(
    [string[]]$Lighting = @('overcast', 'clear'),
    [string]$OutputRoot = '',
    [string]$SlotOwner = '',
    [string]$Before = '',
    [string]$Segment = '',
    [switch]$SkipRender,
    [switch]$SkipPreflight
)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Push-Location $root
try {
    $sha = (& git rev-parse --short=10 HEAD).Trim()
    if (!$OutputRoot) { $OutputRoot = "artifacts/sbs-low/$sha" }
    if (!$SlotOwner) { $SlotOwner = 'sbs-low-' + ((& git branch --show-current).Trim() -replace '[^A-Za-z0-9._-]', '_') }
    $out = [IO.Path]::GetFullPath($OutputRoot, $root)
    if (!$SkipRender) {
        if (!$SkipPreflight) {
            & uv run --project tools/refs python tools/refs/sbs_pairs.py preflight
            if ($LASTEXITCODE -ne 0) { throw 'World on disk is stale against the committed manifest (see STALE lines).' }
        }
        & pwsh -NoProfile -File scripts/sbs-gate3.ps1 -RenderOnly -Tiers Low -Lighting $Lighting -SlotOwner $SlotOwner -OutputRoot $out
        if ($LASTEXITCODE -ne 0) { throw "sbs-gate3 render failed ($LASTEXITCODE)" }
    }
    foreach ($light in $Lighting) {
        $renders = Join-Path $out "renders/Low-$light"
        if (!(Test-Path -LiteralPath $renders)) { throw "No renders: $renders" }
        $pairArgs = @('pairs', '--renders', $renders, '--output', (Join-Path $out "pairs/Low-$light"), '--label', "Low-$light $sha")
        if ($Before) {
            $beforeDir = Join-Path ([IO.Path]::GetFullPath($Before, $root)) "renders/Low-$light"
            $pairArgs += @('--before', $beforeDir)
        }
        if ($Segment) { $pairArgs += @('--segment', $Segment) } else { $pairArgs += '--require-all' }
        & uv run --project tools/refs python tools/refs/sbs_pairs.py @pairArgs
        if ($LASTEXITCODE -ne 0) { throw "Pair composition incomplete: Low-$light" }
    }
    "sbs-low-pairs OK -> $out (renders/, pairs/)"
} finally { Pop-Location }
