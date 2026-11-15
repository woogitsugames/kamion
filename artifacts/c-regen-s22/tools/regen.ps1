# c-regen-s22: ONE regeneration of C + Dojlidy after merging qa-tools-0219 (#95) and summer-cd-0216b (#120). Heavy slot.
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\c-regen-s22'; Set-Location $wt
$o = 'artifacts/c-regen-s22/regen'; New-Item -ItemType Directory -Force $o | Out-Null
$st = "$o/regen.status"; Remove-Item "$o/regen.done" -ErrorAction SilentlyContinue
"start $(Get-Date -Format s)" | Set-Content $st
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner c-regen-s22 | Out-Null
"slot $(Get-Date -Format s)" | Add-Content $st
function Step($name, [scriptblock]$b) { & $b *> "$o/$name.log"; "$name exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st }
try {
  foreach ($r in 'bialystok-industrial-c', 'bialystok-dojlidy') {
    Step "build_region-$r" { uv run tools/worldgen/build_region.py --region $r }
    Step "build_world-$r" { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $r }
    Step "fidelity-$r" { uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region $r }
    Step "export_route-$r" { uv run --project tools/worldgen python scripts/export-route.py --region $r }
    Step "lamp_audit-$r" { uv run --project tools/worldgen python tools/worldgen/qa/lamp_family_audit.py --region $r }
  }
} finally { pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner c-regen-s22 | Out-Null }
"DONE $(Get-Date -Format s)" | Add-Content $st; 'done' | Set-Content "$o/regen.done"
