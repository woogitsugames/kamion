param([string]$Round)
# build_world under the machine-wide heavy-Python slot (coordinator rule), then chunk accounting. Run from anywhere.
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
$out = "artifacts/buildings-r16/$Round"
New-Item -ItemType Directory -Force $out | Out-Null
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
pwsh $slot -Acquire -Pool heavy -Owner claude-buildings-r8 | Out-Host
try {
    $t = Get-Date
    uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$out/build_world.log"
    "build_world exit $LASTEXITCODE, $([int]((Get-Date) - $t).TotalSeconds) s" | Tee-Object -Append "$out/round.log"
    uv run --project tools/worldgen python artifacts/buildings-r16/chunk_mats.py Data/raw/derived/bialystok-industrial-c/world "$out/chunk_mats.json" | Tee-Object -Append "$out/round.log"
    Copy-Item Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json "$out/" -Force
} finally { pwsh $slot -Release -Pool heavy -Owner claude-buildings-r8 | Out-Host }
