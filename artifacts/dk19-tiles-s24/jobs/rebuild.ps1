# dk19-tiles-s24: rebuild bojary + mickiewicza (world --context, fidelity, export-route), then streaming data.
$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s24'
Set-Location $wt
$st = "$wt\artifacts\dk19-tiles-s24\jobs\rebuild.status"
$logd = "$wt\artifacts\logs"; New-Item -ItemType Directory -Force $logd | Out-Null
"start $(Get-Date -Format s)" | Set-Content $st
function Step($name, [scriptblock]$b) {
  $log = "$logd\dk19-s24-$name.log"
  & $b *> $log
  $ec = $LASTEXITCODE
  "$name exit=$ec $(Get-Date -Format s)" | Add-Content $st
  return $ec
}
foreach ($t in 'bojary','mickiewicza') {
  pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -MaxSlots 3 -Owner "dk19-s24-$t" | Out-Null
  Step "world-$t" { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region "bialystok-$t" --context } | Out-Null
  Step "fidelity-$t" { uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region "bialystok-$t" } | Out-Null
  Step "route-$t" { uv run --project tools/worldgen python scripts/export-route.py --region "bialystok-$t" } | Out-Null
  pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner "dk19-s24-$t" | Out-Null
}
Step 'route_links' { uv run --project tools/worldgen python tools/worldgen/streaming/route_links.py } | Out-Null
Step 'tile_graph' { uv run --project tools/worldgen python tools/worldgen/streaming/tile_graph.py } | Out-Null
Step 'catalog' { uv run --no-project python scripts/export-region-catalog.py --check } | Out-Null
"DONE exit=0 $(Get-Date -Format s)" | Add-Content $st
