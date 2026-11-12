param([string]$Round)
# build_world under the machine-wide heavy-Python slot (coordinator rule), then chunk accounting. Run from anywhere.
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
$out = "artifacts/buildings-r9/$Round"
New-Item -ItemType Directory -Force $out | Out-Null
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
pwsh $slot -Acquire -Pool heavy -Owner claude-buildings-r9 | Out-Host
try {
    # real-data dry run of the plot plan + kit build first (fails fast: ~2 min instead of a broken 9 min build)
    uv run --project tools/worldgen python artifacts/buildings-r9/plan_dry.py "$out/plan.png" *> "$out/plan_dry.txt"
    "plan_dry exit $LASTEXITCODE" | Tee-Object -Append "$out/round.log"
    if ($LASTEXITCODE -ne 0) { "build_world exit SKIPPED (plan_dry failed)" | Tee-Object -Append "$out/round.log"; return }
    $t = Get-Date
    uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$out/build_world.log"
    "build_world exit $LASTEXITCODE, $([int]((Get-Date) - $t).TotalSeconds) s" | Tee-Object -Append "$out/round.log"
    uv run --project tools/worldgen python artifacts/buildings-r9/chunk_mats.py Data/raw/derived/bialystok-industrial-c/world "$out/chunk_mats.json" | Tee-Object -Append "$out/round.log"
    Copy-Item Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json "$out/" -Force
} finally { pwsh $slot -Release -Pool heavy -Owner claude-buildings-r9 | Out-Host }
