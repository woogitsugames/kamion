<#
.SYNOPSIS
  ADR 0177: refresh the A16 Low PSO collections (ADR 0113) after a world regeneration, with a before/after p99 check. ONE command.
.DESCRIPTION
  Run from the repo (main) AFTER the regeneration and the clean release APK of that state (-BeforeApk). Steps:
    1. Development APK (Unity slot; build-android.ps1 -Tier Low -Development), then `git checkout` of the files the build touches.
    2. A16 trace: G3-A `pso_trace 90 pso_tag g3a`, G3-B `pso_trace 95 pso_tag g3b` (tracing works only in Development, ADR 0113),
       adb pull of pso_Vulkan_Low_g3{a,b}.graphicsstate; refuses files < 4 KB (0 states = release trace / failed trace).
    3. Copy into game/Assets/_Project/Rendering/Resources/Pso/ (existing .meta kept -> same GUIDs).
    4. Release APK with the new collections (Unity slot).
    5. A16 before/after x2, interleaved (before A,B / after A,B / before A,B / after A,B), then tools/perf/p99_spikes.py --summary.
  Phone runs use tools/perf/phone-p99.ps1 (PHONE_RUN lock, adb retry, keyguard reject). The A16 must be unlocked.
  Unity must not be running a build on this project; other agents' Unity processes may run, but the PHONE_RUN lock is held only
  during the phone steps. Outputs: artifacts/perf-p99-0177/refresh-<ts>/ (logs, pulled collections, runs, summary.txt).
  Commit afterwards: the two .graphicsstate files (and nothing from ProjectSettings).
.EXAMPLE
  pwsh tools/perf/pso-refresh.ps1 -BeforeApk artifacts/apk/kamion-0.1.0-<sha>.apk
  pwsh tools/perf/pso-refresh.ps1 -BeforeApk ... -SkipDevBuild -DevApk artifacts/apk/kamion-0.1.0-<sha>-dev.apk   # reuse a dev APK
#>
param(
    [Parameter(Mandatory = $true)] [string]$BeforeApk,
    [string]$DevApk = '',
    [switch]$SkipDevBuild,
    [string]$AfterApk = '',
    [switch]$SkipAfterBuild,
    [int]$Repeats = 2,
    [string]$TraceFrom = '',   # reuse trace/ from an earlier refresh-<ts> dir (skips dev build + phone trace)
    [string]$Owner = 'pso-refresh'
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot)
Set-Location $repo
$main = 'C:\Users\matma\Documents\Claude\kamion'
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
$out = Join-Path $main "artifacts/perf-p99-0177/refresh-$ts"
New-Item -ItemType Directory -Force $out | Out-Null
$log = Join-Path $out 'refresh.log'
function L($m) { $s = "$(Get-Date -Format 'HH:mm:ss') $m"; Write-Host $s; Add-Content $log $s }
function Abs($p) { if ([IO.Path]::IsPathRooted($p)) { $p } else { Join-Path $repo $p } }
$BeforeApk = Abs $BeforeApk
if (-not (Test-Path $BeforeApk)) { throw "missing $BeforeApk" }
$psoDir = Join-Path $repo 'game/Assets/_Project/Rendering/Resources/Pso'

function Build([string]$tag, [switch]$Dev) {
    $before = @(Get-ChildItem (Join-Path $repo 'artifacts/apk') -Filter *.apk | ForEach-Object FullName)
    pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner $Owner | Out-Null
    try {
        $a = @('-NoProfile', '-File', 'scripts/build-android.ps1', '-Tier', 'Low')
        if ($Dev) { $a += '-Development' }
        & pwsh @a *> (Join-Path $out "build-$tag.log")
        if ($LASTEXITCODE -ne 0) { throw "build $tag failed (exit $LASTEXITCODE), see build-$tag.log" }
    }
    finally { pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner $Owner | Out-Null }
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
    $apk = Get-ChildItem (Join-Path $repo 'artifacts/apk') -Filter *.apk | Where-Object { $before -notcontains $_.FullName } |
        Sort-Object LastWriteTime | Select-Object -Last 1
    if (-not $apk) { throw "build $tag produced no new APK" }
    L "build $tag -> $($apk.FullName)"
    return $apk.FullName
}
function Phone([string]$apk, [string]$dir, [string]$runs, [string[]]$pull = @()) {
    $a = @('-NoProfile', '-File', 'tools/perf/phone-p99.ps1', '-Apk', $apk, '-OutDir', (Join-Path $out $dir), '-Runs', $runs, '-Owner', $Owner)
    if ($pull.Count) { $a += @('-PullPso', ($pull -join ',')) }
    # Start-Process without a pipe: an adb server spawned by the child would otherwise hold the pipe open forever
    Start-Process pwsh -ArgumentList $a -Wait -WindowStyle Hidden
}

if ($TraceFrom) {
    New-Item -ItemType Directory -Force (Join-Path $out 'trace') | Out-Null
    Copy-Item (Join-Path $TraceFrom 'trace/*') (Join-Path $out 'trace') -Recurse -Force
    $SkipDevBuild = $true
    L "trace reused from $TraceFrom"
}
# 1. development APK
if (-not $TraceFrom) {
if (-not $SkipDevBuild) { $DevApk = Build 'dev' -Dev } else { $DevApk = Abs $DevApk }
if (-not (Test-Path $DevApk)) { throw "missing dev APK $DevApk" }

# 2. trace on the phone
L "trace with $DevApk"
Phone $DevApk 'trace' 'traceA=A:pso_trace=90 pso_tag=g3a;traceB=B:pso_trace=95 pso_tag=g3b' @('g3a', 'g3b')
}
foreach ($tag in 'g3a', 'g3b') {
    $f = Join-Path $out "trace/pso_Vulkan_Low_$tag.graphicsstate"
    if (-not (Test-Path $f) -or (Get-Item $f).Length -lt 4096) { throw "trace $tag missing or empty ($f) - is the APK a Development build?" }
    $saved = Select-String -Path (Join-Path $out "trace/trace$($tag.Substring(2).ToUpper())/logcat.txt") -Pattern '\[PSO\] trace saved' -ErrorAction SilentlyContinue | Select-Object -First 1
    L "trace ${tag}: $((Get-Item $f).Length) B; $($saved.Line)"
}

# 3. install the collections (keep .meta)
foreach ($tag in 'g3a', 'g3b') {
    $dst = Join-Path $psoDir "pso_Vulkan_Low_$tag.graphicsstate"
    Copy-Item $dst (Join-Path $out "old_pso_Vulkan_Low_$tag.graphicsstate") -ErrorAction SilentlyContinue
    Copy-Item (Join-Path $out "trace/pso_Vulkan_Low_$tag.graphicsstate") $dst -Force
}
L 'collections copied into Resources/Pso'

# 4. release APK with the new collections
if (-not $SkipAfterBuild) { $AfterApk = Build 'after' } else { $AfterApk = Abs $AfterApk }

# 5. before/after, interleaved
for ($i = 1; $i -le $Repeats; $i++) {
    Phone $BeforeApk 'runs' "before_a$i=A:spike_probe=1;before_b$i=B:spike_probe=1"
    Phone $AfterApk 'runs' "after_a$i=A:spike_probe=1;after_b$i=B:spike_probe=1"
}
$dirs = Get-ChildItem (Join-Path $out 'runs') -Directory | Sort-Object Name | ForEach-Object FullName
python tools/perf/p99_spikes.py --summary @dirs | Tee-Object (Join-Path $out 'summary.txt')
L "done: $out (commit game/Assets/_Project/Rendering/Resources/Pso/*.graphicsstate)"
