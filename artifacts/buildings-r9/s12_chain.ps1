param([string]$Round = 'r2c')
# s12: after world.ps1 -> (heavy slot) fidelity + full pytest gis, in parallel with (unity slot) full_round + EditMode.
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
$out = "artifacts/buildings-r9/$Round"
while (-not (Test-Path "$out/round.log") -or -not (Select-String -Path "$out/round.log" -Pattern 'build_world exit' -Quiet)) { Start-Sleep 20 }
if (-not (Select-String -Path "$out/round.log" -Pattern 'build_world exit 0' -Quiet)) { 'CHAIN STOP: build_world failed' | Tee-Object -Append "$out/round.log"; exit 1 }
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$heavy = Start-Job -ArgumentList $wt, $out, $slot -ScriptBlock {
    param($wt, $out, $slot)
    Set-Location $wt
    pwsh $slot -Acquire -Pool heavy -Owner claude-buildings-r9 | Out-Null
    try {
        uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c *> "$out/fidelity.log"
        "fidelity exit $LASTEXITCODE" | Add-Content "$out/round.log"
        uv run --project tools/worldgen python -m pytest tests/gis -q *> "$out/pytest_gis.log"
        "pytest(full) exit $LASTEXITCODE" | Add-Content "$out/round.log"
    } finally { pwsh $slot -Release -Pool heavy -Owner claude-buildings-r9 | Out-Null }
}
pwsh artifacts/buildings-r9/full_round.ps1 -Round $Round
pwsh artifacts/buildings-r9/editmode.ps1 -Round $Round
$heavy | Wait-Job | Out-Null
'CHAIN DONE' | Tee-Object -Append "$out/round.log"
