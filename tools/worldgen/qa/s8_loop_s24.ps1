param(
    [ValidateSet('world', 'unity', 'post', 'pytest')][string]$Phase = 'world',
    [string[]]$Tiles = @('s8-04', 's8-01', 'dk65-01'),
    [string]$Tag = 'r8',
    [int]$UnitySlots = 2, [int]$HeavySlots = 3
)
<#
ADR 0288, s24 continuation (branch s8-loop-s24, new machine). One exit= file per step in
artifacts/s8-loop-s24/run/<step>-<Tag>.exit. Run detached from the worktree root, e.g.
    Start-Process pwsh -ArgumentList '-NoProfile','-File','tools/worldgen/qa/s8_loop_s24.ps1','-Phase','world','-Tiles','s8-04,s8-01,dk65-01'
Phases:
  world  : per tile: [s8-04: build_region (graph_filter drops the underpass way 222577653)] -> build_world (--context
           for s8-04) -> export-route. All five s8 tiles + dk65-01 are rebuilt: main brought generator changes
           (seams-fix ADR 0289, markings/meshing) and the S8 overrides changed (per-way median shift).
  unity  : per tile: import-region Win64 + visual-qa High (artifacts/s8-loop-s24/vqa-<Tag>/<tile>).
  post   : s8_xsec_overrides --check, tile_graph, route_links, catalog, qa.seams, fidelity of the tiles.
  pytest : pytest tests/gis.
#>
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
Set-Location $root
$Tiles = @($Tiles | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$run = Join-Path $root 'artifacts\s8-loop-s24\run'
New-Item -ItemType Directory -Force $run | Out-Null

function Step([string]$Name, [string]$Pool, [scriptblock]$Body) {
    $owner = "s8-loop-s24-$Name-$Tag"
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

$phaseTag = "$Phase-$($Tiles -join '_')"
if ($Phase -eq 'world') {
    foreach ($r in $Tiles) {
        $ok = $true
        if ($r -eq 's8-04') { $ok = (Step "region-$r" 'heavy' { uv run tools/worldgen/build_region.py --region s8-04 }) -eq 0 }
        if ($ok) {
            $wa = @('run', '--project', 'tools/worldgen', 'tools/worldgen/roads/build_world.py', '--region', $r)
            if ($r -eq 's8-04') { $wa += '--context' }
            $ok = (Step "world-$r" 'heavy' { & uv @wa }) -eq 0
        }
        if ($ok) { Step "route-$r" '' { uv run --project tools/worldgen python scripts/export-route.py --region $r } | Out-Null }
    }
}
elseif ($Phase -eq 'unity') {
    foreach ($r in $Tiles) {
        $c = Step "import-$r" 'unity' { pwsh -NoProfile -File scripts/import-region.ps1 -Region $r -BuildTarget Win64 }
        if ($c -eq 0) {
            $out = Join-Path $root "artifacts\s8-loop-s24\vqa-$Tag\$r"
            Step "vqa-$r" 'unity' { pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene "World_${r}_High" -Tier High -Pc -Width 1920 -Height 1080 -Lighting clear -BuildTarget Win64 -OutputDir $out } | Out-Null
        }
    }
}
elseif ($Phase -eq 'post') {
    Step 'streaming' '' {
        uv run --project tools/worldgen python tools/worldgen/qa/s8_xsec_overrides.py --check
        uv run --project tools/worldgen python tools/worldgen/streaming/tile_graph.py
        uv run --project tools/worldgen python tools/worldgen/streaming/route_links.py
        uv run --no-project python scripts/export-region-catalog.py
        uv run --no-project python scripts/export-region-catalog.py --check
    } | Out-Null
    Step 'seams' '' {
        New-Item -ItemType Directory -Force artifacts/s8-loop-s24/seams | Out-Null
        uv run --project tools/worldgen python -m tools.worldgen.qa.seams --tiles s8-01,s8-02,s8-03,s8-04,s8-05,dk65-01,dk65-03 --json artifacts/s8-loop-s24/seams/seams-$Tag.json --md artifacts/s8-loop-s24/seams/seams-$Tag.md
    } | Out-Null
    foreach ($r in $Tiles) {
        Step "fid-$r" 'heavy' { uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region $r --fetch } | Out-Null
    }
}
elseif ($Phase -eq 'pytest') {
    Step 'pytest' 'heavy' { uv run --project tools/worldgen pytest tests/gis -q -p no:cacheprovider } | Out-Null
}
"exit=0" | Set-Content (Join-Path $run "final-$phaseTag-$Tag.exit")
