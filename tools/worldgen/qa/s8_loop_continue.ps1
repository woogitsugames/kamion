param([string]$Tag = 'r7', [int]$UnitySlots = 2, [int]$HeavySlots = 3, [switch]$SkipUnity)
<#
ADR 0288, continuation of branch s8-loop-s23 after the stop of 2026-11-17 (machine move). Strictly serial, one exit= file
per step in artifacts/s8-loop-s23/run/<step>-<Tag>.exit. Run detached from the checkout root:
    Start-Process pwsh -ArgumentList '-NoProfile','-File','tools/worldgen/qa/s8_loop_continue.ps1'
Needs Data/raw of the tiles (a new machine without Data/raw/derived/<tile>: ingest.py + build_region.py for s8-01..05
and dk65-01 first, then build_world for ALL of them, not only the two below).
Steps: s8-04 build_region (graph_filter drops the underpass way 222577653) -> build_world --context -> export-route;
dk65-01 build_world -> export-route; import Win64 + visual-qa High of both (skipped with -SkipUnity);
tile_graph / route_links / catalog; qa.seams; fidelity (s8-04, dk65-01); pytest tests/gis.
#>
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
Set-Location $root
$run = Join-Path $root 'artifacts\s8-loop-s23\run'
New-Item -ItemType Directory -Force $run | Out-Null

function Step([string]$Name, [string]$Pool, [scriptblock]$Body) {
    $owner = "s8-loop-s23-$Name-$Tag"
    $log = Join-Path $run "$Name-$Tag.log"
    Remove-Item (Join-Path $run "$Name-$Tag.exit") -ErrorAction SilentlyContinue
    $code = 99
    try {
        if ($Pool) {
            $max = if ($Pool -eq 'unity') { $UnitySlots } else { $HeavySlots }
            pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool $Pool -MaxSlots $max -Owner $owner *> (Join-Path $run "$Name-$Tag.slot.log")
        }
        "start $(Get-Date -Format s)" | Set-Content $log
        & $Body *>> $log
        $code = $LASTEXITCODE
        "end $(Get-Date -Format s)" | Add-Content $log
    } finally {
        if ($Pool) { pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool $Pool -Owner $owner *>> (Join-Path $run "$Name-$Tag.slot.log") }
        if ($Pool -eq 'unity') {      # docs/owner/AGENT-RULES.md p.2: undo Unity side effects
            git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
        }
        "exit=$code" | Set-Content (Join-Path $run "$Name-$Tag.exit")
    }
    return $code
}

$ok04 = (Step 'region-s8-04' 'heavy' { uv run tools/worldgen/build_region.py --region s8-04 }) -eq 0
if ($ok04) { $ok04 = (Step 'world-s8-04' 'heavy' { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region s8-04 --context }) -eq 0 }
if ($ok04) { $ok04 = (Step 'route-s8-04' '' { uv run --project tools/worldgen python scripts/export-route.py --region s8-04 }) -eq 0 }
$ok01 = (Step 'world-dk65-01' 'heavy' { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region dk65-01 }) -eq 0
if ($ok01) { $ok01 = (Step 'route-dk65-01' '' { uv run --project tools/worldgen python scripts/export-route.py --region dk65-01 }) -eq 0 }

if (-not $SkipUnity) {
    foreach ($p in @(@('s8-04', $ok04), @('dk65-01', $ok01))) {
        $r = $p[0]
        if (-not $p[1]) { continue }
        $c = Step "import-$r" 'unity' { pwsh -NoProfile -File scripts/import-region.ps1 -Region $r -BuildTarget Win64 }
        if ($c -eq 0) {
            $out = Join-Path $root "artifacts\s8-loop-s23\vqa-$Tag\$r"
            Step "vqa-$r" 'unity' { pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene "World_${r}_High" -Tier High -Pc -Width 1920 -Height 1080 -Lighting clear -BuildTarget Win64 -OutputDir $out } | Out-Null
        }
    }
}

Step 'streaming' '' {
    uv run --project tools/worldgen python tools/worldgen/qa/s8_xsec_overrides.py --check
    uv run --project tools/worldgen python tools/worldgen/streaming/tile_graph.py
    uv run --project tools/worldgen python tools/worldgen/streaming/route_links.py
    python scripts/export-region-catalog.py
    python scripts/export-region-catalog.py --check
} | Out-Null
Step 'seams' '' {
    New-Item -ItemType Directory -Force artifacts/s8-loop-s23/seams | Out-Null
    uv run --project tools/worldgen python -m tools.worldgen.qa.seams --tiles s8-01,s8-02,s8-03,s8-04,s8-05,dk65-01,dk65-03 --json artifacts/s8-loop-s23/seams/seams-final.json --md artifacts/s8-loop-s23/seams/seams-final.md
} | Out-Null
foreach ($r in 's8-04', 'dk65-01') {
    Step "fid-$r" 'heavy' { uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region $r --fetch } | Out-Null
}
Step 'pytest' 'heavy' { uv run --project tools/worldgen pytest tests/gis -q -p no:cacheprovider } | Out-Null
"exit=0" | Set-Content (Join-Path $run "final-$Tag.exit")
