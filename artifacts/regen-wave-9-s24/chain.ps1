param([string]$Chain = 'A')
# Fala 9 (s24, ADR 0339 r2 las z CHM, 0346 bele, 0335 P2, osadzanie propów): claim z kolejki, per kafel build_world --context, export-route, fidelity (pool heavy).
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$env:PYTHONIOENCODING = 'utf-8'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\regen-wave-9-s24'
$main = 'C:\Users\matma\Documents\Claude\kamion'
$out = Join-Path $wt 'artifacts\regen-wave-9-s24'
$claims = Join-Path $out 'claims'
New-Item -ItemType Directory -Force $claims | Out-Null
$status = Join-Path $out 'chain.status'
$tiles = Get-Content (Join-Path $out 'queue.txt') | Where-Object { $_.Trim() -and -not $_.StartsWith('#') }
Set-Location $wt
$owner = "regen-wave-9-s24-$Chain"
foreach ($t in $tiles) {
    if (Test-Path (Join-Path $out 'STOP')) { Add-Content $status "$(Get-Date -Format s) chain=$Chain STOP"; break }
    if (Test-Path (Join-Path $claims "$t.claim")) { continue }
    try { New-Item -ItemType File (Join-Path $claims "$t.claim") -ErrorAction Stop | Out-Null } catch { continue }
    $log = Join-Path $out "logs\$t.log"
    pwsh -NoProfile -File (Join-Path $main 'scripts\unity-slot.ps1') -Acquire -Pool heavy -Owner $owner *>> $log
    $t0 = Get-Date
    uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $t --context *>> $log
    $e1 = $LASTEXITCODE
    $t1 = Get-Date
    uv run --project tools/worldgen python scripts/export-route.py --region $t *>> $log
    $e2 = $LASTEXITCODE
    uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region $t *>> $log
    $e3 = $LASTEXITCODE
    $t2 = Get-Date
    pwsh -NoProfile -File (Join-Path $main 'scripts\unity-slot.ps1') -Release -Pool heavy -Owner $owner *>> $log
    Add-Content $status ("{0} chain={1} tile={2} build_exit={3} route_exit={4} fidelity_exit={5} build_s={6:N0} total_s={7:N0}" -f (Get-Date -Format s), $Chain, $t, $e1, $e2, $e3, ($t1 - $t0).TotalSeconds, ($t2 - $t0).TotalSeconds)
}
Add-Content $status "$(Get-Date -Format s) chain=$Chain DONE"
