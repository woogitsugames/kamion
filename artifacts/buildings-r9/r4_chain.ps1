param([string]$Round = 'r4', [switch]$SkipBase)
# s13 r4 (leader decision B), after the second `git merge main`:
#  (1) base2 = the CONTENT of main (tools/worldgen, art-source/world, Data/Regions, Data/SourceManifests checked out from
#      `main` into this worktree, built and imported here) -> Low overcast control cameras + 8 High review cameras +
#      Low review cameras; then the paths are restored to HEAD (the worktree must be committed and clean before the run);
#  (2) r4 = this branch: build_all, build_world, export-route, fidelity, import + renders, full pytest gis, EditMode.
# The heavy slot is held from a build_world to the end of its import (nobody else rebuilds in between on this machine
# budget). Log: <round>/round.log (ends with CHAIN DONE). Base log: base2/round.log.
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
$A = 'artifacts/buildings-r9'
$R = 'bialystok-industrial-c'
$out = "$A/$Round"
$only = 'r16_drive_0,r16_drive_3,r17_street_0a,r17_street_1a,r17_street_3a,r17_over_0,r15_front_brick_bars,r16_garden_2'
$paths = @('tools/worldgen', 'art-source/world', 'Data/Regions', 'Data/SourceManifests', 'scripts/export-route.py')
New-Item -ItemType Directory -Force $out, "$A/base2" | Out-Null
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
if (-not $SkipBase) {
    if (git status --porcelain -- @paths) { 'CHAIN STOP: worktree not clean' | Tee-Object -Append "$out/round.log"; exit 1 }
    "base2 main = $(git rev-parse --short main)" | Tee-Object -Append "$A/base2/round.log"
    pwsh $slot -Acquire -Pool heavy -Owner claude-buildings-r9 | Out-Host
    try {
        git checkout main -- @paths
        uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py *> "$A/base2/build_all.log"
        "build_all exit $LASTEXITCODE" | Tee-Object -Append "$A/base2/round.log"
        $t = Get-Date
        uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $R *> "$A/base2/build_world.log"
        "build_world exit $LASTEXITCODE, $([int]((Get-Date) - $t).TotalSeconds) s" | Tee-Object -Append "$A/base2/round.log"
        Copy-Item Data/Regions/$R/generated/streetscape_qa.json "$A/base2/" -Force
        uv run --project tools/worldgen python scripts/export-route.py --region $R *> "$A/base2/export_route.log"
        pwsh $A/run_round.ps1 -Round base2 -Configs 'Low:overcast' *> "$A/base2.round.out"
    } finally {
        git checkout HEAD -- @paths
        git status --porcelain -- @paths | Out-File "$A/base2/restore_status.txt"
        pwsh $slot -Release -Pool heavy -Owner claude-buildings-r9 | Out-Host
    }
    pwsh $A/extra.ps1 -Round base2 -Scene WorldC_High -Tier High -Sub extra_hc -Only $only *>> "$A/base2.round.out"
    pwsh $A/extra.ps1 -Round base2 -Tier Low -Sub extra_low *>> "$A/base2.round.out"
    'BASE2 DONE' | Tee-Object -Append "$out/round.log"
}
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
    pwsh $A/run_round.ps1 -Round $Round -Configs 'Low:overcast' *> "$A/$Round.round.out"
    'IMPORT DONE' | Add-Content "$out/round.log"
    uv run --project tools/worldgen python -m pytest tests/gis -q -p no:cacheprovider *> "$out/pytest_gis.log"
    "pytest(gis) exit $LASTEXITCODE" | Tee-Object -Append "$out/round.log"
} finally { pwsh $slot -Release -Pool heavy -Owner claude-buildings-r9 | Out-Host }
pwsh $A/extra.ps1 -Round $Round -Scene WorldC_High -Tier High -Sub extra_hc -Only $only *>> "$A/$Round.round.out"
pwsh $A/extra.ps1 -Round $Round -Tier Low -Sub extra_low *>> "$A/$Round.round.out"
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings 2>$null
'ROUND DONE' | Tee-Object -Append "$out/round.log"
pwsh $A/editmode.ps1 -Round $Round
'CHAIN DONE' | Add-Content "$out/round.log"
