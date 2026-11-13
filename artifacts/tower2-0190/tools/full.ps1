# ADR 0190 chain. -Tag base: sources of the three changed files from $BaseRef (restored afterwards), -Tag rN: working tree.
# build_world (heavy slot) -> import + vqa Low clear (48 control cameras, stats.txt) + tower cameras (unity slot)
# -> [-Sbs] SBS Low pairs. Status lines: artifacts/tower2-0190/logs/chain.status
param([string]$Tag = 'r1', [string]$BaseRef = '8145d1d68', [switch]$Sbs, [switch]$SkipBuild)
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\tower2-0190'
$n = 'tower2-0190'
Set-Location $wt
$A = Join-Path $wt "artifacts\$n"; $logs = Join-Path $A 'logs'; $st = Join-Path $logs 'chain.status'
New-Item -ItemType Directory -Force $logs | Out-Null
$R = 'bialystok-industrial-c'
$src = @('tools/worldgen/streetscape/frontage.py', 'tools/worldgen/streetscape/buildings_mesh.py', "Data/Regions/$R/overrides.yaml")
function Mark($m) { "$Tag $m $(Get-Date -Format s)" | Out-File $st -Append -Encoding utf8 }
function Restore { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>&1 | Out-Null }
Mark 'start'
$bw = 0
if (-not $SkipBuild) {
  if ($Tag -eq 'base') {
    if (git status --porcelain -- $src) { Mark 'ABORT: changed sources not committed'; exit 1 }
    git checkout $BaseRef -- $src; git reset -q -- $src; Mark 'sources = base'   # index stays at HEAD: a WIP commit must not take them
  }
  pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $n
  try {
    uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $R *> (Join-Path $logs "$Tag-build_world.log")
    $bw = $LASTEXITCODE
  } finally {
    pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool heavy -Owner $n
    if ($Tag -eq 'base') {
      git checkout HEAD -- $src; Mark 'sources restored'
    }
  }
  Mark "build_world exit $bw"
}
if ($bw -eq 0) {
  if ($Tag -eq 'base') {
    New-Item -ItemType Directory -Force (Join-Path $A 'base/world') | Out-Null
    Copy-Item "Data/raw/derived/$R/world/chunk_6_6*.glb" (Join-Path $A 'base/world') -Force
  }
  pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner $n
  try {
    pwsh -NoProfile -File scripts/import-region.ps1 -Region $R *> (Join-Path $logs "$Tag-import.log")
    $ic = $LASTEXITCODE; Restore; Mark "import exit $ic"
    if ($ic -eq 0) {
      pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -OutputDir (Join-Path $A "$Tag/Low-clear") *> (Join-Path $logs "$Tag-vqa_low.log")
      Mark "vqa Low-clear exit $LASTEXITCODE"; Restore
      $cams = (Get-Content (Join-Path $A 'tower_cameras.json') -Raw | ConvertFrom-Json).cameras.id -join ','
      foreach ($l in 'clear', 'overcast') {
        pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting $l -Gate3 (Join-Path $A 'tower_cameras.json') -Cameras $cams -OutputDir (Join-Path $A "$Tag/tower-Low-$l") *> (Join-Path $logs "$Tag-tower-$l.log")
        Mark "tower cams Low-$l exit $LASTEXITCODE"; Restore
      }
    }
  } finally { pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner $n; Restore }
  if ($Sbs -and $ic -eq 0) {
    pwsh -NoProfile -File scripts/sbs-low-pairs.ps1 -SlotOwner $n -OutputRoot "artifacts/$n/sbs-$Tag" *> (Join-Path $logs "$Tag-sbs.log")
    Mark "sbs exit $LASTEXITCODE"; Restore
  }
}
if ($Tag -eq 'base') { git checkout -- "Data/Regions/$R/generated" 2>&1 | Out-Null }   # base outputs are not committed
Mark 'CHAIN DONE'
