# ADR 0210: rebuild regions WITHOUT the water stage on this branch; their committed outputs must stay byte-identical.
param([string[]]$Regions = @('bialystok-industrial-c', 'bialystok-dojlidy'))
$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$L = 'artifacts/water-0210/logs'; $st = "$L/determinism.status"; $o = 'water-0210'
foreach ($r in $Regions) {
  pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $o | Out-Null
  "world-$r start $(Get-Date -Format s)" | Add-Content $st
  uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $r *> "$L/det-$r.log"
  "world-$r exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
  pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $o | Out-Null
  $d = git status --porcelain -- "Data/Regions/$r" "game/Assets/_Project/UI/Resources/CabDisplay/Nav" "Data/SourceManifests/$r-far-field.manifest.json"
  "status-${r}: $(if ($d) { $d -join ' | ' } else { 'CLEAN' })" | Add-Content $st
}
"DET DONE $(Get-Date -Format s)" | Add-Content $st
