param([string]$Round, [string]$Only = '', [string]$Configs = 'High:overcast,Low:overcast,High:clear', [switch]$SkipWorld)
# texture sets -> build_world -> chunk accounting -> import + renders (run_round.ps1). Run from anywhere.
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
$out = "artifacts/buildings-r13/$Round"
New-Item -ItemType Directory -Force $out | Out-Null
if ($Only) {
    $t = Get-Date
    uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only $Only *> "$out/build_all.log"
    "build_all ($Only) exit $LASTEXITCODE, $([int]((Get-Date) - $t).TotalSeconds) s" | Tee-Object -Append "$out/round.log"
    if ($LASTEXITCODE -ne 0) { exit 1 }
    # import-region rebuilds ALL sets (~5 min) when any _src/*.py is newer than a PNG; the other generators did not
    # change (deterministic output), so mark their PNGs as current
    $now = Get-Date
    Get-ChildItem art-source/world/materials -Recurse -Filter *.png | Where-Object { $_.FullName -notmatch '_renders|_src' } | ForEach-Object { $_.LastWriteTime = $now }
}
if (-not $SkipWorld) {
    $t = Get-Date
    uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$out/build_world.log"
    "build_world exit $LASTEXITCODE, $([int]((Get-Date) - $t).TotalSeconds) s" | Tee-Object -Append "$out/round.log"
    if ($LASTEXITCODE -ne 0) { exit 1 }
    uv run --project tools/worldgen python artifacts/buildings-r13/chunk_mats.py Data/raw/derived/bialystok-industrial-c/world "$out/chunk_mats.json" | Tee-Object -Append "$out/round.log"
    Copy-Item Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json "$out/" -Force
}
pwsh artifacts/buildings-r13/run_round.ps1 -Round $Round -Configs $Configs *> "$out/round.out"
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings 2>$null
