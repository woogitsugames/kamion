param([string]$Round = 'r2')
# r2: (a) base = the import of main (with ADR 0124) copied over _Generated and rendered without import, in parallel with
# (b) build_world of this branch in the heavy slot; then import + renders of the round, then fidelity + full pytest gis
# (heavy slot) in parallel with EditMode (unity slot). Run from anywhere.
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
$A = 'artifacts/buildings-r9'
$main = 'C:\Users\matma\Documents\Claude\kamion'
New-Item -ItemType Directory -Force "$A/$Round" | Out-Null
$world = Start-Job -ArgumentList $wt, $Round -ScriptBlock { param($wt, $Round) Set-Location $wt; pwsh artifacts/buildings-r9/world.ps1 -Round $Round *> "artifacts/buildings-r9/$Round.world.out" }
# (a) base
robocopy "$main\game\Assets\_Generated" "$wt\game\Assets\_Generated" /MIR /MT:16 /NFL /NDL /NJH /NP /R:1 /W:1 | Select-Object -Last 3 | Out-File "$A/base_copy.txt"
Remove-Item "$A/base" -Recurse -Force -ErrorAction SilentlyContinue
pwsh $A/run_round.ps1 -Round base -Configs 'Low:overcast' -SkipImport *> "$A/base.round.out"
pwsh $A/extra.ps1 -Round base -Tier Low -Sub extra_low *>> "$A/base.round.out"
pwsh $A/extra.ps1 -Round base -Scene WorldC_High -Tier High -Sub extra_hc -Only 'r16_drive_0,r16_drive_3,r17_street_0a,r17_street_1a,r17_street_3a,r17_over_0,r15_front_brick_bars,r16_garden_2' *>> "$A/base.round.out"
'BASE DONE' | Add-Content "$A/$Round/round.log"
$world | Wait-Job | Out-Null
if (-not (Select-String -Path "$A/$Round/round.log" -Pattern 'build_world exit 0' -Quiet)) { 'CHAIN STOP: build_world failed' | Add-Content "$A/$Round/round.log"; exit 1 }
$slot = "$main\scripts\unity-slot.ps1"
$heavy = Start-Job -ArgumentList $wt, "$A/$Round", $slot -ScriptBlock {
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
pwsh $A/round.ps1 -Round $Round -SkipWorld
pwsh $A/editmode.ps1 -Round $Round
$heavy | Wait-Job | Out-Null
'CHAIN DONE' | Add-Content "$A/$Round/round.log"
