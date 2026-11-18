# ADR 0213: determinism of the regions WITHOUT water (C, Dojlidy): build_world on this branch, then git diff of the
# committed outputs (world_manifest = sha256 of every GLB / instance file; far-field QA + manifest).
$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$L = 'artifacts/water2-0213/logs'; $o = 'water2-0213'
foreach ($r in 'bialystok-industrial-c', 'bialystok-dojlidy') {
  pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner "$o-det" | Out-Null
  "det $r start $(Get-Date -Format s)" | Add-Content "$L/det.status"
  uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $r --context *> "$L/det-$r.log"
  "det $r exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content "$L/det.status"
  pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner "$o-det" | Out-Null
}
git status --short -- Data/Regions/bialystok-industrial-c Data/Regions/bialystok-dojlidy Data/SourceManifests art-source/world > "$L/det-status.txt"
git diff --stat -- Data/Regions/bialystok-industrial-c Data/Regions/bialystok-dojlidy Data/SourceManifests >> "$L/det-status.txt"
"DET DONE $(Get-Date -Format s)" | Add-Content "$L/det.status"
