<#
  pc-budget-s23 (D83): sweep frame time vs tris/draws per tier on the RTX 5070 dev machine ("emulacja" klas D74, D76).
  Runs scripts/pc-metrics.ps1 (main repo) for each point x config. Output: artifacts/pc-budget-s23/runs/<point>__<cfg>/
  Resumable: a run dir with run.json is skipped. Progress: artifacts/pc-budget-s23/run.status (+ live file).
  Do NOT start while Unity.exe / build_world.py run (watch.ps1 guards this; run.ps1 re-checks before every run and pauses).
#>
param(
    [string]$Exe = 'C:\Users\matma\Documents\Claude\kamion\artifacts\win\kamion-0.1.0-e28533ca31-regions\Kamion.exe',
    [int]$DurationSeconds = 40,
    [switch]$DryRun
)
$ErrorActionPreference = 'Continue'
$Main = 'C:\Users\matma\Documents\Claude\kamion'
$Root = Join-Path $Main 'artifacts\pc-budget-s23'
$Runs = Join-Path $Root 'runs'
$Status = Join-Path $Root 'run.status'
$Live = Join-Path $Main 'artifacts\live\pc-budget-s23.md'
New-Item -ItemType Directory -Force $Runs | Out-Null

# Points: region scene + route_s (truck spawned standing on the start route, chase camera = default view).
# Spread: dense city (C, Dojlidy, Maczka, Kleeberga, Knyszynska) -> town (Knyszyn, Tykocin, Monki) -> open road (dk65, knyszyn-w).
$Points = @(
    @{ id = 'c-300';          scene = 'bialystok-industrial-c'; s = 300 },
    @{ id = 'c-1500';         scene = 'bialystok-industrial-c'; s = 1500 },
    @{ id = 'dojlidy-400';    scene = 'bialystok-dojlidy';      s = 400 },
    @{ id = 'maczka-400';     scene = 'bialystok-maczka';       s = 400 },
    @{ id = 'kleeberga-400';  scene = 'bialystok-kleeberga';    s = 400 },
    @{ id = 'knyszynska-400'; scene = 'bialystok-knyszynska';   s = 400 },
    @{ id = 'knyszyn-300';    scene = 'knyszyn';                s = 300 },
    @{ id = 'tykocin-300';    scene = 'dw671-tykocin-01';       s = 300 },
    @{ id = 'monki-300';      scene = 'dk65-monki-01';          s = 300 },
    @{ id = 'dk65-03-500';    scene = 'dk65-03';                s = 500 },
    @{ id = 'knyszyn-w-500';  scene = 'knyszyn-w';              s = 500 }
)
# Configs: D74 class emulation (min = Low 1080p30, zalecany = High 1080p60) + uncapped per tier for the cost curve.
$Configs = @(
    @{ id = 'min-Low-30';       tier = 'Low';    fps = 30;   vsync = -1; cls = 'min' },
    @{ id = 'zal-High-60';      tier = 'High';   fps = 60;   vsync = -1; cls = 'zalecany' },
    @{ id = 'unc-Low';          tier = 'Low';    fps = 1000; vsync = 0;  cls = '' },
    @{ id = 'unc-Medium';       tier = 'Medium'; fps = 1000; vsync = 0;  cls = '' },
    @{ id = 'unc-High';         tier = 'High';   fps = 1000; vsync = 0;  cls = '' },
    @{ id = 'unc-Ultra';        tier = 'Ultra';  fps = 1000; vsync = 0;  cls = '' }
)

function Test-Busy {
    $procs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
    $u = @($procs | Where-Object { $_.Name -ieq 'Unity.exe' })
    $b = @($procs | Where-Object { $_.CommandLine -match 'build_world\.py' })
    if ($u.Count -or $b.Count) { return "Unity.exe=$($u.Count) build_world=$($b.Count)" }
    return ''
}
function Write-Status([string]$msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Add-Content -Path $Status -Value $line
    Add-Content -Path $Live -Value "- $line"
}

$total = $Points.Count * $Configs.Count; $n = 0
Write-Status "run.ps1 start: $total runs x ${DurationSeconds}s"
foreach ($c in $Configs) {          # config-major: every tier gets all points even if the sweep is cut short
    foreach ($p in $Points) {
        $n++
        $dir = Join-Path $Runs "$($p.id)__$($c.id)"
        if (Test-Path (Join-Path $dir 'run.json')) { continue }
        # pause while the machine is busy (max 2 h per pause), never measure under load
        $waited = 0
        if ($DryRun) { Write-Host "[$($p.id) $($c.id)]"; continue }
        while (($busy = Test-Busy) -and $waited -lt 7200) {
            if ($waited % 600 -eq 0) { Write-Status "pause ($busy) before $n/$total" }
            Start-Sleep 60; $waited += 60
        }
        if ($busy) { Write-Status "ABORT: machine busy > 2 h ($busy)"; exit 3 }
        if (Get-Process -Name Kamion -ErrorAction SilentlyContinue) { Write-Status "skip: Kamion already running"; Start-Sleep 30; continue }
        if (Test-Path $dir) { Remove-Item -Recurse -Force $dir }
        $a = @('-NoProfile', '-File', (Join-Path $Main 'scripts\pc-metrics.ps1'),
            '-Exe', $Exe, '-Scene', $p.scene, '-Tier', $c.tier, '-Fps', $c.fps, '-Width', 1920, '-Height', 1080,
            '-DurationSeconds', $DurationSeconds, '-WarmupSeconds', 8, '-OutDir', $dir,
            '-Label', "pcbudget-$($p.id)-$($c.id)", '-Extra', "route_s=$($p.s),metricsMaxFps=1000", '-AllowContextMismatch')
        if ($c.vsync -ge 0) { $a += @('-VSync', $c.vsync) }
        if ($c.cls) { $a += @('-Class', $c.cls) }
        if ($DryRun) { Write-Host "pwsh $($a -join ' ')"; continue }
        New-Item -ItemType Directory -Force $dir | Out-Null
        & pwsh @a *> (Join-Path $dir 'pc-metrics.stdout.txt')
        Write-Status "$n/$total $($p.id) $($c.id) exit=$LASTEXITCODE"
        Start-Sleep 5
    }
}
Write-Status 'run.ps1 DONE'
