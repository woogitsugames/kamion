# c-regen-s22: after merging origin/main (tunnel, rail, dk65-r4, win-build): determinism check - rebuild C + Dojlidy, refresh fidelity.
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\c-regen-s22'; Set-Location $wt
$o = 'artifacts/c-regen-s22/postmerge'; New-Item -ItemType Directory -Force $o | Out-Null
$st = "$o/postmerge.status"; Remove-Item "$o/postmerge.done" -ErrorAction SilentlyContinue
"start $(Get-Date -Format s)" | Set-Content $st
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner c-regen-s22 | Out-Null
"slot $(Get-Date -Format s)" | Add-Content $st
function Step($name, [scriptblock]$b) { & $b *> "$o/$name.log"; "$name exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st }
try {
  foreach ($r in 'bialystok-industrial-c', 'bialystok-dojlidy') {
    Step "build_world-$r" { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $r }
    Step "fidelity-$r" { uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region $r }
  }
  Step "pytest-sel" { uv run --project tools/worldgen pytest tests/gis -q -p no:cacheprovider -k "0219 or far_field or 0216 or budget_0221 or report_not_stale or streetscape or world_v31 or forest_0187 or tunnel or rail or determinism" }
} finally { pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner c-regen-s22 | Out-Null }
"DONE $(Get-Date -Format s)" | Add-Content $st; 'done' | Set-Content "$o/postmerge.done"
