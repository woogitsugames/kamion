$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\seam-knw-s24'
$log = "$wt\artifacts\seam-knw-s24\build.log"
Set-Location $wt
$env:PYTHONIOENCODING = 'utf-8'
$code = 0
pwsh C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1 -Acquire -Pool heavy -Owner seam-knw-s24 *>> $log
try {
  foreach ($r in 'knyszyn-w', 'knyszyn') {
    "=== build_world $r $(Get-Date -Format s)" | Add-Content $log
    uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $r *>> $log
    if ($LASTEXITCODE -ne 0) { $code = $LASTEXITCODE; "build $r exit $code" | Add-Content $log; break }
    "=== export-route $r $(Get-Date -Format s)" | Add-Content $log
    uv run --project tools/worldgen python scripts/export-route.py --region $r *>> $log
  }
  if ($code -eq 0) {
    "=== route_links $(Get-Date -Format s)" | Add-Content $log
    uv run --project tools/worldgen python tools/worldgen/streaming/route_links.py *>> $log
    "=== probe $(Get-Date -Format s)" | Add-Content $log
    uv run --project tools/worldgen python tools/worldgen/qa/seam_strip_probe.py knyszyn-w knyszyn 760587 611930 612000 artifacts/seam-knw-s24/probe_after.json *>> $log
    uv run --project tools/worldgen python tools/worldgen/qa/seam_strip_probe.py knyszyn-w knyszyn 760587 612050 612100 artifacts/seam-knw-s24/probe_dk65_after.json *>> $log
    "=== combo $(Get-Date -Format s)" | Add-Content $log
    uv run --project tools/worldgen python tools/worldgen/qa/combo_lane_check.py --tiles knyszyn,knyszyn-w --out artifacts/seam-knw-s24/combo_after.json *>> $log
    "combo exit $LASTEXITCODE" | Add-Content $log
  }
} finally {
  pwsh C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1 -Release -Pool heavy -Owner seam-knw-s24 *>> $log
  "DONE code $code $(Get-Date -Format s)" | Add-Content $log
  Set-Content "$wt\artifacts\seam-knw-s24\build.exit" $code
}
