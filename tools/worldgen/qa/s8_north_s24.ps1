param(
    [ValidateSet('ingest', 'world', 'unity', 'post', 'pytest', 'editmode')][string]$Phase = 'world',
    [string[]]$Tiles = @('dk8-wasilkow-01','dk8-wasilkow-02','dk8-wasilkow-03','dk8-korycin-01'),
    [string]$Tag = 'r1',
    [switch]$Context,
    [int]$UnitySlots = 2, [int]$HeavySlots = 3
)
<#
s8-north-s24 (owner D93 p.4, D95 p.4, D63): DK8 north out of Bialystok -> Wasilkow junction -> towards Korycin, tiles of
tools/worldgen/qa/dk8_north_plan.py (lattice (0,1)..(0,4)). Same step order as tools/worldgen/qa/dk8_s8_s24.ps1
(ADR 0292); one exit= file per step in artifacts/s8-north-s24/run/<step>-<Tag>.exit. Run detached from the worktree root:
    Start-Process pwsh -ArgumentList '-NoProfile','-File','tools/worldgen/qa/s8_north_s24.ps1','-Phase','world'
Phases: ingest | world (build_region -> build_world [--context] -> export-route) | unity (import Win64 + visual-qa High)
        | post (tile_graph, route_links, catalog, qa.seams, fidelity) | pytest | editmode.
#>
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
Set-Location $root
$env:PYTHONUTF8 = '1'
$Tiles = @($Tiles | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$run = Join-Path $root 'artifacts\s8-north-s24\run'
New-Item -ItemType Directory -Force $run | Out-Null

function Step([string]$Name, [string]$Pool, [scriptblock]$Body) {
    $owner = "s8-north-s24-$Name-$Tag"
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
if ($Phase -eq 'ingest') {
    foreach ($r in $Tiles) { Step "ingest-$r" '' { uv run --project tools/worldgen tools/worldgen/ingest.py --region $r } | Out-Null }
}
elseif ($Phase -eq 'world') {
    foreach ($r in $Tiles) {
        $ok = (Step "region-$r" '' { uv run tools/worldgen/build_region.py --region $r }) -eq 0
        if ($ok) {
            $wa = @('run', '--project', 'tools/worldgen', 'tools/worldgen/roads/build_world.py', '--region', $r)
            if ($Context) { $wa += '--context' }
            $ok = (Step "world-$r" 'heavy' { & uv @wa }) -eq 0
        }
        if ($ok) { Step "route-$r" '' { uv run --project tools/worldgen python scripts/export-route.py --region $r } | Out-Null }
    }
}
elseif ($Phase -eq 'unity') {
    foreach ($r in $Tiles) {
        $c = Step "import-$r" 'unity' { pwsh -NoProfile -File scripts/import-region.ps1 -Region $r -BuildTarget Win64 }
        if ($c -eq 0) {
            $out = Join-Path $root "artifacts\s8-north-s24\vqa-$Tag\$r"
            Step "vqa-$r" 'unity' { pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene "World_${r}_High" -Tier High -Pc -Width 1920 -Height 1080 -Lighting clear -BuildTarget Win64 -OutputDir $out } | Out-Null
        }
    }
}
elseif ($Phase -eq 'post') {
    Step 'streaming' '' {
        uv run --project tools/worldgen python tools/worldgen/streaming/tile_graph.py
        uv run --project tools/worldgen python tools/worldgen/streaming/route_links.py
        uv run --no-project python scripts/export-region-catalog.py
        uv run --no-project python scripts/export-region-catalog.py --check
    } | Out-Null
    Step 'seams' '' {
        New-Item -ItemType Directory -Force artifacts/s8-north-s24/seams | Out-Null
        uv run --project tools/worldgen python -m tools.worldgen.qa.seams --tiles bialystok-industrial-c,dk8-wasilkow-01,dk8-wasilkow-02,dk8-wasilkow-03,dk8-korycin-01 --json artifacts/s8-north-s24/seams/seams-$Tag.json --md artifacts/s8-north-s24/seams/seams-$Tag.md
    } | Out-Null
    foreach ($r in $Tiles) {
        Step "fid-$r" 'heavy' { uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region $r --fetch } | Out-Null
    }
}
elseif ($Phase -eq 'pytest') {
    Step 'pytest' 'heavy' { uv run --project tools/worldgen pytest tests/gis -q -p no:cacheprovider } | Out-Null
}
elseif ($Phase -eq 'editmode') {
    Step 'editmode' 'unity' { pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode -BuildTarget Win64 } | Out-Null
}
"exit=0" | Set-Content (Join-Path $run "final-$phaseTag-$Tag.exit")
