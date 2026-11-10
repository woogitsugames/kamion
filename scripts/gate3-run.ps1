<#
.SYNOPSIS
  Gate 3 run on ONE phone: build -> install -> autopilot drive of the quality-sample segment with metrics -> control cameras.
  Reuses build-android.ps1 and device-metrics.ps1; adds the lock checks, segment/camera plan and a result JSON.
.DESCRIPTION
  Segment and camera definitions: Data/Regions/<region>/gate3_segment.json and gate3_cameras.json
  (regenerate with `python scripts/gate3-segment.py`). Plan: docs/plan/STAGE-3.md.
  The phone must be UNLOCKED and awake: isKeyguardShowing is checked before install, before the run, after the run
  and before every camera frame. A measurement taken while the keyguard showed is REJECTED (exit 5), never reported.
  Never types a PIN. Never touches the game code: launch arguments the game does not read yet are detected by grepping
  the Unity sources and the step is refused/skipped with a clear status (STAGE-3.md section 5).
  One Unity process per project: this script starts Unity (build) - do not run it while another Unity/build is active.
.EXAMPLE
  pwsh scripts/gate3-run.ps1 -Serial RFGL34SJYDZ -Tier Low  -Fps 30                    # A16, segment G3-A
  pwsh scripts/gate3-run.ps1 -Serial RZCX60VE8ZY -Tier High -Fps 60 -WorldHigh         # S24+, High world content
  pwsh scripts/gate3-run.ps1 -Serial RFGL34SJYDZ -Tier Low -SkipBuild -SkipCameras     # re-measure with the installed APK
  pwsh scripts/gate3-run.ps1 -Serial X -Tier High -SkipBuild -Apk artifacts/apk/kamion-0.1.0-<sha>-high.apk       # exact APK
  pwsh scripts/gate3-run.ps1 -Serial X -Tier Low -DryRun                              # validate plan, no adb/Unity
.NOTES
  Exit: 0 all requested steps done and measurement valid; 2 plan/prerequisite error; 3 unsupported segment (game lacks
  launch arg; no longer the case once route_s exists in the game sources, the check greps for it); 4 build/install failed; 5 phone locked/asleep (measurement rejected); 6 metrics missing.
  Output: artifacts/gate3/<ts>/<serial>/ (gate3-result.json, metrics copy, logcat, cam/<id>.png).
  Verdicts compare with docs/PERFORMANCE_BUDGETS.md WORKING_VALUEs; they are measurements, not the owner's gate decision.
#>
param(
    [Parameter(Mandatory = $true)] [string]$Serial,
    [ValidateSet('A', 'B')] [string]$Segment = 'A',
    [Parameter(Mandatory = $true)] [ValidateSet('Low', 'Medium', 'High', 'Ultra')] [string]$Tier,
    [int]$Fps = 30,
    [int]$SpeedKmh = 30,
    [string]$Region = 'bialystok-industrial-c',
    [switch]$WorldHigh,
    [switch]$SkipBuild,
    # With -SkipBuild: the exact APK to install. Default: newest artifacts/apk/*.apk of the variant that matches the run
    # (-high when -WorldHigh or -Tier High/Ultra, otherwise the plain one; never -dev unless -Development).
    [string]$Apk = '',
    [switch]$SkipCameras,
    [switch]$Development,
    [int]$LoadSeconds = 25,
    [int]$CameraWaitSeconds = 30,
    [string]$CameraFilter = '',
    # Truck-mounted control cameras (TruckAssetBuilder: truck-34, cab-dash) framed on the phone under each lighting preset (r6 section 8 #1).
    # Taken only for segment A (they do not depend on the segment); pass -TruckCameras @() to skip.
    [string[]]$TruckCameras = @('truck-34', 'cab-dash'),
    [string[]]$TruckLightings = @('overcast', 'lowsun', 'dusk'),
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
$ts = Get-Timestamp
$segId = "G3-$Segment"
$exit = 0

# ---------------------------------------------------------------- plan
$segFile = Join-Path $RepoRoot "Data/Regions/$Region/gate3_segment.json"
$camFile = Join-Path $RepoRoot "Data/Regions/$Region/gate3_cameras.json"
foreach ($f in $segFile, $camFile) { if (-not (Test-Path $f)) { Write-Host "missing $f - run: python scripts/gate3-segment.py --region $Region" -ForegroundColor Red; exit 2 } }
$segSpec = (Get-Content $segFile -Raw | ConvertFrom-Json).segments | Where-Object { $_.id -eq $segId }
$camSpec = Get-Content $camFile -Raw | ConvertFrom-Json
if (-not $segSpec) { Write-Host "segment $segId not in $segFile" -ForegroundColor Red; exit 2 }
$lengthM = [double]$segSpec.length_m
$driveSeconds = [int][Math]::Ceiling($lengthM / ($SpeedKmh / 3.6) * 1.35)   # 40 t combination accelerates from rest; margin
$runSeconds = $LoadSeconds + $driveSeconds
$cams = @($camSpec.cameras | Where-Object { $_.segment -eq $segId })
if ($CameraFilter) { $cams = @($cams | Where-Object { $_.id -match $CameraFilter }) }
$reuse = @($camSpec.reuse_from_control_cameras)

# Launch-argument support in the game (read from the sources, never assumed).
$src = Join-Path $RepoRoot 'game/Assets/_Project'
function Test-LaunchArg([string]$name) { [bool](Get-ChildItem $src -Recurse -Filter *.cs | Select-String -Pattern "GetLaunchArgument\(""$name""\)" -List) }
$hasRouteS = Test-LaunchArg 'route_s'
$hasGate3Cams = Test-LaunchArg 'qacam_set'
$needRouteS = [bool]($segSpec.s_start_m -gt 30)   # the game spawns at s=12 m (WorldSceneBuilder spawnS); G3-B starts further on

Write-Host "== gate3: segment $segId s=$($segSpec.s_start_m)..$($segSpec.s_end_m) ($lengthM m), tier $Tier, $Fps fps, $SpeedKmh km/h, run ${runSeconds}s ($LoadSeconds s load + $driveSeconds s drive)"
Write-Host "   cameras: $($cams.Count) from gate3_cameras.json + $($reuse.Count) existing control cameras; game reads route_s: $hasRouteS, qacam_set: $hasGate3Cams"
if ($needRouteS -and -not $hasRouteS) {
    Write-Host "REFUSED: segment $segId starts at s=$($segSpec.s_start_m) m but the game has no 'route_s' launch argument (spawn at s along the route). See docs/plan/STAGE-3.md section 5." -ForegroundColor Red
    exit 3
}
if ($DryRun) {
    Write-Host 'DRY RUN - plan only, nothing executed. Cameras:'
    $cams | ForEach-Object { Write-Host ("   {0,-28} {1,-12} truck_s={2}" -f $_.id, $_.kind, $_.truck_s_m) }
    $dryHigh = [bool]($WorldHigh -or $Tier -in @('High', 'Ultra'))
    $dryApk = if ($Apk) { $Apk } else { (& python (Join-Path $PSScriptRoot 'gate3_meta.py') pick --dir (Join-Path $ArtifactsDir 'apk') --high $(if ($dryHigh) { 1 } else { 0 }) --dev $(if ($Development) { 1 } else { 0 }) | Select-Object -First 1) }
    if ($SkipBuild) { Write-Host "   would INSTALL (-SkipBuild): $(if ($dryApk) { $dryApk } else { '<none found for this tier>' })" } else { Write-Host '   would BUILD, then install the fresh APK' }
    if ($dryApk -and (Test-Path $dryApk)) { (& python (Join-Path $PSScriptRoot 'gate3_meta.py') apk --apk $dryApk --repo $RepoRoot) | Write-Host }
    exit 0
}

# ---------------------------------------------------------------- device + lock gate
if (-not (Test-Path $Adb)) { Write-Host "adb not found: $Adb" -ForegroundColor Red; exit 2 }
if ((Get-AdbDevices) -notcontains $Serial) { Write-Host "device $Serial not attached" -ForegroundColor Red; exit 2 }

function Assert-PhoneReady([string]$when) {
    # Test-DeviceUnlocked wakes the screen and reads isKeyguardShowing; we additionally require an awake display.
    if (-not (Test-DeviceUnlocked $Serial)) {
        Write-Host "REJECTED ($when): keyguard is showing on $Serial - unlock the phone (scripts never enter a PIN)." -ForegroundColor Red
        return $false
    }
    $wake = (& $Adb -s $Serial shell dumpsys power) | Select-String 'mWakefulness=(\w+)' | Select-Object -First 1
    if ($wake -and $wake.Matches[0].Groups[1].Value -ne 'Awake') {
        Write-Host "REJECTED ($when): display is $($wake.Matches[0].Groups[1].Value) on $Serial." -ForegroundColor Red
        return $false
    }
    return $true
}

$outRoot = Join-Path $ArtifactsDir "gate3/$ts/$Serial"
New-Item -ItemType Directory -Force (Join-Path $outRoot 'cam') | Out-Null
$result = [ordered]@{
    schema = 'truck-sim-pl/gate3-result/1'; timestamp = $ts; serial = $Serial; segment = $segId
    segmentSpec = [ordered]@{ s_start_m = $segSpec.s_start_m; s_end_m = $segSpec.s_end_m; length_m = $lengthM }
    tier = $Tier; fps = $Fps; speedKmh = $SpeedKmh; worldHigh = [bool]$WorldHigh; gitSha = $null   # set from the installed APK below, never from HEAD
    gameLacks = @(); valid = $false
}
if (-not $hasGate3Cams) { $result.gameLacks += "qacam_set (gate3_cameras.json not loaded in the scene -> g3* cameras cannot be framed on the phone)" }

if (-not (Assert-PhoneReady 'before install')) { exit 5 }

# gate3_cameras.json is read by the game from Resources (qacam_set=gate3): refresh the copy so the APK carries the current file.
if (-not $SkipBuild -and $hasGate3Cams) {
    $resDir = Join-Path $RepoRoot 'game/Assets/_Project/Gameplay/Resources'
    New-Item -ItemType Directory -Force $resDir | Out-Null
    Copy-Item $camFile (Join-Path $resDir 'gate3_cameras.json') -Force
}

# ---------------------------------------------------------------- 1. build + install (build-android.ps1)
$metaPy = Join-Path $PSScriptRoot 'gate3_meta.py'
$wantHigh = [bool]($WorldHigh -or $Tier -in @('High', 'Ultra'))
$apkDir = Join-Path $ArtifactsDir 'apk'
$baArgs = @('-Install', '-Serial', $Serial)
if ($WorldHigh) { $baArgs += '-WorldHigh' }
if ($Development) { $baArgs += '-Development' }
if ($SkipBuild) {
    # Never "the newest file": Low and -high APKs sit side by side (r7 section 7).
    $apkPath = $Apk
    if (-not $apkPath) {
        $apkPath = (& python $metaPy pick --dir $apkDir --high $(if ($wantHigh) { 1 } else { 0 }) --dev $(if ($Development) { 1 } else { 0 }) | Select-Object -First 1)
        if (-not $apkPath) { Write-Host "no $(if ($wantHigh) { '-high' } else { 'plain (Low/Medium)' }) APK in $apkDir for -Tier $Tier - pass -Apk <path> or build" -ForegroundColor Red; exit 2 }
    }
    if (-not (Test-Path $apkPath)) { Write-Host "-Apk not found: $apkPath" -ForegroundColor Red; exit 2 }
    $apkPath = (Resolve-Path $apkPath).Path
    $baArgs += @('-SkipBuild', '-Apk', $apkPath)
    Write-Host "INSTALLING APK (-SkipBuild, $(if ($Apk) { 'explicit -Apk' } else { 'auto-picked for tier ' + $Tier })): $apkPath"
}
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'build-android.ps1') @baArgs
if ($LASTEXITCODE -ne 0) { Write-Host "build/install failed (exit $LASTEXITCODE)" -ForegroundColor Red; exit 4 }
if (-not $SkipBuild) {
    $apkItem = Get-ChildItem $apkDir -Filter *.apk | Where-Object { ($_.Name -match '-high\.apk$|-high-dev\.apk$') -eq [bool]$WorldHigh -and ($_.Name -match '-dev\.apk$') -eq [bool]$Development } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $apkPath = $apkItem.FullName
}
# Identity of the installed APK comes from the APK (name + hash), not from `git rev-parse HEAD` at measurement time (r7 section 7).
$meta = (& python $metaPy apk --apk $apkPath --repo $RepoRoot) -join "`n" | ConvertFrom-Json
$apkFi = Get-Item $apkPath
$result.apkFile = $meta.apkFile; $result.apkSha256 = $meta.apkSha256
$result.gitSha = $meta.gitSha; $result.repoHeadAtMeasurement = (Get-GitShortSha)
$result.apkDirty = $meta.dirty
$result.apk = [ordered]@{ path = $apkPath; file = $meta.apkFile; sizeMB = [Math]::Round($apkFi.Length / 1MB, 1); sha256 = $meta.apkSha256; builtFromSha = $meta.gitSha; dirty = $meta.dirty }
$result.warnings = @($meta.warnings)
if ($wantHigh -and $meta.high -eq $false) { $result.warnings += "tier $Tier / WorldHigh run but the APK is not a -high build" }
if (-not $wantHigh -and $meta.high -eq $true) { $result.warnings += "tier $Tier run with a -high APK (World content High)" }
if ($meta.dirty) { $result.valid = $false }
foreach ($w in $result.warnings) { Write-Host "WARNING: $w" -ForegroundColor Yellow }
Write-Host "APK $($meta.apkFile) $($result.apk.sizeMB) MB sha256 $($meta.apkSha256) built from $($meta.gitSha)$(if ($meta.dirty) { ' (DIRTY)' }) (repo HEAD now $($result.repoHeadAtMeasurement))"

# ---------------------------------------------------------------- 2. autopilot drive + metrics
if (-not (Assert-PhoneReady 'before drive')) { exit 5 }
& $Adb -s $Serial logcat -c
$batt0 = (& $Adb -s $Serial shell dumpsys battery) | Select-String '^\s*temperature:\s*(\d+)' | Select-Object -First 1
$result.batteryTempBeforeC = if ($batt0) { [double]$batt0.Matches[0].Groups[1].Value / 10 } else { $null }
$dm = @('-NoProfile', '-File', (Join-Path $PSScriptRoot 'device-metrics.ps1'), '-Serial', $Serial, '-Launch',
    '-DurationSeconds', "$runSeconds", '-WarmupSeconds', "$LoadSeconds", '-Tier', $Tier, '-Fps', "$Fps",
    '-Scene', 'WorldC', '-Autopilot', 'route', '-Speed', "$SpeedKmh", '-Trailer', '40')
$extra = @('telemetry=1')
if ($needRouteS) { $extra += "route_s=$($segSpec.s_start_m)" }
if (Test-LaunchArg 'route_end') { $extra += "route_end=$($segSpec.s_end_m)" } else { $result.gameLacks += 'route_end (autopilot does not stop at s_end; the drive window is time-limited)' }
$dm += @('-Extra', ($extra -join ','))
$before = @(Get-ChildItem (Join-Path $ArtifactsDir "device/$Serial") -Directory -ErrorAction SilentlyContinue | ForEach-Object Name)
& pwsh @dm
$dmExit = $LASTEXITCODE
$logRun = Join-Path $outRoot 'logcat-run.txt'
& $Adb -s $Serial logcat -d -v threadtime -s Unity:V AndroidRuntime:E DEBUG:E libc:F | Set-Content $logRun -Encoding utf8
$locked = -not (Assert-PhoneReady 'after drive')
$newDir = Get-ChildItem (Join-Path $ArtifactsDir "device/$Serial") -Directory | Where-Object { $before -notcontains $_.Name } | Sort-Object Name | Select-Object -Last 1
if ($newDir) { Copy-Item $newDir.FullName (Join-Path $outRoot 'drive') -Recurse -Force }
$ready = Select-String -Path $logRun -Pattern '\[LAB\] DrivingLab ready:.*autopilot=route' -List
$bad = Select-String -Path $logRun -Pattern 'Exception|FATAL|signal \d+ \(SIG|ANR in' | Where-Object { $_.Line -notmatch '\[DIAG\]' }
$result.driveLog = [ordered]@{ autopilotStartedLine = [bool]$ready; suspiciousLines = @($bad).Count; logcat = $logRun }
if ($locked) { $result.rejected = 'keyguard/asleep after the drive: measurement invalid'; $result | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $outRoot 'gate3-result.json') -Encoding utf8; exit 5 }
if ($dmExit -ne 0 -or -not $newDir -or -not (Test-Path (Join-Path $newDir.FullName 'metrics.json'))) {
    Write-Host 'metrics missing (device-metrics exit ' $dmExit ')' -ForegroundColor Red
    $result | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $outRoot 'gate3-result.json') -Encoding utf8; exit 6
}
$m = Get-Content (Join-Path $newDir.FullName 'metrics.json') -Raw | ConvertFrom-Json
$result.device = $m.device; $result.frameTime = $m.frameTime; $result.gpuMs = $m.gpuMs; $result.cpuMainMs = $m.cpuMainMs
$result.pssMb = $m.pssMb; $result.batteryTempAfterC = $m.batteryTempC; $result.thermalStatus = $m.thermalStatus
$result.valid = [bool]($ready -and $m.frameTime -and $m.frameTime.samples -gt 100 -and -not $meta.dirty)
if ($meta.dirty) { $result.gameLacks += 'APK is -dirty: not valid gate evidence (rebuild from a clean commit)' }
if (-not $ready) { $result.gameLacks += "no '[LAB] DrivingLab ready ... autopilot=route' in logcat: the autopilot did not start (scene/route missing?)" }

# Budget comparison (docs/PERFORMANCE_BUDGETS.md WORKING_VALUEs).
$b = switch ($Tier) {
    'Low' { @{ p95 = 34.0; p99 = 40.0; pss = 1000 } }
    'Medium' { @{ p95 = 34.0; p99 = 40.0; pss = 1200 } }
    default { @{ p95 = 17.0; p99 = 20.0; pss = 2000 } }
}
if ($m.frameTime) {
    $result.budget = [ordered]@{ p95Ms = $b.p95; p99Ms = $b.p99; pssMb = $b.pss; source = 'docs/PERFORMANCE_BUDGETS.md (WORKING_VALUE)'
        p95Ok = ($m.frameTime.p95Ms -le $b.p95); p99Ok = ($m.frameTime.p99Ms -le $b.p99); pssOk = ($m.pssMb -le $b.pss) }
    Write-Host ("FPS: p50 {0:F1} / p95 {1:F1} / p99 {2:F1} ms, PSS {3} MB, thermal {4} -> p95 {5}, p99 {6}, PSS {7}" -f $m.frameTime.p50Ms, $m.frameTime.p95Ms, $m.frameTime.p99Ms, $m.pssMb, $m.thermalStatus,
        $(if ($result.budget.p95Ok) { 'ok' } else { 'OVER' }), $(if ($result.budget.p99Ok) { 'ok' } else { 'OVER' }), $(if ($result.budget.pssOk) { 'ok' } else { 'OVER' }))
}

# ---------------------------------------------------------------- 3. control cameras (device frames)
$camResults = @(); $ids = @(); $seenMd5 = @{}
if (-not $SkipCameras) {
    $ids = @($cams | ForEach-Object { $_ }) + @($reuse | Where-Object { $_ -match $CameraFilter } | ForEach-Object { [pscustomobject]@{ id = $_; truck_s_m = $null; kind = 'existing' } })
    if ($Segment -eq 'A') {
        foreach ($tc in $TruckCameras) { foreach ($lg in $TruckLightings) {
            if ($CameraFilter -and ($tc -notmatch $CameraFilter)) { continue }
            $ids += [pscustomobject]@{ id = $tc; truck_s_m = $null; kind = 'truck'; lighting = $lg } } }
    }
    foreach ($c in $ids) {
        $lightTag = if ($c.PSObject.Properties['lighting']) { $c.lighting } else { '' }
        $frameId = if ($lightTag) { "$($c.id)_$lightTag" } else { $c.id }
        if (-not (Assert-PhoneReady "before camera $($c.id)")) { $camResults += [ordered]@{ id = $frameId; status = 'REJECTED_LOCKED' }; $exit = 5; break }
        $ex = @()
        if ($null -ne $c.truck_s_m) {
            if (-not $hasRouteS) { $camResults += [ordered]@{ id = $frameId; status = 'SKIPPED_NEEDS_route_s' }; continue }
            $ex += "route_s=$($c.truck_s_m)"
        }
        if ($c.id -like 'g3*' -and $hasGate3Cams) { $ex += 'qacam_set=gate3' }
        if ($lightTag) { $ex += "lighting=$lightTag" }
        $png = Join-Path $outRoot "cam/$frameId.png"
        $status = 'NO_SCREENSHOT'; $md5 = $null; $dupOf = $null; $locked2 = $false
        # A frame byte-identical to an earlier camera's frame is not a frame of THIS camera (r7 section 7: s1532 == s1482): retake once, then flag.
        foreach ($attempt in 1, 2) {
            & $Adb -s $Serial logcat -c
            $cmArgs = @('-NoProfile', '-File', (Join-Path $PSScriptRoot 'device-metrics.ps1'), '-Serial', $Serial, '-Launch', '-DurationSeconds', "$CameraWaitSeconds",
                '-Tier', $Tier, '-Fps', "$Fps", '-Scene', 'WorldC', '-QaCamera', $c.id)
            if ($ex) { $cmArgs += @('-Extra', ($ex -join ',')) }
            $b4 = @(Get-ChildItem (Join-Path $ArtifactsDir "device/$Serial") -Directory | ForEach-Object Name)
            Remove-Item $png -ErrorAction SilentlyContinue
            & pwsh @cmArgs | Out-Null
            $lg = (& $Adb -s $Serial logcat -d -v threadtime -s Unity:V) -join "`n"
            $locked2 = -not (Assert-PhoneReady "after camera $($c.id)")
            $d = Get-ChildItem (Join-Path $ArtifactsDir "device/$Serial") -Directory | Where-Object { $b4 -notcontains $_.Name } | Sort-Object Name | Select-Object -Last 1
            $active = $lg -match [regex]::Escape("control camera $($c.id) active")
            if ($d -and (Test-Path (Join-Path $d.FullName 'screen.png'))) { Copy-Item (Join-Path $d.FullName 'screen.png') $png -Force }
            $status = if ($locked2) { 'REJECTED_LOCKED' } elseif (-not $active) { 'MISSING_IN_SCENE' } elseif (Test-Path $png) { 'CAPTURED' } else { 'NO_SCREENSHOT' }
            if ($status -eq 'MISSING_IN_SCENE') { Remove-Item $png -ErrorAction SilentlyContinue }   # a frame of the wrong camera is not evidence
            $dupOf = $null
            if ($status -eq 'CAPTURED') {
                $md5 = (Get-FileHash -Algorithm MD5 $png).Hash.ToLower()
                if ($seenMd5.ContainsKey($md5)) { $dupOf = $seenMd5[$md5] } else { $seenMd5[$md5] = $frameId }
            }
            if (-not $dupOf -or $locked2) { break }
            Write-Host "  cam $frameId identical to $dupOf (md5 $md5) - retaking once" -ForegroundColor Yellow
        }
        if ($dupOf) { $status = 'DUPLICATE_FRAME'; $result.warnings += "frame $frameId is byte-identical to $dupOf (md5 $md5): not evidence of this camera" }
        $camResults += [ordered]@{ id = $frameId; status = $status; md5 = $md5; duplicateOf = $dupOf; png = $(if ($status -eq 'CAPTURED') { $png } else { $null }) }
        Write-Host ("  cam {0,-28} {1}" -f $frameId, $status)
        if ($locked2) { $exit = 5; break }
    }
}
$result.cameras = $camResults
$result.camerasCaptured = @($camResults | Where-Object { $_.status -eq 'CAPTURED' }).Count
$result.camerasPlanned = $ids.Count
$dupFrames = @($camResults | Where-Object { $_.status -eq 'DUPLICATE_FRAME' })
$result.duplicateFrames = @($dupFrames | ForEach-Object { "$($_.id) == $($_.duplicateOf)" })
if ($dupFrames.Count -gt 0) { $result.valid = $false; Write-Host "INVALID: $($dupFrames.Count) duplicate camera frame(s): $($result.duplicateFrames -join '; ')" -ForegroundColor Red }
$result | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $outRoot 'gate3-result.json') -Encoding utf8
Write-Host "result $(Join-Path $outRoot 'gate3-result.json'): valid=$($result.valid), cameras $($result.camerasCaptured)/$($result.camerasPlanned)"
if (-not $result.valid -and $exit -eq 0) { $exit = 6 }
exit $exit
