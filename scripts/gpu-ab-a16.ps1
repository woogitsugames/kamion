<#
.SYNOPSIS
  GPU A/B on ONE phone (default: Galaxy A16 RFGL34SJYDZ, tier Low): the same APK is launched once per variant with
  launch arguments (am start -e rq_* ...), measured with device-metrics.ps1 on the gate 3 segments (G3-A / G3-B) or
  on fixed gate cameras, repeated, and collected into one table. ADR 0241, backlog B-113.
.DESCRIPTION
  Variants: tools/perf/gpu-ab-variants.json (id -> rq_* launch arguments + the expected gain with its source).
  The baseline variant has no arguments = the shipped tier. Nothing in the project is changed by this script.

  Order. Every repeat is split into blocks: one baseline run followed by up to -BaselineEvery variant runs. A variant is
  compared with the baseline of ITS block (measured minutes earlier at a similar phone temperature), so slow thermal
  drift does not leak into the difference. The variant order is reversed on even repeats.

  Rejections (a rejected run is written with valid=false and never enters the table):
    - battery >= -MaxBatteryC (36 C, HANDOVER rule) before the run: the app is stopped and the script waits; after
      -CooldownTimeoutMinutes it stops the session (exit 7),
    - keyguard showing or display not awake before / after the run (exit 5; the script never types a PIN and never
      sends KEYCODE_SLEEP / POWER),
    - thermal status >= 2 after the run, missing frame log, the autopilot / control camera did not start,
    - the game did not log "[GPUAB] ... abtag=<variant>" (the APK was built before ADR 0241 or the arguments did not
      arrive) - skip this check with -NoTagCheck only for catalogue variants made of pre-0241 switches.

  Uses the PHONE_RUN lock of the main checkout (as gate12-phone.ps1). Do not run while Unity builds/tests run on this
  PC (Unity restarts the adb daemon).
.EXAMPLE
  pwsh scripts/gpu-ab-a16.ps1 -DryRun                                           # plan + duration, no adb
  pwsh scripts/gpu-ab-a16.ps1 -Apk artifacts/apk/kamion-0.1.0-<sha>.apk          # default variants, G3-A + G3-B, 3 repeats, 30 FPS cap
  pwsh scripts/gpu-ab-a16.ps1 -Variants scale-070,lod-030,far-720 -Segments B -Uncapped
  pwsh scripts/gpu-ab-a16.ps1 -Mode Camera -Cameras g3b_eye_s1282 -Variants msaa-1,depthtex-on,opaquetex-on -Uncapped
  pwsh scripts/gpu-ab-a16.ps1 -Report artifacts/gpu-ab/<ts>                      # rebuild the table of an existing session
.NOTES
  Exit: 0 ok; 2 plan/prerequisite error; 4 install failed; 5 phone locked/asleep; 6 no valid run; 7 too hot / battery low.
  Output: artifacts/gpu-ab/<ts>/ (session.json, runs/<name>/{run.json, frametimes.csv, metrics.json, logcat-run.txt, ...},
  results.csv, summary.csv, REPORT.md). Table: uv run --project tools/perf python -m perfgate.gpuab report <dir>.
  Numbers are measurements of that session only; the "estimate" column comes from the catalogue (ESTIMATED / UNVERIFIED).
#>
param(
    [string]$Serial = 'RFGL34SJYDZ',
    # APK to install once before the session ('' = measure the APK that is already installed).
    [string]$Apk = '',
    # Variant ids from the catalogue; default = every variant with "default": true. The baseline is always added.
    [string[]]$Variants = @(),
    [switch]$AllVariants,
    [ValidateSet('Drive', 'Camera')] [string]$Mode = 'Drive',
    # Drive mode: gate 3 segments (Data/Regions/<region>/gate3_segment.json), autopilot at -SpeedKmh with the 40 t trailer.
    [string[]]$Segments = @('A', 'B'),
    # Camera mode: fixed gate cameras (gate3_cameras.json), the truck is parked at the camera's route distance.
    [string[]]$Cameras = @('g3a_eye_s0212', 'g3b_eye_s1282'),
    [ValidateRange(1, 20)] [int]$Repeats = 3,
    [ValidateRange(1, 50)] [int]$BaselineEvery = 4,
    [ValidateSet('Low', 'Medium', 'High', 'Ultra')] [string]$Tier = 'Low',
    # Frame cap of the runs. 30 = the condition of the gate numbers (B-113). -Uncapped (fps 240) removes the cap so the
    # Mali governor does not stretch the GPU time (ADR 0106 / 0136: use it to rank elements, the cap to check the budget).
    [int]$Fps = 30,
    [switch]$Uncapped,
    [int]$SpeedKmh = 30,
    [int]$LoadSeconds = 25,
    [int]$CameraSeconds = 60,
    [int]$CameraWarmupSeconds = 20,
    [double]$MaxBatteryC = 36.0,
    [int]$MinBatteryPercent = 20,
    [int]$CooldownTimeoutMinutes = 20,
    [int]$CooldownPollSeconds = 30,
    [string]$Region = 'bialystok-industrial-c',
    [string]$Catalog = '',
    [string]$OutDir = '',
    [string]$Owner = 'gpu-ab',
    [switch]$UseExistingLock,
    [switch]$NoTagCheck,
    # Only rebuild results.csv / summary.csv / REPORT.md of an existing session directory.
    [string]$Report = '',
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
$ts = Get-Timestamp

function Invoke-Report([string]$dir) {
    $catArg = @()
    if ($Catalog) { $catArg = @('--catalog', $Catalog) }
    # Output goes to the host, not the pipeline: the function must return the exit code only.
    & uv run --project (Join-Path $RepoRoot 'tools/perf') python -m perfgate.gpuab report $dir @catArg 2>&1 | ForEach-Object { Write-Host $_ }
    return $LASTEXITCODE
}
if ($Report) {
    if (-not (Test-Path $Report)) { Write-Host "no such session: $Report" -ForegroundColor Red; exit 2 }
    exit (Invoke-Report (Resolve-Path $Report).Path)
}

# ---------------------------------------------------------------- plan
if (-not $Catalog) { $Catalog = Join-Path $RepoRoot 'tools/perf/gpu-ab-variants.json' }
if (-not (Test-Path $Catalog)) { Write-Host "missing catalogue $Catalog" -ForegroundColor Red; exit 2 }
$cat = Get-Content $Catalog -Raw -Encoding utf8 | ConvertFrom-Json
$baselineId = $cat.baseline
$byId = @{}
foreach ($v in $cat.variants) { $byId[$v.id] = $v }
# pwsh -File passes "a,b" as one string: accept both forms.
$Variants = @($Variants | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$Cameras = @($Cameras | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$Segments = @($Segments | ForEach-Object { $_ -split ',' } | Where-Object { $_ } | ForEach-Object { $_.ToUpperInvariant() -replace '^G3-', '' })
if ($AllVariants) { $Variants = @($cat.variants | ForEach-Object { $_.id }) }
elseif ($Variants.Count -eq 0) { $Variants = @($cat.variants | Where-Object { $_.default } | ForEach-Object { $_.id }) }
foreach ($id in $Variants) { if (-not $byId.ContainsKey($id)) { Write-Host "unknown variant '$id' (see $Catalog)" -ForegroundColor Red; exit 2 } }
$tests = @($Variants | Where-Object { $_ -ne $baselineId } | Select-Object -Unique)
if ($tests.Count -eq 0) { Write-Host 'nothing to compare: only the baseline was selected' -ForegroundColor Red; exit 2 }

# Places: gate 3 segments (drive) or gate cameras (static).
$places = @()
if ($Mode -eq 'Drive') {
    $segFile = Join-Path $RepoRoot "Data/Regions/$Region/gate3_segment.json"
    if (-not (Test-Path $segFile)) { Write-Host "missing $segFile - run: python scripts/gate3-segment.py --region $Region" -ForegroundColor Red; exit 2 }
    $segAll = (Get-Content $segFile -Raw | ConvertFrom-Json).segments
    foreach ($s in $Segments) {
        $spec = $segAll | Where-Object { $_.id -eq "G3-$s" }
        if (-not $spec) { Write-Host "segment G3-$s not in $segFile" -ForegroundColor Red; exit 2 }
        $drive = [int][Math]::Ceiling([double]$spec.length_m / ($SpeedKmh / 3.6) * 1.35)   # as gate3-run.ps1
        $places += [pscustomobject]@{ id = "G3-$s"; seconds = $LoadSeconds + $drive; warmup = $LoadSeconds; sStart = [double]$spec.s_start_m; sEnd = [double]$spec.s_end_m; camera = '' }
    }
} else {
    $camFile = Join-Path $RepoRoot "Data/Regions/$Region/gate3_cameras.json"
    if (-not (Test-Path $camFile)) { Write-Host "missing $camFile" -ForegroundColor Red; exit 2 }
    $camAll = (Get-Content $camFile -Raw | ConvertFrom-Json).cameras
    foreach ($c in $Cameras) {
        $spec = $camAll | Where-Object { $_.id -eq $c }
        if (-not $spec) { Write-Host "camera $c not in $camFile" -ForegroundColor Red; exit 2 }
        $places += [pscustomobject]@{ id = $c; seconds = $CameraSeconds; warmup = $CameraWarmupSeconds; sStart = $spec.truck_s_m; sEnd = $null; camera = $c }
    }
}
if ($places.Count -eq 0) { Write-Host 'no segment / camera selected' -ForegroundColor Red; exit 2 }

# Run list: repeat -> place -> blocks of (baseline + up to BaselineEvery variants).
$plan = @()
for ($rep = 1; $rep -le $Repeats; $rep++) {
    $order = @($tests | ForEach-Object { $_ })   # a copy: Reverse works in place
    if ($rep % 2 -eq 0) { [array]::Reverse($order) }
    foreach ($pl in $places) {
        $blk = 0
        for ($i = 0; $i -lt $order.Count; $i += $BaselineEvery) {
            $blk++
            $block = "$rep.$($pl.id).$blk"
            $plan += [pscustomobject]@{ variant = $baselineId; place = $pl; repeat = $rep; block = $block }
            $last = [Math]::Min($i + $BaselineEvery, $order.Count) - 1
            foreach ($id in $order[$i..$last]) { $plan += [pscustomobject]@{ variant = $id; place = $pl; repeat = $rep; block = $block } }
        }
    }
}
$fpsLabel = if ($Uncapped) { 'uncapped (fps 240)' } else { "$Fps" }
$overhead = 25   # s per run: launch, pull, screencap, dumpsys (WORKING_VALUE, not measured)
$totalS = ($plan | ForEach-Object { $_.place.seconds + $overhead } | Measure-Object -Sum).Sum
Write-Host "== gpu-ab: $($tests.Count) variant(s) + baseline, $($places.Count) place(s) [$(($places | ForEach-Object id) -join ', ')], $Repeats repeat(s), tier $Tier, cap $fpsLabel, mode $Mode"
Write-Host "   $($plan.Count) runs, about $([Math]::Round($totalS / 60)) min without cool-down waits (per run: place seconds + ~$overhead s)"
if ($DryRun) {
    Write-Host 'DRY RUN - plan only, nothing executed:'
    $n = 0
    foreach ($r in $plan) {
        $n++
        $ex = ($byId[$r.variant].extras.PSObject.Properties | ForEach-Object { "$($_.Name)=$($_.Value)" }) -join ','
        Write-Host ("   {0,3} rep {1} block {2,-22} {3,-18} {4,-8} {5,4}s  {6}" -f $n, $r.repeat, $r.block, $r.variant, $r.place.id, $r.place.seconds, $(if ($ex) { $ex } else { '(shipping state)' }))
    }
    exit 0
}

# ---------------------------------------------------------------- device
if (-not (Test-Path $Adb)) { Write-Host "adb not found: $Adb" -ForegroundColor Red; exit 2 }
if ((Get-AdbDevices) -notcontains $Serial) { Write-Host "device $Serial not attached" -ForegroundColor Red; exit 2 }
if (-not $OutDir) { $OutDir = Join-Path $ArtifactsDir "gpu-ab/$ts" }
if (-not [IO.Path]::IsPathRooted($OutDir)) { $OutDir = Join-Path $RepoRoot $OutDir }
$runsDir = Join-Path $OutDir 'runs'
New-Item -ItemType Directory -Force $runsDir | Out-Null
$log = Join-Path $OutDir 'gpu-ab.log'
function L([string]$m) { $s = "$(Get-Date -Format 'HH:mm:ss') $m"; Write-Host $s; Add-Content $log $s }

function Get-Battery {
    $txt = & $Adb -s $Serial shell dumpsys battery
    $t = $txt | Select-String '^\s*temperature:\s*(\d+)' | Select-Object -First 1
    $l = $txt | Select-String '^\s*level:\s*(\d+)' | Select-Object -First 1
    [pscustomobject]@{
        tempC = if ($t) { [double]$t.Matches[0].Groups[1].Value / 10 } else { $null }
        level = if ($l) { [int]$l.Matches[0].Groups[1].Value } else { $null }
    }
}
function Test-PhoneReady([string]$when) {
    if (-not (Test-DeviceUnlocked $Serial)) { L "REJECTED ($when): keyguard is showing on $Serial - unlock the phone (scripts never enter a PIN)"; return $false }
    $wake = (& $Adb -s $Serial shell dumpsys power) | Select-String 'mWakefulness=(\w+)' | Select-Object -First 1
    if ($wake -and $wake.Matches[0].Groups[1].Value -ne 'Awake') { L "REJECTED ($when): display is $($wake.Matches[0].Groups[1].Value)"; return $false }
    return $true
}
# Waits until the battery is below the limit. Returns the temperature, or $null when it did not cool down in time.
function Wait-Cool {
    $deadline = (Get-Date).AddMinutes($CooldownTimeoutMinutes)
    $stopped = $false
    while ($true) {
        $b = Get-Battery
        if ($null -ne $b.level -and $b.level -lt $MinBatteryPercent) { L "battery $($b.level) % < $MinBatteryPercent % - stopping"; return $null }
        if ($null -ne $b.tempC -and $b.tempC -lt $MaxBatteryC) { return $b.tempC }
        if ((Get-Date) -gt $deadline) { L "battery $($b.tempC) C still >= $MaxBatteryC C after $CooldownTimeoutMinutes min"; return $null }
        if (-not $stopped) { & $Adb -s $Serial shell am force-stop $PackageName | Out-Null; $stopped = $true }
        L "cooling: battery $($b.tempC) C >= $MaxBatteryC C, app stopped, next check in $CooldownPollSeconds s"
        Start-Sleep -Seconds $CooldownPollSeconds
    }
}
# Child pwsh without a pipe: an adb server spawned by the child would hold a pipe open forever (HANDOVER s20, pso-refresh.ps1).
# Same call as tools/perf/pso-refresh.ps1 (no redirection); the child's own output is not kept - its results are files.
function Invoke-Child([string]$script, [string[]]$scriptArgs) {
    $a = @('-NoProfile', '-File', "`"$script`"") + $scriptArgs
    $p = Start-Process pwsh -ArgumentList $a -Wait -PassThru -WindowStyle Hidden
    return $p.ExitCode
}

# ---------------------------------------------------------------- lock
$main = if ($env:KAMION_MAIN) { $env:KAMION_MAIN } else { 'C:\Users\matma\Documents\Claude\kamion' }
if (-not (Test-Path $main)) { $main = $RepoRoot }
$lockDir = Join-Path $main 'artifacts/locks'
$lock = Join-Path $lockDir 'PHONE_RUN'
New-Item -ItemType Directory -Force $lockDir | Out-Null
$ownLock = $false
if ($UseExistingLock) {
    if (-not (Test-Path $lock)) { Write-Host "-UseExistingLock: $lock does not exist - create it first (leader)" -ForegroundColor Red; exit 2 }
    L "using existing PHONE_RUN: $(Get-Content $lock -Raw)"
} else {
    while ($true) {
        if (-not (Test-Path $lock)) { try { New-Item -ItemType File $lock -ErrorAction Stop | Out-Null; Set-Content $lock "$Owner $(Get-Date -Format s) $OutDir"; $ownLock = $true; break } catch { } }
        L "waiting for PHONE_RUN: $(Get-Content $lock -ErrorAction SilentlyContinue)"; Start-Sleep -Seconds 60
    }
    L "PHONE_RUN taken ($Owner)"
}
if (@(Get-Process -Name Unity -ErrorAction SilentlyContinue).Count) { L 'WARNING: Unity is running - it restarts the adb daemon; the phone may drop offline mid-session' }

$exit = 0
$validRuns = 0
try {
    if (-not (Test-PhoneReady 'before the session')) { exit 5 }

    # ------------------------------------------------------------ APK (one install, the same APK for every variant)
    $apkInfo = [ordered]@{ file = '(already installed)'; sha256 = $null; builtFromSha = $null; dirty = $null }
    if ($Apk) {
        if (-not [IO.Path]::IsPathRooted($Apk)) { $Apk = Join-Path $RepoRoot $Apk }
        if (-not (Test-Path $Apk)) { L "-Apk not found: $Apk"; exit 2 }
        $Apk = (Resolve-Path $Apk).Path
        $meta = (& python (Join-Path $PSScriptRoot 'gate3_meta.py') apk --apk $Apk --repo $RepoRoot) -join "`n" | ConvertFrom-Json
        $apkInfo = [ordered]@{ file = $meta.apkFile; sha256 = $meta.apkSha256; builtFromSha = $meta.gitSha; dirty = $meta.dirty; path = $Apk }
        L "installing $($meta.apkFile) sha256 $($meta.apkSha256) built from $($meta.gitSha)$(if ($meta.dirty) { ' (DIRTY - not gate evidence)' })"
        $code = Invoke-Child (Join-Path $PSScriptRoot 'build-android.ps1') @('-Install', '-Serial', $Serial, '-SkipBuild', '-Apk', "`"$Apk`"")
        if ($code -ne 0) { L "install failed (exit $code); run: pwsh scripts/build-android.ps1 -Install -Serial $Serial -SkipBuild -Apk $Apk"; exit 4 }
    } else {
        $ver = (& $Adb -s $Serial shell dumpsys package $PackageName) | Select-String 'versionName=(\S+)' | Select-Object -First 1
        $apkInfo.versionName = if ($ver) { $ver.Matches[0].Groups[1].Value } else { $null }
        L "measuring the installed APK (versionName $($apkInfo.versionName)); pass -Apk to record its hash"
    }
    $props = [ordered]@{}
    foreach ($p in 'ro.product.model', 'ro.soc.model', 'ro.build.version.release', 'ro.hardware.egl') { $props[$p] = (& $Adb -s $Serial shell getprop $p).Trim() }
    $session = [ordered]@{
        schema = 'truck-sim-pl/gpu-ab-session/1'; timestamp = $ts; serial = $Serial; device = $props; tier = $Tier
        fps = $(if ($Uncapped) { 240 } else { $Fps }); fpsLabel = $fpsLabel; mode = $Mode; region = $Region; repeats = $Repeats
        baselineEvery = $BaselineEvery; warmupSeconds = $places[0].warmup; speedKmh = $SpeedKmh; maxBatteryC = $MaxBatteryC
        places = @($places | ForEach-Object id); variants = @($baselineId) + $tests; apk = $apkInfo
        catalog = $Catalog; repoHead = (Get-GitShortSha); plannedRuns = $plan.Count
    }
    $session | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $OutDir 'session.json') -Encoding utf8

    # ------------------------------------------------------------ runs
    $n = 0
    foreach ($r in $plan) {
        $n++
        $v = $byId[$r.variant]
        $pl = $r.place
        $name = '{0:D3}-r{1}-{2}-{3}' -f $n, $r.repeat, $r.variant, $pl.id
        $runDir = Join-Path $runsDir $name
        New-Item -ItemType Directory -Force $runDir | Out-Null
        $extras = [ordered]@{}
        foreach ($pr in $v.extras.PSObject.Properties) { $extras[$pr.Name] = "$($pr.Value)" }
        $run = [ordered]@{
            schema = 'truck-sim-pl/gpu-ab-run/1'; name = $name; variant = $r.variant; segment = $pl.id; repeat = $r.repeat; block = $r.block
            extras = $extras; tier = $Tier; fps = $session.fps; mode = $Mode; warmupSeconds = $pl.warmup; runSeconds = $pl.seconds
            valid = $false; rejectReason = ''; batteryTempBeforeC = $null; started = (Get-Date -Format s)
        }
        $stop = 0
        $temp = Wait-Cool
        if ($null -eq $temp) { $run.rejectReason = "battery not below $MaxBatteryC C (or level < $MinBatteryPercent %) - session stopped"; $stop = 7 }
        elseif (-not (Test-PhoneReady "before $name")) { $run.rejectReason = 'keyguard / display asleep before the run'; $stop = 5 }
        if ($stop -eq 0) {
            $run.batteryTempBeforeC = $temp
            & $Adb -s $Serial logcat -c
            # The variant label is always sent: the game logs "[GPUAB] ... abtag=<id>" and the run is checked against it.
            $kv = @("rq_abtag=$($r.variant)")
            foreach ($k in $extras.Keys) { $kv += "$k=$($extras[$k])" }
            $dm = @('-Serial', $Serial, '-Launch', '-DurationSeconds', "$($pl.seconds)", '-WarmupSeconds', "$($pl.warmup)", '-Tier', $Tier, '-Scene', 'WorldC')
            if ($Uncapped) { $dm += '-Uncapped' } else { $dm += @('-Fps', "$Fps") }
            if ($Mode -eq 'Drive') {
                $dm += @('-Autopilot', 'route', '-Speed', "$SpeedKmh", '-Trailer', '40')
                $kv += @('telemetry=1', "route_end=$($pl.sEnd)")
                if ($pl.sStart -gt 30) { $kv += "route_s=$($pl.sStart)" }   # the game spawns at s = 12 m (gate3-run.ps1)
            } else {
                $dm += @('-QaCamera', $pl.camera)
                if ($pl.camera -like 'g3*') { $kv += 'qacam_set=gate3' }
                if ($null -ne $pl.sStart) { $kv += "route_s=$($pl.sStart)" }
            }
            $dm += @('-Extra', ($kv -join ','))
            $devRoot = Join-Path $ArtifactsDir "device/$Serial"
            $before = @(Get-ChildItem $devRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object Name)
            L "run $n/$($plan.Count) $name ($($pl.seconds) s, battery $temp C): $($kv -join ' ')"
            $code = Invoke-Child (Join-Path $PSScriptRoot 'device-metrics.ps1') $dm
            $logRun = Join-Path $runDir 'logcat-run.txt'
            & $Adb -s $Serial logcat -d -v threadtime -s Unity:V AndroidRuntime:E DEBUG:E libc:F | Set-Content $logRun -Encoding utf8
            $readyAfter = Test-PhoneReady "after $name"
            $newDir = Get-ChildItem $devRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $before -notcontains $_.Name } | Sort-Object Name | Select-Object -Last 1
            if ($newDir) { Copy-Item (Join-Path $newDir.FullName '*') $runDir -Recurse -Force; $run.deviceDir = $newDir.FullName }
            $metricsFile = Join-Path $runDir 'metrics.json'
            $m = if (Test-Path $metricsFile) { Get-Content $metricsFile -Raw | ConvertFrom-Json } else { $null }
            $startPattern = if ($Mode -eq 'Drive') { '\[LAB\] DrivingLab ready:.*autopilot=route' } else { [regex]::Escape("control camera $($pl.camera) active") }
            $started = Select-String -Path $logRun -Pattern $startPattern -List
            $tagged = Select-String -Path $logRun -Pattern ("\[GPUAB\].*abtag=" + [regex]::Escape($r.variant) + '(\s|$)') -List
            $bad = @(Select-String -Path $logRun -Pattern 'Exception|FATAL|signal \d+ \(SIG|ANR in' | Where-Object { $_.Line -notmatch '\[DIAG\]' })
            $run.suspiciousLogLines = $bad.Count
            if ($m) { $run.thermalStatusAfter = $m.thermalStatus; $run.batteryTempAfterC = $m.batteryTempC }
            $reasons = @()
            if (-not $readyAfter) { $reasons += 'keyguard / display asleep after the run'; $stop = 5 }
            if ($code -ne 0 -or -not $m -or -not $m.frameTime) { $reasons += "frame log missing (device-metrics exit $code)" }
            if (-not $started) { $reasons += $(if ($Mode -eq 'Drive') { 'autopilot did not start (no [LAB] DrivingLab ready ... autopilot=route)' } else { "control camera $($pl.camera) not active" }) }
            if (-not $tagged -and -not $NoTagCheck) { $reasons += "no '[GPUAB] ... abtag=$($r.variant)' in logcat: APK without ADR 0241 switches or arguments not delivered" }
            if ($m -and $null -ne $m.thermalStatus -and $m.thermalStatus -ge 2) { $reasons += "thermal status $($m.thermalStatus) >= 2 after the run" }
            $run.valid = ($reasons.Count -eq 0)
            $run.rejectReason = $reasons -join '; '
            if ($run.valid) {
                $validRuns++
                $g = $m.gpuMs
                L ("   ok: frame p50 {0:F2} / p95 {1:F2} / p99 {2:F2} ms, GPU p50 {3} / p95 {4} ms, PSS {5} MB, battery {6} C, thermal {7}" -f $m.frameTime.p50Ms, $m.frameTime.p95Ms, $m.frameTime.p99Ms,
                    $(if ($g) { '{0:F2}' -f $g.p50 } else { 'n/a' }), $(if ($g) { '{0:F2}' -f $g.p95 } else { 'n/a' }), $m.pssMb, $m.batteryTempC, $m.thermalStatus)
            } else { L "   REJECTED: $($run.rejectReason)" }
        } else { L "run $name not started: $($run.rejectReason)" }
        $run.finished = (Get-Date -Format s)
        $run | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $runDir 'run.json') -Encoding utf8
        if ($stop -ne 0) { $exit = $stop; L "session stopped (exit $stop) after $n of $($plan.Count) runs"; break }
    }
} finally {
    try { & $Adb -s $Serial shell am force-stop $PackageName | Out-Null } catch { }
    if ($ownLock) { Remove-Item $lock -ErrorAction SilentlyContinue; L 'PHONE_RUN released' }
}

# ---------------------------------------------------------------- table
if ($validRuns -gt 0) {
    $rc = Invoke-Report $OutDir
    if ($rc -ne 0) { L "report failed (exit $rc): uv run --project tools/perf python -m perfgate.gpuab report $OutDir" }
    else { L "table: $(Join-Path $OutDir 'REPORT.md')" }
} elseif ($exit -eq 0) { $exit = 6; L 'no valid run' }
exit $exit
