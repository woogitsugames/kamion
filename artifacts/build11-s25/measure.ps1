<#
.SYNOPSIS
  Build #11 measurement and verification orchestrator (plan only — requires explicit execution by leader).
.DESCRIPTION
  Executes the Build #11 leader sequence in order:
    (1) Preflight & TruckAssetBuilder: verify SM_CabInterior_LOD0.fbx, run TruckAssetBuilder.BuildBatch
        (+ optional WorldTruckInstaller.InstallBatch) under unity slot, run check-build-scenes.py.
    (2) Build: pwsh scripts/build-windows.ps1 -Slot -Regions d67-full (+ package-windows.py --dry-run check).
    (3) Measure: pc-metrics.ps1 (zalecany High/60 and min Low/30, 1920x1080 borderless, VSync 0) for:
          - Reference comparison vs Build #10 (knyszyn-w, dk65-07)
          - 8 dense/town city tiles + bialystok-industrial-c (worst frame_estimate cameras + Cab route_s)
          - A/B pairs: rq_mirror_main=0 (Cab), rq_cardedge=0 (maczka), -farRing off on edge-north with -stream 1 (knyszyn-w)
    (4) Summary: aggregate pc-report.json metrics (tris, draw_calls, gpu_ms, cpu_main_ms, frame_ms p50/p95) into
        summary.csv and summary.md.

  Supports -WhatIf / -DryRun without touching Unity, builds, or Data/.
.EXAMPLE
  pwsh artifacts/build11-s25/measure.ps1 -WhatIf
  pwsh artifacts/build11-s25/measure.ps1 -DryRun -Steps Measure,Summary -Exe artifacts/win/kamion-.../Kamion.exe
  pwsh artifacts/build11-s25/measure.ps1 -Steps Preflight,TruckBuild,Build,Measure,Summary
  pwsh artifacts/build11-s25/measure.ps1 -Steps Measure,Summary -Exe artifacts/win/kamion-0.1.0-abc-regions/Kamion.exe -Resume
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string[]]$Steps = @('Preflight', 'TruckBuild', 'Build', 'Measure', 'Summary'),
    [string]$Worktree = '',
    [string]$Exe = '',
    [string]$OutDir = '',
    [int]$RefDurationSeconds = 90,
    [int]$DurationSeconds = 45,
    [int]$WarmupSeconds = 5,
    [ValidateSet('qacam', 'route', 'both')]
    [string]$CityMode = 'both',
    [switch]$InstallWorldC,
    [switch]$IncludeUncappedAB,
    [switch]$Resume,
    [switch]$DryRun,
    [string]$SlotOwner = 'build11-s25',
    [int]$WaitBusyMinutes = 120
)

$ErrorActionPreference = 'Stop'
if ($DryRun) { $WhatIfPreference = $true }
$ValidSteps = @('Preflight', 'TruckBuild', 'Build', 'Measure', 'Summary')
$Steps = @($Steps | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
foreach ($s in $Steps) {
    if ($s -notin $ValidSteps) { throw "Invalid step '$s'. Allowed: $($ValidSteps -join ', ')" }
}

if (-not $Worktree) {
    $Worktree = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
} else {
    $Worktree = (Resolve-Path $Worktree).Path
}
if (-not $OutDir) {
    $OutDir = Join-Path $Worktree 'artifacts\build11-s25\results'
}
$RunsDir = Join-Path $OutDir 'runs'
$StatusFile = Join-Path $OutDir 'measure.status'

. (Join-Path $Worktree 'scripts\env.ps1')

function Write-Log([string]$Msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $Msg"
    Write-Host $line
    if (-not $WhatIfPreference) {
        New-Item -ItemType Directory -Force $OutDir | Out-Null
        Add-Content -Path $StatusFile -Value $line -Encoding utf8
    }
}

function Invoke-StepCmd([string]$Target, [string]$Action, [scriptblock]$Script) {
    if ($PSCmdlet.ShouldProcess($Target, $Action)) {
        & $Script
    } else {
        Write-Host "[WHATIF] $Action :: $Target" -ForegroundColor Cyan
    }
}

function Get-BusyReason {
    $procs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
    $u = @($procs | Where-Object { $_.Name -ieq 'Unity.exe' })
    $b = @($procs | Where-Object { $_.CommandLine -match 'build_world\.py|far_field\.py|build_region\.py' })
    $k = @($procs | Where-Object { $_.Name -ieq 'Kamion.exe' })
    if ($u.Count -or $b.Count -or $k.Count) {
        return "Unity=$($u.Count) worldgen=$($b.Count) Kamion=$($k.Count)"
    }
    return ''
}

function Wait-QuietMachine {
    if ($WhatIfPreference) { return }
    $waited = 0
    $maxSec = $WaitBusyMinutes * 60
    while (($busy = Get-BusyReason) -and $waited -lt $maxSec) {
        if ($waited % 300 -eq 0) { Write-Log "WAIT machine busy ($busy)..." }
        Start-Sleep -Seconds 30
        $waited += 30
    }
    if ($busy) { throw "ABORT: machine remained busy > $WaitBusyMinutes min ($busy)" }
}

function Resolve-ExpectedWinExe {
    $ver = (Select-String -Path (Join-Path $Worktree 'game\ProjectSettings\ProjectSettings.asset') -Pattern '^\s*bundleVersion:\s*(.+)$').Matches[0].Groups[1].Value.Trim()
    $sha = (& git -C $Worktree rev-parse --short=10 HEAD 2>$null)
    if (& git -C $Worktree status --porcelain --untracked-files=no) { $sha = "$sha-dirty" }
    $cand = Join-Path $ArtifactsDir "win\kamion-$ver-$sha-regions\Kamion.exe"
    if (Test-Path -LiteralPath $cand) { return (Resolve-Path -LiteralPath $cand).Path }
    $latest = Get-ChildItem (Join-Path $ArtifactsDir 'win') -Directory -Filter "kamion-$ver-*-regions" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latest) {
        $p = Join-Path $latest.FullName 'Kamion.exe'
        if (Test-Path -LiteralPath $p) { return (Resolve-Path -LiteralPath $p).Path }
    }
    return $cand
}

function Assert-CleanProjectSettings {
    $dirty = & git -C $Worktree status --porcelain -- 'game/ProjectSettings/'
    if ($dirty) {
        Write-Warning "ProjectSettings modified after Unity step:`n$dirty"
        Write-Warning "Revert QualitySettings.asset before committing: git -C `"$Worktree`" checkout -- game/ProjectSettings/QualitySettings.asset"
    }
}

# ------------------------------------------------------------------ (1) Preflight & TruckAssetBuilder
if ($Steps -contains 'Preflight') {
    Write-Log "=== Step 1a: Preflight ==="
    $fbx = Join-Path $Worktree 'art-source\truck\interior\export\SM_CabInterior_LOD0.fbx'
    if (Test-Path -LiteralPath $fbx) {
        $item = Get-Item -LiteralPath $fbx
        Write-Log ("OK SM_CabInterior_LOD0.fbx present ({0:N1} MB, {1:yyyy-MM-dd HH:mm})" -f ($item.Length / 1MB), $item.LastWriteTime)
    } else {
        Write-Warning "MISSING $fbx - regenerate before TruckAssetBuilder: pwsh scripts/cab-lod0.ps1 -Build"
        if (-not $WhatIfPreference) { exit 2 }
    }
    Invoke-StepCmd "pwsh scripts/cab-lod0.ps1 -Require" "Verify cab LOD0 FBX" {
        & pwsh -NoProfile -File (Join-Path $Worktree 'scripts\cab-lod0.ps1') -Require
        if ($LASTEXITCODE -ne 0) { throw "cab-lod0.ps1 -Require failed ($LASTEXITCODE)" }
    }
    Invoke-StepCmd "uv run --no-project python scripts/check-build-scenes.py --regions d67-full --require-tiles --require-high" "Check d67-full scenes before build" {
        Push-Location $Worktree
        try {
            & uv run --no-project python (Join-Path $Worktree 'scripts\check-build-scenes.py') --regions d67-full --require-tiles --require-high
            if ($LASTEXITCODE -ne 0) { throw "check-build-scenes.py failed ($LASTEXITCODE)" }
        } finally { Pop-Location }
    }
}

if ($Steps -contains 'TruckBuild') {
    Write-Log "=== Step 1b: TruckAssetBuilder ==="
    $truckLog = Join-Path $LogsDir ("build11-TruckAssetBuilder-{0}.log" -f (Get-Timestamp))
    $cmdLine = "$UnityExe -batchmode -projectPath `"$ProjectPath`" -logFile `"$truckLog`" -buildTarget Win64 -quit -executeMethod Game.Editor.Setup.TruckAssetBuilder.BuildBatch"
    Invoke-StepCmd $cmdLine "Run TruckAssetBuilder.BuildBatch (unity slot)" {
        $acquired = $false
        & pwsh -NoProfile -File (Join-Path $Worktree 'scripts\unity-slot.ps1') -Acquire -Pool unity -Owner $SlotOwner | Out-Host
        $acquired = ($LASTEXITCODE -eq 0)
        try {
            $code = Invoke-UnityBatch -LogFile $truckLog -BuildTarget 'Win64' -Arguments @('-executeMethod', 'Game.Editor.Setup.TruckAssetBuilder.BuildBatch')
            if ($code -ne 0) { Show-UnityLogErrors $truckLog; throw "TruckAssetBuilder.BuildBatch failed (exit $code), log: $truckLog" }
            if ($InstallWorldC) {
                $instLog = Join-Path $LogsDir ("build11-WorldTruckInstaller-{0}.log" -f (Get-Timestamp))
                $icode = Invoke-UnityBatch -LogFile $instLog -BuildTarget 'Win64' -Arguments @('-executeMethod', 'Game.World.Import.WorldTruckInstaller.InstallBatch')
                if ($icode -ne 0) { Show-UnityLogErrors $instLog; throw "WorldTruckInstaller.InstallBatch failed (exit $icode), log: $instLog" }
            }
        } finally {
            if ($acquired) {
                & pwsh -NoProfile -File (Join-Path $Worktree 'scripts\unity-slot.ps1') -Release -Pool unity -Owner $SlotOwner | Out-Host
            }
        }
        Assert-CleanProjectSettings
    }
}

# ------------------------------------------------------------------ (2) Windows Build
if ($Steps -contains 'Build') {
    Write-Log "=== Step 2: Windows Build (d67-full) ==="
    $buildCmd = "pwsh scripts/build-windows.ps1 -Slot -SlotOwner $SlotOwner -Regions d67-full"
    Invoke-StepCmd $buildCmd "Build Windows x64 player with d67-full" {
        Push-Location $Worktree
        try {
            & pwsh -NoProfile -File (Join-Path $Worktree 'scripts\build-windows.ps1') -Slot -SlotOwner $SlotOwner -Regions d67-full
            if ($LASTEXITCODE -ne 0) { throw "build-windows.ps1 failed ($LASTEXITCODE)" }
        } finally { Pop-Location }
        Assert-CleanProjectSettings
    }
    $resolved = if ($Exe) { $Exe } else { Resolve-ExpectedWinExe }
    $pkgDir = Split-Path -Parent $resolved
    Invoke-StepCmd "uv run --no-project python scripts/package-windows.py `"$pkgDir`" --dry-run" "Dry-run package check" {
        if (Test-Path -LiteralPath $pkgDir) {
            & uv run --no-project python (Join-Path $Worktree 'scripts\package-windows.py') $pkgDir --dry-run
        }
    }
}

# ------------------------------------------------------------------ (3) pc-metrics Measurements
if ($Steps -contains 'Measure') {
    Write-Log "=== Step 3: pc-metrics Measurements ==="
    if (-not $Exe) { $Exe = Resolve-ExpectedWinExe }
    if (-not $WhatIfPreference -and -not (Test-Path -LiteralPath $Exe -PathType Leaf)) {
        throw "Kamion.exe not found at '$Exe'. Pass -Exe or run -Steps Build first."
    }
    Write-Log "Target Exe: $Exe"

    # Measurement matrix (verified against codex-city-budget-s25/WYNIKI.md, control_cameras.json, route_start.json, FarRing.cs, RenderOverrides.cs)
    $Jobs = [System.Collections.Generic.List[hashtable]]::new()

    # 3A. Reference comparison vs Build #10 (knyszyn-w, dk65-07)
    foreach ($tile in @('knyszyn-w', 'dk65-07')) {
        $Jobs.Add(@{ id = "ref-${tile}-high60"; group = 'ref-b10'; scene = $tile; tier = 'High'; fps = 60; cls = 'zalecany'; dur = $RefDurationSeconds; extra = '' })
        $Jobs.Add(@{ id = "ref-${tile}-low30";  group = 'ref-b10'; scene = $tile; tier = 'Low';  fps = 30; cls = 'min';      dur = $RefDurationSeconds; extra = '' })
    }

    # 3B. 8 city tiles (> 2.0 M High) + bialystok-industrial-c (REF) - worst frame_estimate cameras
    $CityCameras = @(
        @{ tile = 'bialystok-wygoda';       camH = 'roundabout_01_above'; camL = 'roundabout_01_above'; sH = $null; sL = $null; note = 'route_start=91m (2643m od ronda) -> tylko qacam' },
        @{ tile = 'bialystok-bojary';       camH = 'route_s0612';         camL = 'route_s0612';         sH = 612;   sL = 612;   note = '' },
        @{ tile = 'bialystok-maczka';       camH = 'route_s0440';         camL = 'route_s0440';         sH = 440;   sL = 440;   note = '' },
        @{ tile = 'bialystok-mickiewicza';  camH = 'dw678_ciolkowskiego'; camL = 'roundabout_03_above'; sH = 2038;  sL = $null; note = 'Low roundabout_03_above 425m od trasy -> tylko qacam' },
        @{ tile = 'bialystok-kleeberga';    camH = 'route_s0159';         camL = 'route_s0159';         sH = 159;   sL = 159;   note = '' },
        @{ tile = 'knyszyn';                camH = 'gardens_tykocka_eye'; camL = 'gardens_tykocka_eye'; sH = 649;   sL = 649;   note = '' },
        @{ tile = 'bialystok-krywlany';     camH = 'route_s0461';         camL = 'route_s0461';         sH = 461;   sL = 461;   note = '' },
        @{ tile = 'monki';                  camH = 'route_s0170';         camL = 'route_s0170';         sH = 170;   sL = 170;   note = '' },
        @{ tile = 'bialystok-industrial-c'; camH = 'stretch_04';          camL = 'stretch_04';          sH = 360;   sL = 360;   note = 'REF C' }
    )

    if ($CityMode -in @('qacam', 'both')) {
        foreach ($c in $CityCameras) {
            $t = $c.tile
            $Jobs.Add(@{ id = "city-${t}-high60"; group = 'city-qacam'; scene = $t; tier = 'High'; fps = 60; cls = 'zalecany'; dur = $DurationSeconds; extra = "qacam=$($c.camH)" })
            $Jobs.Add(@{ id = "city-${t}-low30";  group = 'city-qacam'; scene = $t; tier = 'Low';  fps = 30; cls = 'min';      dur = $DurationSeconds; extra = "qacam=$($c.camL)" })
        }
    }

    if ($CityMode -in @('route', 'both')) {
        # Cab-mode (with mirrors + cab interior) at nearest route_s for worst Cab-accessible dense city tiles + C
        $CabRuns = @(
            @{ id = 'cab-bojary-high60';      scene = 'bialystok-bojary';       tier = 'High'; fps = 60; cls = 'zalecany'; s = 612 },
            @{ id = 'cab-bojary-low30';       scene = 'bialystok-bojary';       tier = 'Low';  fps = 30; cls = 'min';      s = 612 },
            @{ id = 'cab-maczka-high60';      scene = 'bialystok-maczka';       tier = 'High'; fps = 60; cls = 'zalecany'; s = 440 },
            @{ id = 'cab-mickiewicza-high60'; scene = 'bialystok-mickiewicza';  tier = 'High'; fps = 60; cls = 'zalecany'; s = 2038 },
            @{ id = 'cab-c-high60';           scene = 'bialystok-industrial-c'; tier = 'High'; fps = 60; cls = 'zalecany'; s = 360 },
            @{ id = 'cab-c-low30';            scene = 'bialystok-industrial-c'; tier = 'Low';  fps = 30; cls = 'min';      s = 360 }
        )
        foreach ($r in $CabRuns) {
            $Jobs.Add(@{ id = $r.id; group = 'city-cab'; scene = $r.scene; tier = $r.tier; fps = $r.fps; cls = $r.cls; dur = $DurationSeconds; extra = "route_s=$($r.s)" })
        }
    }

    # 3C. A/B Isolations (High/60 zalecany + optional uncapped)
    # 1) Mirrors: rq_mirror_main=0 MUST run in Cab mode (not qacam) so class II mirror insets are active in baseline
    $Jobs.Add(@{ id = 'ab-mirror-on';       group = 'ab-mirror';   scene = 'bialystok-bojary'; tier = 'High'; fps = 60; cls = 'zalecany'; dur = $DurationSeconds; extra = 'route_s=612' })
    $Jobs.Add(@{ id = 'ab-mirror-off';      group = 'ab-mirror';   scene = 'bialystok-bojary'; tier = 'High'; fps = 60; cls = 'zalecany'; dur = $DurationSeconds; extra = 'route_s=612,rq_mirror_main=0' })
    # 2) VegCardEdge: rq_cardedge=0 on tree-heavy tile (bialystok-maczka route_s0440)
    $Jobs.Add(@{ id = 'ab-cardedge-on';     group = 'ab-cardedge'; scene = 'bialystok-maczka'; tier = 'High'; fps = 60; cls = 'zalecany'; dur = $DurationSeconds; extra = 'qacam=route_s0440' })
    $Jobs.Add(@{ id = 'ab-cardedge-off';    group = 'ab-cardedge'; scene = 'bialystok-maczka'; tier = 'High'; fps = 60; cls = 'zalecany'; dur = $DurationSeconds; extra = 'qacam=route_s0440,rq_cardedge=0' })
    # 3) FarRing: -farRing off on edge-north with -stream 1 (knyszyn-w)
    $Jobs.Add(@{ id = 'ab-farring-on';      group = 'ab-farring';  scene = 'knyszyn-w';        tier = 'High'; fps = 60; cls = 'zalecany'; dur = $DurationSeconds; extra = 'qacam=edge-north,stream=1' })
    $Jobs.Add(@{ id = 'ab-farring-off';     group = 'ab-farring';  scene = 'knyszyn-w';        tier = 'High'; fps = 60; cls = 'zalecany'; dur = $DurationSeconds; extra = 'qacam=edge-north,stream=1,farRing=off' })

    if ($IncludeUncappedAB) {
        $Jobs.Add(@{ id = 'ab-unc-mirror-on';    group = 'ab-uncapped'; scene = 'bialystok-bojary'; tier = 'High'; fps = 1000; cls = ''; dur = $DurationSeconds; extra = 'route_s=612' })
        $Jobs.Add(@{ id = 'ab-unc-mirror-off';   group = 'ab-uncapped'; scene = 'bialystok-bojary'; tier = 'High'; fps = 1000; cls = ''; dur = $DurationSeconds; extra = 'route_s=612,rq_mirror_main=0' })
        $Jobs.Add(@{ id = 'ab-unc-cardedge-on';  group = 'ab-uncapped'; scene = 'bialystok-maczka'; tier = 'High'; fps = 1000; cls = ''; dur = $DurationSeconds; extra = 'qacam=route_s0440' })
        $Jobs.Add(@{ id = 'ab-unc-cardedge-off'; group = 'ab-uncapped'; scene = 'bialystok-maczka'; tier = 'High'; fps = 1000; cls = ''; dur = $DurationSeconds; extra = 'qacam=route_s0440,rq_cardedge=0' })
        $Jobs.Add(@{ id = 'ab-unc-farring-on';   group = 'ab-uncapped'; scene = 'knyszyn-w';        tier = 'High'; fps = 1000; cls = ''; dur = $DurationSeconds; extra = 'qacam=edge-north,stream=1' })
        $Jobs.Add(@{ id = 'ab-unc-farring-off';  group = 'ab-uncapped'; scene = 'knyszyn-w';        tier = 'High'; fps = 1000; cls = ''; dur = $DurationSeconds; extra = 'qacam=edge-north,stream=1,farRing=off' })
    }

    $slotHeld = $false
    if (-not $WhatIfPreference) {
        New-Item -ItemType Directory -Force $RunsDir | Out-Null
        & pwsh -NoProfile -File (Join-Path $Worktree 'scripts\unity-slot.ps1') -Acquire -Pool heavy -Owner $SlotOwner | Out-Host
        $slotHeld = ($LASTEXITCODE -eq 0)
    }
    try {
        $idx = 0
        $total = $Jobs.Count
        foreach ($j in $Jobs) {
            $idx++
            $runOut = Join-Path $RunsDir $j.id
            if ($Resume -and (Test-Path -LiteralPath (Join-Path $runOut 'run.json'))) {
                Write-Log "[$idx/$total] SKIP (resume) $($j.id)"
                continue
            }
            $pcmArgs = @(
                '-NoProfile', '-File', (Join-Path $Worktree 'scripts\pc-metrics.ps1'),
                '-Exe', $Exe,
                '-Scene', $j.scene,
                '-Tier', $j.tier,
                '-Fps', "$($j.fps)",
                '-VSync', '0',
                '-Width', '1920',
                '-Height', '1080',
                '-WindowMode', 'borderless',
                '-DurationSeconds', "$($j.dur)",
                '-WarmupSeconds', "$WarmupSeconds",
                '-OutDir', $runOut,
                '-Label', "b11-$($j.id)"
            )
            if ($j.cls) { $pcmArgs += @('-Class', $j.cls) }
            if ($j.extra) { $pcmArgs += @('-Extra', $j.extra) }

            $cmdPreview = "pwsh $($pcmArgs -join ' ')"
            if (-not $PSCmdlet.ShouldProcess($j.id, $cmdPreview)) {
                Write-Host ("[{0,2}/{1}] [WHATIF] {2}" -f $idx, $total, $cmdPreview) -ForegroundColor Cyan
                continue
            }

            Wait-QuietMachine
            $env:KAMION_FAR_RING = $null
            if (Test-Path -LiteralPath $runOut) { Remove-Item -Recurse -Force $runOut }
            New-Item -ItemType Directory -Force $runOut | Out-Null

            $stdoutLog = Join-Path $runOut 'pc-metrics.stdout.txt'
            & pwsh @pcmArgs *> $stdoutLog
            $rc = $LASTEXITCODE
            $env:KAMION_FAR_RING = $null
            $verdictLine = (Select-String -Path $stdoutLog -Pattern '^verdict=' -ErrorAction SilentlyContinue | Select-Object -Last 1).Line
            Write-Log ("[{0,2}/{1}] {2} ({3}) exit={4} {5}" -f $idx, $total, $j.id, $j.group, $rc, $verdictLine)
            Start-Sleep -Seconds 3
        }
    } finally {
        $env:KAMION_FAR_RING = $null
        if ($slotHeld) {
            & pwsh -NoProfile -File (Join-Path $Worktree 'scripts\unity-slot.ps1') -Release -Pool heavy -Owner $SlotOwner | Out-Host
        }
    }
}

# ------------------------------------------------------------------ (4) Summary Aggregation
if ($Steps -contains 'Summary') {
    Write-Log "=== Step 4: Summary ==="
    $sumPy = @'
import csv, json, pathlib, sys
runs_dir = pathlib.Path(sys.argv[1])
out_dir = pathlib.Path(sys.argv[2])
rows = []
for rdir in sorted(runs_dir.iterdir()):
    if not rdir.is_dir():
        continue
    rep_p = rdir / "pc-report.json"
    run_p = rdir / "run.json"
    if not rep_p.exists():
        rows.append({"id": rdir.name, "verdict": "MISSING_REPORT" if run_p.exists() else "MISSING"})
        continue
    rep = json.loads(rep_p.read_text(encoding="utf-8"))
    m = rep.get("metrics", {})
    disp = rep.get("display", {})
    cls = rep.get("class") or {}
    loads = (m.get("region_load_s") or {}).get("loads") or []
    scene_name = loads[0].get("scene", "") if loads else ""
    def g(k, stat):
        v = (m.get(k) or {}).get(stat)
        return "" if v is None else v
    rows.append({
        "id": rdir.name,
        "scene": scene_name,
        "tier": disp.get("qualityName", ""),
        "fps_cap": disp.get("targetFrameRate", ""),
        "class": cls.get("name", ""),
        "verdict": rep.get("verdict", ""),
        "measurement_kind": rep.get("measurement_kind", ""),
        "gate_eligible": rep.get("gate_eligible", ""),
        "frames": m.get("frames_window", ""),
        "frame_p50_ms": g("frame_ms", "p50"),
        "frame_p95_ms": g("frame_ms", "p95"),
        "cpu_p50_ms": g("cpu_main_ms", "p50"),
        "cpu_p95_ms": g("cpu_main_ms", "p95"),
        "gpu_p50_ms": g("gpu_ms", "p50"),
        "gpu_p95_ms": g("gpu_ms", "p95"),
        "dc_p50": g("draw_calls", "p50"),
        "dc_p95": g("draw_calls", "p95"),
        "tris_p50": g("tris", "p50"),
        "tris_p95": g("tris", "p95"),
        "gc_win": (m.get("gc") or {}).get("collections_in_window", ""),
    })

csv_p = out_dir / "summary.csv"
md_p = out_dir / "summary.md"
fields = ["id","scene","tier","fps_cap","class","verdict","measurement_kind","gate_eligible","frames",
          "frame_p50_ms","frame_p95_ms","cpu_p50_ms","cpu_p95_ms","gpu_p50_ms","gpu_p95_ms",
          "dc_p50","dc_p95","tris_p50","tris_p95","gc_win"]
with csv_p.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in fields})

lines = [
    "# Build #11 pc-metrics Summary",
    "",
    "| id | scene | tier | class | verdict | frame p50/p95 [ms] | CPU p50/p95 [ms] | GPU p50/p95 [ms] | DC p50/p95 | tris p50/p95 | GC |",
    "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|",
]
for r in rows:
    def pair(a, b):
        return f"{r.get(a,'')} / {r.get(b,'')}" if r.get(a,'') != '' or r.get(b,'') != '' else "—"
    lines.append(f"| `{r['id']}` | `{r.get('scene','')}` | {r.get('tier','')}/{r.get('fps_cap','')} | {r.get('class','')} | **{r.get('verdict','')}** | {pair('frame_p50_ms','frame_p95_ms')} | {pair('cpu_p50_ms','cpu_p95_ms')} | {pair('gpu_p50_ms','gpu_p95_ms')} | {pair('dc_p50','dc_p95')} | {pair('tris_p50','tris_p95')} | {r.get('gc_win','')} |")
md_p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {len(rows)} rows -> {csv_p} and {md_p}")
'@
    Invoke-StepCmd "uv run --no-project python `"$OutDir\summarize.py`" `"$RunsDir`" `"$OutDir`"" "Aggregate pc-metrics results" {
        if (-not (Test-Path -LiteralPath $RunsDir)) { Write-Warning "No runs dir at $RunsDir"; return }
        New-Item -ItemType Directory -Force $OutDir | Out-Null
        $sumPath = Join-Path $OutDir 'summarize.py'
        Set-Content -Path $sumPath -Value $sumPy -Encoding utf8
        & uv run --no-project python $sumPath $RunsDir $OutDir
        if ($LASTEXITCODE -ne 0) { throw "Summary python failed ($LASTEXITCODE)" }
    }
}
