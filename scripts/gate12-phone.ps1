<#
.SYNOPSIS
  Gates 1-2 (docs/03, Etap 1 i 2) on the phone: DrivingLab drives with vehicle telemetry, frame metrics, logcat and
  screenshots on the A16 (Low 30, reference phone) and optionally the S24+ (High, owner's phone - battery rules).
.DESCRIPTION
  What is measured automatically (the game's launch arguments, no game code changes):
    boot_idle        Boot scene, 75 s                          -> gate 0 numbers (empty scene)
    park_flat_solo   DrivingLab, solo tractor parked, 330 s     -> docs/04 s6.1 drift/oscillation on flat (parking brake)
    c50_solo_1..3    autopilot circle50 @ 40 km/h, solo, 90 s   -> 0->30/0->38 km/h repeatability (proxy, see report),
                                                                   speed hold, path radius, |dv| per step, physics step cost
    c25_solo         autopilot circle25 @ 25 km/h, solo, 75 s
    c50_empty        autopilot circle50 @ 40 km/h, empty combination (14.5 t), 90 s
    c50_40t          autopilot circle50 @ 40 km/h, 40 t combination, 150 s -> articulation, fifth wheel error, step cost
    s080_solo_1..3   autopilot straight080 (ADR 0195), solo, 70 s -> gate 1: 0->60/0->80 km/h x3 repeatability (+/-3 %),
                                                                   stop distance 80->0, MFDD, max decel, wheel slip
    s080_empty       autopilot straight080, empty combination (14.5 t), 80 s
    s080_40t         autopilot straight080, 40 t combination, 120 s -> gate 2: 0->80 and emergency stop 80->0, full trailer
  NOT automatable with the current game (manual / owner feel test, see GATE-1.md / GATE-2.md): 12 % hill hold and
  hill start, kerb 8/15 cm, jackknife, reversing to the dock, descent 7 %.
  Telemetry CSV (persistentDataPath/telemetry/drive-*.csv, 100 Hz) is pulled after each run; analysis:
  `uv run --project tools/perf python scripts/gate12_telemetry.py <OutDir>`.

  Safety: PHONE_RUN lock in the MAIN repo (taken here, or -UseExistingLock when the leader already holds it). Never runs
  while the lock belongs to someone else. Does not start Unity. Never types a PIN: a locked phone (keyguard) rejects the
  run. S24+ (RZCX60VE8ZY, owner's phone): starts only at battery >= 40 %, stops below 30 %, waits for battery < 36 C.
  A16 waits for battery < 34 C.
.EXAMPLE
  pwsh scripts/gate12-phone.ps1 -Apk artifacts/apk/kamion-0.1.0-<sha>.apk -DryRun
  pwsh scripts/gate12-phone.ps1 -Apk artifacts/apk/kamion-0.1.0-<sha>.apk -UseExistingLock            # A16 only
  pwsh scripts/gate12-phone.ps1 -Apk artifacts/apk/kamion-0.1.0-<sha>.apk -UseExistingLock -IncludeS24 # + S24+ (short set)
  pwsh scripts/gate12-phone.ps1 -SkipInstall -UseExistingLock -Only c50_40t                           # one run, installed APK
#>
param(
    [string]$Apk = '',
    [switch]$SkipInstall,
    [switch]$IncludeS24,
    [switch]$S24Only,
    [string]$A16Tier = 'Low', [int]$A16Fps = 30,
    [string]$S24Tier = 'High', [int]$S24Fps = 60,
    [string[]]$Only = @(),
    [switch]$UseExistingLock,
    [string]$Owner = 'gate12',
    [string]$OutDir = '',
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
$main = 'C:\Users\matma\Documents\Claude\kamion'
$lock = Join-Path $main 'artifacts\locks\PHONE_RUN'
$A16 = 'RFGL34SJYDZ'; $S24 = 'RZCX60VE8ZY'
$ts = Get-Timestamp
if (-not $OutDir) { $OutDir = Join-Path $ArtifactsDir "gate12/$ts" }
if (-not [IO.Path]::IsPathRooted($OutDir)) { $OutDir = Join-Path $RepoRoot $OutDir }
if ($Apk -and -not [IO.Path]::IsPathRooted($Apk)) { $Apk = Join-Path $RepoRoot $Apk }
New-Item -ItemType Directory -Force $OutDir | Out-Null
$log = Join-Path $OutDir 'gate12-phone.log'
function L($m) { $s = "$(Get-Date -Format 'HH:mm:ss') $m"; Write-Host $s; Add-Content $log $s }

# name, scene ('' = Boot), autopilot, speed, trailer, seconds, warmup
$A16Runs = @(
    @{ n = 'boot_idle';      scene = '';           ap = '';         v = 0;  tr = '';      s = 75;  w = 15 },
    @{ n = 'park_flat_solo'; scene = 'DrivingLab'; ap = '';         v = 0;  tr = 'solo';  s = 330; w = 25 },
    @{ n = 'c50_solo_1';     scene = 'DrivingLab'; ap = 'circle50'; v = 40; tr = 'solo';  s = 90;  w = 25 },
    @{ n = 'c50_solo_2';     scene = 'DrivingLab'; ap = 'circle50'; v = 40; tr = 'solo';  s = 90;  w = 25 },
    @{ n = 'c50_solo_3';     scene = 'DrivingLab'; ap = 'circle50'; v = 40; tr = 'solo';  s = 90;  w = 25 },
    @{ n = 'c25_solo';       scene = 'DrivingLab'; ap = 'circle25'; v = 25; tr = 'solo';  s = 75;  w = 25 },
    @{ n = 'c50_empty';      scene = 'DrivingLab'; ap = 'circle50'; v = 40; tr = 'empty'; s = 90;  w = 25 },
    @{ n = 'c50_40t';        scene = 'DrivingLab'; ap = 'circle50'; v = 40; tr = '40';    s = 150; w = 25 },
    # Straight 0-80-0 on the measurement straight (ADR 0195); sim time to the stop: solo 22 s, empty 29 s, 40 t 56 s (runner).
    @{ n = 's080_solo_1';    scene = 'DrivingLab'; ap = 'straight080'; v = 80; tr = 'solo';  s = 70;  w = 20 },
    @{ n = 's080_solo_2';    scene = 'DrivingLab'; ap = 'straight080'; v = 80; tr = 'solo';  s = 70;  w = 20 },
    @{ n = 's080_solo_3';    scene = 'DrivingLab'; ap = 'straight080'; v = 80; tr = 'solo';  s = 70;  w = 20 },
    @{ n = 's080_empty';     scene = 'DrivingLab'; ap = 'straight080'; v = 80; tr = 'empty'; s = 80;  w = 20 },
    @{ n = 's080_40t';       scene = 'DrivingLab'; ap = 'straight080'; v = 80; tr = '40';    s = 120; w = 20 }
)
# S24+ (owner's phone): short set - cost on the High tier only.
$S24Runs = @(
    @{ n = 'park_flat_solo'; scene = 'DrivingLab'; ap = '';         v = 0;  tr = 'solo';  s = 120; w = 25 },
    @{ n = 'c50_solo_1';     scene = 'DrivingLab'; ap = 'circle50'; v = 40; tr = 'solo';  s = 90;  w = 25 },
    @{ n = 'c50_40t';        scene = 'DrivingLab'; ap = 'circle50'; v = 40; tr = '40';    s = 150; w = 25 }
)
$plan = @()
if (-not $S24Only) { $plan += , @{ serial = $A16; tier = $A16Tier; fps = $A16Fps; runs = $A16Runs; cool = 34.0; owner = $false } }
if ($IncludeS24 -or $S24Only) { $plan += , @{ serial = $S24; tier = $S24Tier; fps = $S24Fps; runs = $S24Runs; cool = 36.0; owner = $true } }
if ($Only.Count) { foreach ($p in $plan) { $p.runs = @($p.runs | Where-Object { $Only -contains $_.n }) } }

# APK identity (clean build required for gate evidence).
$apkInfo = [ordered]@{ path = $Apk; sha256 = $null; dirty = $null; shaFileMatch = $null }
if ($Apk) {
    if (-not (Test-Path $Apk)) { throw "APK missing: $Apk" }
    $apkInfo.sha256 = (Get-FileHash $Apk -Algorithm SHA256).Hash.ToLower()
    $apkInfo.dirty = (Split-Path $Apk -Leaf) -match '-dirty'
    $shaFile = "$Apk.sha256"
    if (Test-Path $shaFile) { $apkInfo.shaFileMatch = ((Get-Content $shaFile -Raw) -split '\s+')[0].ToLower() -eq $apkInfo.sha256 }
} elseif (-not $SkipInstall) { throw 'pass -Apk <clean APK> or -SkipInstall (uses the installed build; gate evidence needs the APK hash)' }

L "plan -> $OutDir"
foreach ($p in $plan) { L ("  {0} {1}/{2}: {3}" -f $p.serial, $p.tier, $p.fps, (($p.runs | ForEach-Object { "$($_.n)($($_.s)s)" }) -join ' ')) }
L "  apk: $($apkInfo.path) sha256=$($apkInfo.sha256) dirty=$($apkInfo.dirty) shaFileMatch=$($apkInfo.shaFileMatch)"
if ($DryRun) { L 'DryRun: nothing executed'; exit 0 }
if ($apkInfo.dirty) { L 'WARNING: APK is -dirty - results are NOT valid gate evidence' }

function Get-Battery([string]$s) {
    $d = & $Adb -s $s shell dumpsys battery
    $lvl = ($d | Select-String '^\s*level:\s*(\d+)' | Select-Object -First 1).Matches[0].Groups[1].Value
    $tmp = ($d | Select-String '^\s*temperature:\s*(\d+)' | Select-Object -First 1).Matches[0].Groups[1].Value
    return @{ level = [int]$lvl; tempC = [double]$tmp / 10 }
}
function Wait-Online([string]$s) {
    for ($i = 0; $i -lt 20; $i++) {
        $st = "$((& $Adb -s $s get-state) 2>&1)"
        if ($st -match '^device') { return $true }
        L "$s not online ($st), retry in 30 s"; Start-Sleep -Seconds 30
    }
    return $false
}

# ---- lock
$ownLock = $false
if ($UseExistingLock) {
    if (-not (Test-Path $lock)) { throw "-UseExistingLock: $lock does not exist - create it first (leader)" }
    L "using existing PHONE_RUN: $(Get-Content $lock -Raw)"
} else {
    while ($true) {
        if (-not (Test-Path $lock)) { try { New-Item -ItemType File $lock -ErrorAction Stop | Out-Null; Set-Content $lock "$Owner $(Get-Date -Format s) $OutDir"; $ownLock = $true; break } catch { } }
        L "waiting for PHONE_RUN: $(Get-Content $lock -ErrorAction SilentlyContinue)"; Start-Sleep -Seconds 60
    }
    L "PHONE_RUN taken ($Owner)"
}
$unity = @(Get-Process -Name Unity -ErrorAction SilentlyContinue)
if ($unity.Count) { L "WARNING: $($unity.Count) Unity process(es) running - Unity restarts the adb daemon; phones may drop offline" }

$results = [ordered]@{ schema = 'truck-sim-pl/gate12-phone/1'; timestamp = $ts; apk = $apkInfo; gitHead = (Get-GitShortSha); devices = @() }
try {
    & $Adb start-server | Out-Null
    foreach ($p in $plan) {
        $s = $p.serial
        $dev = [ordered]@{ serial = $s; tier = $p.tier; fps = $p.fps; runs = @(); stopped = $null }
        $results.devices += $dev
        if (-not (Wait-Online $s)) { $dev.stopped = 'offline'; L "$s offline - skipped"; continue }
        $b = Get-Battery $s
        L "$s battery $($b.level) % $($b.tempC) C"
        if ($p.owner -and $b.level -lt 40) { $dev.stopped = "battery $($b.level) % < 40 % (owner's phone rule)"; L "$s SKIPPED: $($dev.stopped)"; continue }
        if ($Apk -and -not $SkipInstall) {
            L "$s install $Apk"
            & $Adb -s $s install -r $Apk | Out-Null
            if ($LASTEXITCODE -ne 0) { $dev.stopped = 'install failed'; L "$s install FAILED (exit $LASTEXITCODE)"; continue }
        }
        foreach ($r in $p.runs) {
            if (-not (Wait-Online $s)) { $dev.stopped = 'offline mid-run'; break }
            for ($i = 0; $i -lt 20; $i++) {
                $b = Get-Battery $s
                if ($p.owner -and $b.level -lt 30) { break }
                if ($b.tempC -lt $p.cool) { break }
                L "$s cooling: battery $($b.tempC) C"; & $Adb -s $s shell am force-stop $PackageName | Out-Null; Start-Sleep -Seconds 60
            }
            if ($p.owner -and $b.level -lt 30) { $dev.stopped = "battery $($b.level) % < 30 % - stop (owner's phone rule)"; L "$s STOP: $($dev.stopped)"; break }
            $rr = [ordered]@{ name = $r.n; scene = $r.scene; autopilot = $r.ap; speed = $r.v; trailer = $r.tr; seconds = $r.s; valid = $false; reasons = @()
                batteryBefore = $b; dir = $null }
            if (-not (Test-DeviceUnlocked $s)) { $rr.reasons += 'locked before run (keyguard)'; $dev.runs += $rr; L "$s $($r.n) REJECTED: phone locked - unlock it"; continue }
            $dst = Join-Path $OutDir "$s/$($r.n)"
            New-Item -ItemType Directory -Force $dst | Out-Null
            $rr.dir = $dst
            # Clear old telemetry so the pulled CSV belongs to this run.
            & $Adb -s $s shell rm -f "/sdcard/Android/data/$PackageName/files/telemetry/drive-*.csv" 2>&1 | Out-Null
            & $Adb -s $s logcat -c
            $dm = @('-NoProfile', '-File', (Join-Path $PSScriptRoot 'device-metrics.ps1'), '-Serial', $s, '-Launch', '-DurationSeconds', "$($r.s)",
                '-WarmupSeconds', "$($r.w)", '-Tier', $p.tier, '-Fps', "$($p.fps)")
            if ($r.scene) { $dm += @('-Scene', $r.scene) }
            if ($r.ap) { $dm += @('-Autopilot', $r.ap, '-Speed', "$($r.v)") }
            if ($r.tr) { $dm += @('-Trailer', $r.tr) }
            if ($r.scene) { $dm += @('-Extra', 'telemetry=1') }
            $devRoot = Join-Path $ArtifactsDir "device/$s"
            $before = @(Get-ChildItem $devRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object Name)
            L "$s run $($r.n) ($($r.s) s) scene=$($r.scene) ap=$($r.ap) v=$($r.v) trailer=$($r.tr)"
            & pwsh @dm | Out-Null
            # HOME -> OnApplicationPause flushes the telemetry CSV, then pull it.
            & $Adb -s $s shell input keyevent KEYCODE_HOME | Out-Null
            Start-Sleep -Seconds 3
            & $Adb -s $s pull "/sdcard/Android/data/$PackageName/files/telemetry" (Join-Path $dst 'telemetry') 2>&1 | Out-Null
            & $Adb -s $s logcat -d -v threadtime -s Unity:V AndroidRuntime:E DEBUG:E libc:F | Set-Content (Join-Path $dst 'logcat.txt') -Encoding utf8
            $new = Get-ChildItem $devRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $before -notcontains $_.Name } | Sort-Object Name | Select-Object -Last 1
            if ($new) { Copy-Item "$($new.FullName)\*" $dst -Recurse -Force } else { $rr.reasons += 'device-metrics produced no output' }
            $lc = Join-Path $dst 'logcat.txt'
            if ($r.scene) {
                $want = if ($r.ap) { "autopilot=$($r.ap)" } else { 'autopilot=off' }
                if (-not (Select-String -Path $lc -Pattern "\[LAB\] DrivingLab ready:.*$want" -Quiet)) { $rr.reasons += "no '[LAB] DrivingLab ready ... $want' in logcat" }
                if ($r.ap -eq 'straight080' -and -not (Select-String -Path $lc -Pattern '\[AUTOPILOT\] straight080 done' -Quiet)) { $rr.reasons += "straight run did not reach the stop (no '[AUTOPILOT] straight080 done' in logcat; longer -s?)" }
                if (-not (Get-ChildItem (Join-Path $dst 'telemetry') -Filter 'drive-*.csv' -ErrorAction SilentlyContinue)) { $rr.reasons += 'no telemetry CSV pulled' }
            }
            $bad = @(Select-String -Path $lc -Pattern 'Exception|FATAL|signal \d+ \(SIG|ANR in' -ErrorAction SilentlyContinue | Where-Object { $_.Line -notmatch '\[DIAG\]' })
            $rr.exceptionLines = $bad.Count
            if ($bad.Count) { $rr.reasons += "$($bad.Count) exception/crash lines in logcat" }
            if (-not (Test-DeviceUnlocked $s)) { $rr.reasons += 'locked after run (keyguard)' }
            if ($apkInfo.dirty) { $rr.reasons += 'APK -dirty' }
            if (-not (Test-Path (Join-Path $dst 'metrics.json'))) { $rr.reasons += 'metrics.json missing' }
            $rr.valid = ($rr.reasons.Count -eq 0)
            $rr.batteryAfter = Get-Battery $s
            & $Adb -s $s shell am force-stop $PackageName | Out-Null
            $dev.runs += $rr
            L "$s done $($r.n): valid=$($rr.valid) $($rr.reasons -join '; ')"
            $results | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $OutDir 'gate12-runs.json') -Encoding utf8
        }
    }
}
catch { L "ERROR $_"; $results.error = "$_" }
finally {
    foreach ($p in $plan) { & $Adb -s $p.serial shell am force-stop $PackageName 2>&1 | Out-Null }
    if ($ownLock) { Remove-Item $lock -Force -ErrorAction SilentlyContinue; L 'PHONE_RUN released' }
    $results | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $OutDir 'gate12-runs.json') -Encoding utf8
}
L "next: uv run --project tools/perf python scripts/gate12_telemetry.py $OutDir"
$anyInvalid = @($results.devices | ForEach-Object { $_.runs } | Where-Object { -not $_.valid }).Count
exit $(if ($results.error) { 3 } elseif ($anyInvalid) { 4 } else { 0 })
