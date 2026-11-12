param([string]$Round = 'r3', [switch]$SkipUnity)
# s13, after `git merge main`: regeneration like artifacts/integration-s12/regen.sh in ONE heavy-slot hold (build_all,
# build_world, export-route, fidelity, pytest gis), then import + Low overcast control cameras + a few review cameras
# + EditMode. Log: <round>/round.log (ends with CHAIN DONE).
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
$A = 'artifacts/buildings-r9'
$out = "$A/$Round"
$R = 'bialystok-industrial-c'
New-Item -ItemType Directory -Force $out | Out-Null
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
pwsh $slot -Acquire -Pool heavy -Owner claude-buildings-r9 | Out-Host
try {
    uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py *> "$out/build_all.log"
    "build_all exit $LASTEXITCODE" | Tee-Object -Append "$out/round.log"
    $t = Get-Date
    uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $R *> "$out/build_world.log"
    "build_world exit $LASTEXITCODE, $([int]((Get-Date) - $t).TotalSeconds) s" | Tee-Object -Append "$out/round.log"
    uv run --project tools/worldgen python $A/chunk_mats.py Data/raw/derived/$R/world "$out/chunk_mats.json" | Tee-Object -Append "$out/round.log"
    Copy-Item Data/Regions/$R/generated/streetscape_qa.json "$out/" -Force
    uv run --project tools/worldgen python scripts/export-route.py --region $R *> "$out/export_route.log"
    "export-route exit $LASTEXITCODE" | Tee-Object -Append "$out/round.log"
    uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region $R *> "$out/fidelity.log"
    "fidelity exit $LASTEXITCODE" | Tee-Object -Append "$out/round.log"
    uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider *> "$out/pytest_gis.log"
    "pytest(gis) exit $LASTEXITCODE" | Tee-Object -Append "$out/round.log"
} finally { pwsh $slot -Release -Pool heavy -Owner claude-buildings-r9 | Out-Host }
if (-not $SkipUnity) {
    pwsh $A/round.ps1 -Round $Round -SkipWorld -Only 'r16_drive_0,r16_drive_3,r17_street_0a,r17_street_1a,r17_street_3a,r17_over_0,r15_front_brick_bars,r16_garden_2'
    pwsh $A/editmode.ps1 -Round $Round
}
'CHAIN DONE' | Add-Content "$out/round.log"
