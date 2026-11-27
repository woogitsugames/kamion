# tykocin-plaza-s24: asset (Blender) -> tests -> build_world tykocin (private derived) -> import Win64 + visual-qa
param([Parameter(Mandatory)][string]$Out, [switch]$SkipBlender, [string]$Lighting = 'clear',
      [string]$Cameras = 'look_tykocin_plaza_cab_0325,look_tykocin_plaza_photo_0325,look_tykocin_czarniecki,look_tykocin_plaza_se,top_tykocin_rynek,czarniecki_figure_0320b,czarniecki_34_0320b,czarniecki_pedestal_0320b,plaza_furniture_0320b')
$ErrorActionPreference = 'Continue'
$wt = Split-Path (Split-Path $PSScriptRoot)
Set-Location $wt
$logs = "artifacts/tykocin-plaza-s24/logs"
$tag = Split-Path $Out -Leaf
if ((Get-Item Data\raw\derived).LinkType) { throw "Data/raw/derived is a link - this script must only write a private copy" }
if (-not $SkipBlender) {
    & 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe' -b --factory-startup -P tools/blender/world/landmarks/make_czarniecki.py *> "$logs/blender-$tag.log"
    "blender exit $LASTEXITCODE"
    if ($LASTEXITCODE) { exit 1 }
}
uv run --project tools/worldgen python -m pytest tests/gis/test_truss_bridge_0320.py -q *> "$logs/pytest-$tag.log"
"pytest exit $LASTEXITCODE"
if ($LASTEXITCODE) { exit 1 }
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner tykocin-plaza-s24 | Select-Object -Last 1
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region tykocin *> "$logs/build_world-$tag.log"
$bw = $LASTEXITCODE
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner tykocin-plaza-s24 | Select-Object -Last 1
"build_world exit $bw"
if ($bw) { exit 1 }
pwsh -NoProfile -File artifacts/tykocin-plaza-s24/run-unity.ps1 -Region tykocin -Out $Out -Cameras $Cameras -Lighting $Lighting
"REBUILD DONE"
