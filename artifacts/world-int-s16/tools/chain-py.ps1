param([string[]]$Steps = @('build_all','build_world','export_route','fidelity'))
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\world-int-s16'
$logs = Join-Path $wt 'artifacts\world-int-s16\logs'
Set-Location $wt
$R = 'bialystok-industrial-c'
$cmds = [ordered]@{
  build_all    = { uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py }
  build_world  = { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $R }
  export_route = { uv run --project tools/worldgen python scripts/export-route.py --region $R }
  fidelity     = { uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region $R }
}
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner world-int-s16
try {
  foreach ($s in ($Steps -split ",")) {
    $log = Join-Path $logs "$s.log"
    $t0 = Get-Date
    "=== $s start $(Get-Date -Format s)" | Out-File $log -Encoding utf8
    & $cmds[$s] *>&1 | Out-File $log -Append -Encoding utf8
    $code = $LASTEXITCODE
    "=== $s exit $code $([int]((Get-Date) - $t0).TotalSeconds) s" | Out-File $log -Append -Encoding utf8
    "$s exit $code" | Out-File (Join-Path $logs 'chain-py.status') -Append -Encoding utf8
    if ($code -ne 0) { break }
  }
} finally {
  pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool heavy -Owner world-int-s16
  "CHAIN DONE $(Get-Date -Format s)" | Out-File (Join-Path $logs 'chain-py.status') -Append -Encoding utf8
}
