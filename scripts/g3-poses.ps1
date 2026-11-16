<#
.SYNOPSIS
  Gate 3 photo pairs (ADR 0246, BACKLOG B-111): frames of the 42 photo-pair poses rendered by the PLAYER and composed side
  by side with the reference photo. Two modes, mutually exclusive:
    -Exe <Kamion.exe>   Windows player (main platform since D73 / ADR 0260) -> artifacts/g3-poses/win/<ts>/
    -Serial <serial>    phone, Development APK through adb (DEFERRED by D73; kept working, behaviour unchanged)
                        -> artifacts/gate3/poses/<serial>/<ts>/
.DESCRIPTION
  WINDOWS (-Exe): no adb, no Unity. Takes an already built DEVELOPMENT player (scripts/build-windows.ps1 -Development ->
  artifacts/win/kamion-<ver>-<sha>-dev/Kamion.exe; a release player refuses g3pose) and starts ONE process per lighting
  preset: windowed (-screen-fullscreen 0 -screen-width/-screen-height, ADR 0261), `-logFile`, `-scene WorldC -tier <Tier>
  -lighting <preset> -g3pose 1 -g3pose_run <id> -g3pose_dir <out>/<preset> -g3pose_quit 1`. The in-game runner renders every
  pose off-screen (window size does not change the frames), writes NN_<id>_<preset>.png + manifest.json straight into the
  output folder and quits. The command line and the verdict come from scripts/g3_poses.py (winargs / verify, pytest
  tests/gate3/test_g3_poses.py). Default tier High (D74 class "zalecany"). Exit 6 when a PNG is missing or duplicated, the
  log holds an exception / FAIL / REFUSED line, the player exit code is not 0, or the run hit -TimeoutSeconds (TIMEOUT).
  Keep the machine otherwise idle; frames are evidence for the visual review, not a performance measurement.

  PHONE (-Serial), deferred (D73):
  Poses: game/Assets/_Project/Gameplay/Resources/g3_poses.json (= Data/Regions/<region>/g3_poses.json), generated from
  sbs_cameras.json + sbs_references.json by `python scripts/g3_poses.py export`; checked here before anything runs.
  The game side (Game.Gameplay.G3PoseRunner, Development builds only) is started with launch arguments
  `-e scene WorldC -e g3pose 1 -e g3pose_run <id> -e lighting <preset>`, renders every pose off-screen at 1280 px x photo
  aspect (same size and render path as the editor pairs of scripts/sbs-gate3.ps1) and logs `[G3POSE] SHOT ...` lines and a
  final `[G3POSE] DONE ...` marker, which this script waits for.
  Phone: must be UNLOCKED. isKeyguardShowing is checked before install, before every run and while waiting; a run during
  which the keyguard showed is REJECTED (exit 5). Never types a PIN, never sends KEYCODE_SLEEP / KEYCODE_POWER (only
  KEYCODE_WAKEUP, through env.ps1 Test-DeviceUnlocked). Battery temperature is read before each run; above -MaxBatteryC
  the run is refused (exit 7) - let the phone cool down.
  Reference photos are outside git (Data/raw, artifacts/sbs-gate3/rectified): -RefDir names a folder that holds them
  (file names as in sbs_references.json comparison_photo / photo); without it the main checkout paths are tried.
  Side-by-side needs ImageMagick (`magick`); without it the phone frames are still pulled and the step says so.
  One Unity per project: -Build starts Unity (build-android.ps1) - not while another Unity/build runs. Unity restarts the
  adb daemon: do not run Unity while this script talks to the phone.
.EXAMPLE
  pwsh scripts/g3-poses.ps1 -Exe artifacts/win/kamion-0.1.0-<sha>-dev/Kamion.exe -RefDir D:/refs/g3   # Windows: 42 x overcast + clear, tier High
  pwsh scripts/g3-poses.ps1 -Exe <Kamion.exe> -Only 1-2 -Lighting overcast                            # Windows smoke test, 2 poses
  pwsh scripts/g3-poses.ps1 -Exe <Kamion.exe> -DryRun                                                 # plan + command lines; needs no exe, no Windows
  pwsh scripts/g3-poses.ps1 -Serial RFGL34SJYDZ -Build                                   # build Development APK, install, overcast + clear
  pwsh scripts/g3-poses.ps1 -Serial RFGL34SJYDZ -Apk artifacts/apk/kamion-0.1.0-<sha>-dev.apk -RefDir D:/refs/g3   # install that APK
  pwsh scripts/g3-poses.ps1 -Serial RFGL34SJYDZ -Lighting overcast -Only 1-3,cm924       # installed APK, 4 poses, one light
  pwsh scripts/g3-poses.ps1 -Serial RFGL34SJYDZ -DryRun                                  # plan only, no adb / Unity
.NOTES
  Exit: 0 every requested frame captured (and composed when ImageMagick and the photo exist); 2 prerequisite / plan error;
  4 build or install failed; 5 phone locked (run rejected); 6 capture incomplete (timeout, crash, missing or duplicate
  frames, exception in the log, release build refused); 7 battery too hot.
  Output, same layout in both modes: <root>/g3poses-result.json, <root>/<light>/NN_<id>_<light>.png + manifest.json,
  <root>/sbs/<light>/NN_<id>_<light>.jpg, and the log (Windows: Player-<light>.log; phone: logcat-<light>.txt).
  <root> = artifacts/g3-poses/win/<ts>/ (Windows) or artifacts/gate3/poses/<serial>/<ts>/ (phone).
  Frames are evidence for the visual review, not a verdict.
  -Lighting dusk is refused in both modes (review P2-4): street lamps follow the player camera, not the pose camera.
#>
[CmdletBinding(DefaultParameterSetName = 'Phone')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'Phone')] [string]$Serial,
    # Windows player (D73): path to a Development Kamion.exe. Excludes -Serial / -Build / -Apk.
    [Parameter(Mandatory = $true, ParameterSetName = 'Exe')] [string]$Exe,
    [Parameter(ParameterSetName = 'Phone')] [switch]$Build,
    [Parameter(ParameterSetName = 'Phone')] [string]$Apk = '',
    # Default: High with -Exe (D74 "zalecany"), Low with -Serial (as before).
    [ValidateSet('Low', 'Medium', 'High', 'Ultra')] [string]$Tier = 'Low',
    # Phone: 30. Windows: passed only when given (player default otherwise).
    [int]$Fps = 30,
    # Windows: window size of the player (the frames are rendered off-screen at -Width, independent of the window).
    [Parameter(ParameterSetName = 'Exe')] [int]$ScreenWidth = 1600,
    [Parameter(ParameterSetName = 'Exe')] [int]$ScreenHeight = 900,
    # Windows: extra game arguments "key=value[,key=value]" -> "-key value" (e.g. g3pose_warmup_s=15).
    [Parameter(ParameterSetName = 'Exe')] [string]$Extra = '',
    # Editor pairs are rendered under overcast and clear (scripts/sbs-gate3.ps1 -Lighting overcast,clear).
    [ValidateSet('clear', 'overcast', 'lowsun', 'dusk')] [string[]]$Lighting = @('overcast', 'clear'),
    [string]$Only = '',
    [int]$Width = 1280,
    [string]$Region = 'bialystok-industrial-c',
    [string]$RefDir = '',
    [int]$TimeoutSeconds = 900,
    [Parameter(ParameterSetName = 'Phone')] [double]$MaxBatteryC = 40.0,   # WORKING_VALUE (ADR 0246): above it the phone throttles; frames are fine, timings not
    [switch]$SkipCompare,
    [Parameter(ParameterSetName = 'Phone')] [switch]$KeepOnDevice,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
$ts = Get-Timestamp
$exit = 0
$winMode = $PSCmdlet.ParameterSetName -eq 'Exe'
if ($winMode -and -not $PSBoundParameters.ContainsKey('Tier')) { $Tier = 'High' }
$winFps = if ($winMode -and $PSBoundParameters.ContainsKey('Fps')) { $Fps } else { 0 }

# ---------------------------------------------------------------- plan (no adb)
$poseFile = Join-Path $RepoRoot 'game/Assets/_Project/Gameplay/Resources/g3_poses.json'
$py = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } elseif (Get-Command python3 -ErrorAction SilentlyContinue) { 'python3' } else { $null }
if (-not $py) { Write-Host 'python not found (needed for scripts/g3_poses.py check)' -ForegroundColor Red; exit 2 }
& $py (Join-Path $PSScriptRoot 'g3_poses.py') check --region $Region
if ($LASTEXITCODE -ne 0) { Write-Host "pose file stale: python scripts/g3_poses.py export --region $Region, then rebuild the APK" -ForegroundColor Red; exit 2 }
$poseDoc = Get-Content $poseFile -Raw | ConvertFrom-Json
$listArgs = @((Join-Path $PSScriptRoot 'g3_poses.py'), 'list', '--region', $Region)
if ($Only) { $listArgs += @('--only', $Only) }
$planned = @((& $py @listArgs) | Where-Object { $_ })
if ($planned.Count -eq 0) { Write-Host "-Only '$Only' matches no pose" -ForegroundColor Red; exit 2 }
$Only = ($Only -replace '\s', '')
$lightings = @($Lighting | ForEach-Object { $_ -split ',' } | Where-Object { $_ } | Select-Object -Unique)
if ($lightings -contains 'dusk') {
    Write-Host '-Lighting dusk is not supported by the pose capture: street lamps and cab lighting follow the player camera, not the pose camera (ADR 0246). Use overcast / clear / lowsun.' -ForegroundColor Red
    exit 2
}

# Main checkout (worktrees): reference photos and artifacts live there, not in the worktree.
$mainRoot = $RepoRoot
try { $common = (& git -C $RepoRoot rev-parse --path-format=absolute --git-common-dir 2>$null); if ($common) { $mainRoot = Split-Path $common.Trim() -Parent } } catch { }
$magick = $null
if (-not $SkipCompare) {
    $mc = Get-Command magick -ErrorAction SilentlyContinue
    if ($mc) { $magick = $mc.Source }
    elseif (-not $IsWindows -and (Get-Command convert -ErrorAction SilentlyContinue)) { $magick = (Get-Command convert).Source }   # IM6; on Windows convert.exe is the FAT tool
}

function Resolve-RefPhoto($ref) {
    $cands = @()
    foreach ($rp in @($ref.comparison_photo, $ref.photo)) {
        if (-not $rp) { continue }
        $leaf = Split-Path $rp -Leaf
        if ($RefDir) { $cands += (Join-Path $RefDir $leaf) }
        $cands += (Join-Path $mainRoot $rp)
        if ($mainRoot -ne $RepoRoot) { $cands += (Join-Path $RepoRoot $rp) }
    }
    if ($RefDir -and $ref.source_id) { foreach ($ext in '.png', '.jpg', '.jpeg') { $cands += (Join-Path $RefDir "$($ref.source_id)$ext") } }
    foreach ($c in $cands) { if ($c -and (Test-Path -LiteralPath $c)) { return (Resolve-Path -LiteralPath $c).Path } }
    return $null
}

# Windows: the command line of one run, from the tested planner (scripts/g3_poses.py winargs).
function Get-WinPlan([string]$runId, [string]$light, [string]$outDir, [string]$logFile) {
    $wa = @((Join-Path $PSScriptRoot 'g3_poses.py'), 'winargs', '--region', $Region, '--run', $runId, '--lighting', $light, '--tier', $Tier,
        '--out-dir', $outDir, '--log', $logFile, '--width', "$Width", '--fps', "$winFps", '--screen-width', "$ScreenWidth", '--screen-height', "$ScreenHeight")
    if ($Only) { $wa += @('--only', $Only) }
    if ($Extra) { $wa += @('--extra', $Extra) }
    $json = (& $py @wa) -join "`n"
    if ($LASTEXITCODE -ne 0 -or -not $json) { return $null }
    return ($json | ConvertFrom-Json)
}

# Left = reference photo, right = player frame. $who: 'phone' / 'win'; $whoDesc goes into the caption.
function Invoke-SideBySide($run, [string]$light, [string]$local, $pngs, [string]$who, [string]$whoDesc) {
    $run.compare = [ordered]@{ composed = 0; missingReference = @(); tool = $magick }
    if ($SkipCompare) { $run.compare.status = 'skipped (-SkipCompare)'; return }
    if (-not $magick) {
        $run.compare.status = 'skipped: ImageMagick not found'
        Write-Host "   side-by-side SKIPPED: ImageMagick (magick) not found - install it (winget install ImageMagick.ImageMagick) and re-run with the same -Lighting, or compare by hand; the $who frames are kept." -ForegroundColor Yellow
        return
    }
    $sbsDir = Join-Path $outRoot "sbs/$light"
    New-Item -ItemType Directory -Force $sbsDir | Out-Null
    $manifest = if (Test-Path (Join-Path $local 'manifest.json')) { Get-Content (Join-Path $local 'manifest.json') -Raw | ConvertFrom-Json } else { $null }
    foreach ($f in $pngs) {
        $idx = [int]($f.Name -split '_')[0]
        $p = $poseDoc.poses | Where-Object { $_.index -eq $idx } | Select-Object -First 1
        if (-not $p) { continue }
        $refPath = Resolve-RefPhoto $p.reference
        if (-not $refPath) { $run.compare.missingReference += $p.id; continue }
        $shot = if ($manifest) { $manifest.shots | Where-Object { $_.index -eq $idx } | Select-Object -First 1 } else { $null }
        $h = if ($shot -and $shot.height) { [int]$shot.height } else { [int]$p.out_height }
        $r = $p.reference
        $cap = "LEFT photo, RIGHT {0}  |  {1}  |  photo: {2}, {3}, {4} ({5})  |  {6} {7} {8}" -f $who, $p.id, $r.author, $r.license, $r.captured_at, $r.page_url, $whoDesc, $Tier, $light
        $sbs = Join-Path $sbsDir ([IO.Path]::ChangeExtension($f.Name, '.jpg'))
        $imArgs = @('(', $refPath, '-auto-orient', '-resize', "x$h", ')', '(', $f.FullName, ')', '-background', '#202020', '-gravity', 'center', '+append',
            '-gravity', 'south', '-splice', '0x34', '-fill', '#e0e0e0', '-pointsize', '18', '-annotate', '+0+8', $cap, '-quality', '90', $sbs)
        & $magick @imArgs 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0 -and (Test-Path $sbs)) { $run.compare.composed++ } else { $result.warnings += "magick failed for $($p.id)" }
    }
    $run.compare.status = 'done'
    Write-Host ("   side-by-side: {0} composed -> {1}; reference missing for {2}" -f $run.compare.composed, $sbsDir, $run.compare.missingReference.Count)
    if ($run.compare.missingReference.Count) {
        # The frames are the evidence; a missing photo is reported (warning + result JSON), not a failed capture.
        Write-Host "   missing reference photos (pass -RefDir): $($run.compare.missingReference -join ', ')" -ForegroundColor Yellow
        $result.warnings += "$light : reference photo missing for $($run.compare.missingReference.Count) pose(s)"
    }
}

Write-Host "== g3-poses [$(if ($winMode) { 'WINDOWS player' } else { "phone $Serial (deferred, D73)" })]: $($planned.Count)/$($poseDoc.count) poses, tier $Tier, $(if ($winMode) { if ($winFps -gt 0) { "$winFps fps" } else { 'player default fps' } } else { "$Fps fps" }), lighting $($lightings -join ', '), width $Width, region $Region"
Write-Host "   pose file $poseFile (schema $($poseDoc.schema)); ImageMagick: $(if ($SkipCompare) { 'skipped (-SkipCompare)' } elseif ($magick) { $magick } else { 'NOT FOUND' })"
if ($DryRun) {
    $refFound = 0
    foreach ($line in $planned) {
        $idx = [int]($line -split "`t")[0]
        $p = $poseDoc.poses | Where-Object { $_.index -eq $idx }
        $rp = Resolve-RefPhoto $p.reference
        if ($rp) { $refFound++ }
        Write-Host ("   {0,2} {1,-32} {2}x{3}  ref: {4}" -f $p.index, $p.id, $p.out_width, $p.out_height, $(if ($rp) { $rp } else { 'NOT FOUND' }))
    }
    Write-Host "   reference photos found: $refFound/$($planned.Count)$(if (-not $RefDir) { ' (pass -RefDir <folder> if they are elsewhere)' })"
    if ($winMode) {
        $dryRoot = Join-Path $ArtifactsDir "g3-poses/win/$ts"
        Write-Host "   exe $Exe $(if (Test-Path -LiteralPath $Exe -PathType Leaf) { '(found)' } else { '(NOT FOUND - fine for -DryRun)' }); output $dryRoot"
        foreach ($light in $lightings) {
            $plan = Get-WinPlan "$ts-$light" $light (Join-Path $dryRoot $light) (Join-Path $dryRoot "Player-$light.log")
            if (-not $plan) { Write-Host "   cannot plan the $light run (see the message above)" -ForegroundColor Red; exit 2 }
            Write-Host "   would run [$light]: Kamion.exe $($plan.line)"
        }
        Write-Host "   would run $($lightings.Count) player process(es), one per lighting, timeout $TimeoutSeconds s each; no adb, no Unity"
        exit 0
    }
    Write-Host "   would $(if ($Build) { 'BUILD a Development APK and install it' } elseif ($Apk) { "INSTALL $Apk" } else { 'use the INSTALLED APK' }), then run $($lightings.Count) capture(s)"
    exit 0
}

# ---------------------------------------------------------------- WINDOWS player (-Exe; D73) - no adb, no Unity
if ($winMode) {
    if (-not (Test-Path -LiteralPath $Exe -PathType Leaf)) { Write-Host "-Exe not found: $Exe (build: pwsh scripts/build-windows.ps1 -Development)" -ForegroundColor Red; exit 2 }
    $exePath = (Resolve-Path -LiteralPath $Exe).Path
    $procName = [IO.Path]::GetFileNameWithoutExtension($exePath)
    if (Get-Process -Name $procName -ErrorAction SilentlyContinue) { Write-Host "$procName is already running - close it first (one player per capture)" -ForegroundColor Red; exit 2 }
    $outRoot = Join-Path $ArtifactsDir "g3-poses/win/$ts"
    New-Item -ItemType Directory -Force $outRoot | Out-Null
    $outRoot = (Resolve-Path -LiteralPath $outRoot).Path
    $buildJson = Join-Path (Split-Path $exePath -Parent) 'build.json'
    $buildInfo = if (Test-Path -LiteralPath $buildJson) { try { Get-Content -LiteralPath $buildJson -Raw | ConvertFrom-Json } catch { $null } } else { $null }
    $machine = if ($env:COMPUTERNAME) { $env:COMPUTERNAME } else { [Environment]::MachineName }
    $result = [ordered]@{
        schema = 'kamion/g3-poses-result/1'; timestamp = $ts; platform = 'windows'; machine = $machine; tier = $Tier; fps = $winFps; width = $Width
        screen = "${ScreenWidth}x${ScreenHeight}"; region = $Region; only = $Only; posesPlanned = $planned.Count; posesInFile = $poseDoc.count
        poseFileSha256 = (Get-FileHash -Algorithm SHA256 $poseFile).Hash.ToLower(); repoHead = (Get-GitShortSha)
        exe = [ordered]@{ path = $exePath; sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $exePath).Hash.ToLower()
            build = $(if ($buildInfo) { [ordered]@{ name = $buildInfo.name; sha = $buildInfo.sha; development = $buildInfo.development; worldHigh = $buildInfo.worldHigh } } else { $null }) }
        runs = @(); warnings = @(); valid = $false
    }
    function Save-Result { $result | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $outRoot 'g3poses-result.json') -Encoding utf8 }
    function Read-PlayerLog([string]$path) {
        # Unity keeps the log open for writing: read with sharing, never fail the wait loop on a busy file.
        try {
            $fs = [IO.File]::Open($path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
            try { $sr = [IO.StreamReader]::new($fs); return $sr.ReadToEnd() } finally { $fs.Dispose() }
        } catch { return '' }
    }
    if ($buildInfo -and $buildInfo.development -eq $false) { $result.warnings += 'build.json says this is not a Development player: the game refuses g3pose outside Development builds' }
    if ($buildInfo -and "$($buildInfo.sha)" -match 'dirty') { $result.warnings += 'player built from a dirty tree: frames are not gate evidence (rebuild from a clean commit)' }
    try {
        foreach ($light in $lightings) {
            $runId = "$ts-$light"
            $local = Join-Path $outRoot $light
            $logFile = Join-Path $outRoot "Player-$light.log"
            $run = [ordered]@{ lighting = $light; runId = $runId; status = 'NOT_STARTED'; playerLog = $logFile }
            $result.runs += $run
            $plan = Get-WinPlan $runId $light $local $logFile
            if (-not $plan) { $run.status = 'PLAN_ERROR'; $exit = 2; break }
            $run.arguments = @($plan.args)
            Remove-Item $local -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item $logFile -Force -ErrorAction SilentlyContinue
            Write-Host "-- $light : $exePath $($plan.line)"
            $p = Start-Process -FilePath $exePath -ArgumentList $plan.line -PassThru
            $null = $p.Handle   # keeps ExitCode readable after the process is gone
            $t0 = Get-Date; $lastShots = -1; $doneAt = $null; $timedOut = $false; $killed = $false
            $doneRx = '\[G3POSE\] (DONE run=' + [regex]::Escape($runId) + ' |REFUSED)'
            while (-not $p.HasExited) {
                Start-Sleep -Seconds 2
                $elapsed = ((Get-Date) - $t0).TotalSeconds
                $log = Read-PlayerLog $logFile
                $shots = ([regex]::Matches($log, '\[G3POSE\] SHOT ')).Count
                if ($shots -ne $lastShots) { Write-Host ("   {0,4:F0} s: {1} frame(s)" -f $elapsed, $shots); $lastShots = $shots }
                if (-not $doneAt -and $log -match $doneRx) { $doneAt = Get-Date }
                # After DONE the player quits by itself (g3pose_quit); a player that stays open is closed here, frames are on disk.
                if ($doneAt -and ((Get-Date) - $doneAt).TotalSeconds -gt 20) { if (-not $p.HasExited) { $p.Kill(); $killed = $true }; break }
                if (-not $doneAt -and $elapsed -gt $TimeoutSeconds) { $timedOut = $true; if (-not $p.HasExited) { $p.Kill() }; break }
            }
            $p.WaitForExit()
            $run.seconds = [Math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
            $run.playerExitCode = if ($timedOut -or $killed) { $null } else { $p.ExitCode }
            if ($killed) { $result.warnings += "$light : the player did not quit after DONE and was closed by the script" }
            $va = @((Join-Path $PSScriptRoot 'g3_poses.py'), 'verify', '--region', $Region, '--dir', $local, '--log', $logFile, '--run', $runId, '--lighting', $light)
            if ($Only) { $va += @('--only', $Only) }
            if ($timedOut) { $va += '--timed-out' }
            if ($null -ne $run.playerExitCode) { $va += @('--exit-code', "$($run.playerExitCode)") }
            $vjson = (& $py @va) -join "`n"
            $v = if ($vjson) { $vjson | ConvertFrom-Json } else { $null }
            if (-not $v) { $run.status = 'VERIFY_ERROR'; $exit = 6; Write-Host "   run $light : scripts/g3_poses.py verify produced no verdict" -ForegroundColor Red; continue }
            $run.pngs = $v.pngs; $run.missing = @($v.missing); $run.unexpected = @($v.unexpected); $run.duplicateFrames = @($v.duplicateFrames)
            $run.settleTimeouts = $v.settleTimeouts; $run.problems = @($v.problems)
            $run.bootLine = $v.log.bootLine; $run.captureLine = $v.log.captureLine; $run.refused = $v.log.refused
            $run.failLines = @($v.log.failLines); $run.suspiciousLines = @($v.log.suspiciousLines)
            if ($v.log.done) { $run.captured = $v.log.done.captured; $run.failed = $v.log.done.failed }
            if ($v.log.unknownLighting) { $result.warnings += "lighting preset '$light' unknown to the game" }
            $run.status = if ($timedOut) { 'TIMEOUT' } elseif ($v.log.refused) { 'REFUSED_BY_GAME' } elseif (-not $v.log.done) { 'APP_DIED' } elseif ($v.ok) { 'DONE' } else { 'INCOMPLETE' }
            Write-Host ("   {0}: {1}, {2}/{3} PNG -> {4} ({5:F0} s, log {6})" -f $light, $run.status, $v.pngs, $v.planned, $local, $run.seconds, $logFile)
            if (-not $v.ok) {
                $exit = 6
                foreach ($pr in $v.problems) { Write-Host "   PROBLEM: $pr" -ForegroundColor Red }
            }
            if ($v.settleTimeouts -gt 0) { $result.warnings += "$light : $($v.settleTimeouts) frame(s) captured after the settle timeout (streaming not quiet)" }
            if ($run.status -eq 'REFUSED_BY_GAME') { break }   # not a Development player: the other presets would be refused too
            $pngs = @(Get-ChildItem $local -Filter *.png -ErrorAction SilentlyContinue | Sort-Object Name)
            if ($pngs.Count -gt 0) { Invoke-SideBySide $run $light $local $pngs 'win' "win $machine" }
        }
        $okRuns = @($result.runs | Where-Object { $_.status -eq 'DONE' })
        $result.valid = ($exit -eq 0 -and $okRuns.Count -eq $lightings.Count -and -not ($buildInfo -and "$($buildInfo.sha)" -match 'dirty'))
    }
    finally { Save-Result }
    foreach ($w in $result.warnings) { Write-Host "WARNING: $w" -ForegroundColor Yellow }
    Write-Host "result $(Join-Path $outRoot 'g3poses-result.json'): valid=$($result.valid), exit $exit"
    exit $exit
}

# ---------------------------------------------------------------- device + lock gate
if (-not (Test-Path $Adb)) { Write-Host "adb not found: $Adb" -ForegroundColor Red; exit 2 }
if ((Get-AdbDevices) -notcontains $Serial) { Write-Host "device $Serial not attached" -ForegroundColor Red; exit 2 }
if ((Test-UnityProjectLocked) -and -not $Build) { Write-Host 'WARNING: Unity is open on game/ - it restarts the adb daemon and can drop the phone mid-run.' -ForegroundColor Yellow }

function Assert-PhoneReady([string]$when) {
    # Test-DeviceUnlocked sends KEYCODE_WAKEUP (never SLEEP/POWER) and reads isKeyguardShowing.
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
function Get-BatteryC {
    $b = (& $Adb -s $Serial shell dumpsys battery) | Select-String '^\s*temperature:\s*(\d+)' | Select-Object -First 1
    if ($b) { return [double]$b.Matches[0].Groups[1].Value / 10 } else { return $null }
}
function Get-ThermalStatus {
    $t = (& $Adb -s $Serial shell dumpsys thermalservice) | Select-String 'Thermal Status:\s*(\d+)' | Select-Object -First 1
    if ($t) { return [int]$t.Matches[0].Groups[1].Value } else { return $null }
}

$outRoot = Join-Path $ArtifactsDir "gate3/poses/$Serial/$ts"
New-Item -ItemType Directory -Force $outRoot | Out-Null
$lockDir = Join-Path $ArtifactsDir 'locks'
$phoneLock = Join-Path $lockDir 'PHONE_RUN'
$ownLock = $false
$result = [ordered]@{
    schema = 'kamion/g3-poses-result/1'; timestamp = $ts; serial = $Serial; tier = $Tier; fps = $Fps; width = $Width
    region = $Region; only = $Only; posesPlanned = $planned.Count; posesInFile = $poseDoc.count
    poseFileSha256 = (Get-FileHash -Algorithm SHA256 $poseFile).Hash.ToLower(); repoHead = (Get-GitShortSha)
    apk = $null; device = [ordered]@{}; runs = @(); warnings = @(); valid = $false
}
function Save-Result { $result | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $outRoot 'g3poses-result.json') -Encoding utf8 }

try {
    if (Test-Path $phoneLock) { Write-Host "WARNING: $phoneLock exists (another phone run?) - continuing; remove it when stale." -ForegroundColor Yellow }
    else { New-Item -ItemType Directory -Force $lockDir | Out-Null; Set-Content $phoneLock "g3-poses $ts $Serial" ; $ownLock = $true }

    foreach ($p in 'ro.product.model', 'ro.product.manufacturer', 'ro.soc.model', 'ro.build.version.release', 'ro.hardware.egl') {
        $result.device[$p] = (& $Adb -s $Serial shell getprop $p).Trim()
    }
    if (-not (Assert-PhoneReady 'before install')) { $result.rejected = 'keyguard before install'; Save-Result; exit 5 }

    # ------------------------------------------------------------ build / install (build-android.ps1)
    if ($Build -or $Apk) {
        $baArgs = @('-NoProfile', '-File', (Join-Path $PSScriptRoot 'build-android.ps1'), '-Install', '-Serial', $Serial, '-Development')
        if (-not $Build) {
            if (-not (Test-Path $Apk)) { Write-Host "-Apk not found: $Apk" -ForegroundColor Red; exit 2 }
            $Apk = (Resolve-Path $Apk).Path
            $baArgs += @('-SkipBuild', '-Apk', $Apk)
        }
        & pwsh @baArgs
        if ($LASTEXITCODE -ne 0) { Write-Host "build/install failed (exit $LASTEXITCODE)" -ForegroundColor Red; $result.rejected = "build-android exit $LASTEXITCODE"; Save-Result; exit 4 }
        if ($Build) {
            $Apk = (Get-ChildItem (Join-Path $ArtifactsDir 'apk') -Filter '*-dev.apk' | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
        }
        if ($Apk -and (Test-Path $Apk)) {
            $meta = (& $py (Join-Path $PSScriptRoot 'gate3_meta.py') apk --apk $Apk --repo $RepoRoot) -join "`n" | ConvertFrom-Json
            $result.apk = [ordered]@{ path = $Apk; file = $meta.apkFile; sha256 = $meta.apkSha256; builtFromSha = $meta.gitSha; dirty = $meta.dirty; dev = $meta.dev; high = $meta.high }
            if (-not $meta.dev) { $result.warnings += 'APK is not a -dev build: the game refuses g3pose outside Development builds' }
            Write-Host "APK $($meta.apkFile) sha256 $($meta.apkSha256) built from $($meta.gitSha)$(if ($meta.dirty) { ' (DIRTY)' })"
        }
    } else {
        $result.apk = [ordered]@{ path = $null; note = 'installed APK used (no -Build / -Apk); identity from the [BOOT] logcat line' }
    }
    $component = (& $Adb -s $Serial shell cmd package resolve-activity --brief $PackageName | Select-Object -Last 1).Trim()
    if (-not $component -or $component -notmatch '/') { Write-Host "$PackageName not installed on $Serial (component '$component')" -ForegroundColor Red; exit 4 }

    # ------------------------------------------------------------ one capture run per lighting preset
    $remoteBase = "/sdcard/Android/data/$PackageName/files/g3poses"
    foreach ($light in $lightings) {
        $runId = "$ts-$light"
        $run = [ordered]@{ lighting = $light; runId = $runId; status = 'NOT_STARTED' }
        $result.runs += $run
        if (-not (Assert-PhoneReady "before run $light")) { $run.status = 'REJECTED_LOCKED'; $exit = 5; break }
        $battC = Get-BatteryC
        $run.batteryBeforeC = $battC; $run.thermalBefore = Get-ThermalStatus
        if ($null -ne $battC -and $battC -gt $MaxBatteryC) {
            Write-Host "REFUSED: battery $battC C > $MaxBatteryC C - let $Serial cool down and run again." -ForegroundColor Red
            $run.status = 'REFUSED_HOT'; $exit = 7; break
        }
        & $Adb -s $Serial shell am force-stop $PackageName | Out-Null
        & $Adb -s $Serial shell rm -rf "$remoteBase/$runId" | Out-Null
        & $Adb -s $Serial logcat -c
        $startArgs = @('shell', 'am', 'start', '-n', $component, '-e', 'scene', 'WorldC', '-e', 'tier', $Tier, '-e', 'fps', "$Fps",
            '-e', 'g3pose', '1', '-e', 'g3pose_run', $runId, '-e', 'g3pose_width', "$Width", '-e', 'lighting', $light)
        if ($Only) { $startArgs += @('-e', 'g3pose_only', $Only) }
        & $Adb -s $Serial @startArgs | Out-Null
        Write-Host "-- $light : launched $component (run $runId), waiting for [G3POSE] DONE (timeout $TimeoutSeconds s)"
        $t0 = Get-Date; $done = $null; $log = ''; $locked = $false; $died = $false; $lastShots = -1
        while (((Get-Date) - $t0).TotalSeconds -lt $TimeoutSeconds) {
            Start-Sleep -Seconds 5
            $log = (& $Adb -s $Serial logcat -d -v threadtime -s Unity:V AndroidRuntime:E DEBUG:E libc:F) -join "`n"
            $done = [regex]::Match($log, '\[G3POSE\] DONE run=' + [regex]::Escape($runId) + ' captured=(\d+) failed=(\d+) timeout=(\d+) dir=(\S+)')
            if ($done.Success) { break }
            $refused = [regex]::Match($log, '\[G3POSE\] REFUSED[^\r\n]*')
            if ($refused.Success) { $run.refused = $refused.Value; break }
            $shots = ([regex]::Matches($log, '\[G3POSE\] SHOT ')).Count
            if ($shots -ne $lastShots) { Write-Host ("   {0,4:F0} s: {1} frame(s)" -f ((Get-Date) - $t0).TotalSeconds, $shots); $lastShots = $shots }
            if (-not (Assert-PhoneReady "during run $light")) { $locked = $true; break }
            $appPid = (& $Adb -s $Serial shell pidof $PackageName 2>$null)
            if (-not $appPid -and ((Get-Date) - $t0).TotalSeconds -gt 20) { $died = $true; break }
        }
        $log = (& $Adb -s $Serial logcat -d -v threadtime -s Unity:V AndroidRuntime:E DEBUG:E libc:F) -join "`n"
        $logFile = Join-Path $outRoot "logcat-$light.txt"
        Set-Content $logFile $log -Encoding utf8
        $run.logcat = $logFile
        $run.batteryAfterC = Get-BatteryC; $run.thermalAfter = Get-ThermalStatus
        $boot = [regex]::Match($log, '\[BOOT\] Kamion [^\r\n]*'); if ($boot.Success) { $run.bootLine = $boot.Value }
        $g3b = [regex]::Match($log, '\[G3POSE\] build=[^\r\n]*'); if ($g3b.Success) { $run.captureLine = $g3b.Value }
        if ($log -match 'lighting=\S+: no such preset') { $result.warnings += "lighting preset '$light' unknown to the game" }
        $run.suspiciousLines = @([regex]::Matches($log, '[^\r\n]*(FATAL EXCEPTION|signal \d+ \(SIG|ANR in)[^\r\n]*') | ForEach-Object Value)
        $run.failLines = @([regex]::Matches($log, '\[G3POSE\] FAIL [^\r\n]*') | ForEach-Object Value)
        if (-not $done.Success) { $done = [regex]::Match($log, '\[G3POSE\] DONE run=' + [regex]::Escape($runId) + ' captured=(\d+) failed=(\d+) timeout=(\d+) dir=(\S+)') }
        $lockedAfter = -not (Assert-PhoneReady "after run $light")
        if ($locked -or $lockedAfter) { $run.status = 'REJECTED_LOCKED'; $exit = 5; Write-Host "   run $light REJECTED: keyguard showed" -ForegroundColor Red; break }
        if ($run.refused) { $run.status = 'REFUSED_BY_GAME'; $exit = 6; Write-Host "   $($run.refused)" -ForegroundColor Red; break }
        if (-not $done.Success) {
            $run.status = $(if ($died) { 'APP_DIED' } else { 'TIMEOUT' }); $exit = 6
            Write-Host "   run $light : no DONE marker ($($run.status)); see $logFile" -ForegroundColor Red
            continue
        }
        $run.captured = [int]$done.Groups[1].Value; $run.failed = [int]$done.Groups[2].Value; $run.settleTimeouts = [int]$done.Groups[3].Value
        $run.status = 'DONE'

        # ---------------------------------------------------- pull
        $local = Join-Path $outRoot $light
        Remove-Item $local -Recurse -Force -ErrorAction SilentlyContinue
        & $Adb -s $Serial pull "$remoteBase/$runId" $outRoot 2>&1 | Out-Null
        $pulled = Join-Path $outRoot $runId
        if (Test-Path $pulled) { Rename-Item $pulled $light }
        if (-not $KeepOnDevice) { & $Adb -s $Serial shell rm -rf "$remoteBase/$runId" | Out-Null }
        $pngs = @(Get-ChildItem $local -Filter *.png -ErrorAction SilentlyContinue | Sort-Object Name)
        $run.pngs = $pngs.Count
        $md5 = @{}; $dups = @()
        foreach ($f in $pngs) {
            $h = (Get-FileHash -Algorithm MD5 $f.FullName).Hash.ToLower()
            if ($md5.ContainsKey($h)) { $dups += "$($f.Name) == $($md5[$h])" } else { $md5[$h] = $f.Name }
        }
        $run.duplicateFrames = $dups
        Write-Host ("   {0}: captured {1}, failed {2}, settle timeouts {3}, pulled {4} PNG -> {5}" -f $light, $run.captured, $run.failed, $run.settleTimeouts, $pngs.Count, $local)
        if ($run.failed -gt 0 -or $run.captured -ne $planned.Count -or $pngs.Count -ne $run.captured -or $dups.Count -gt 0) {
            $exit = 6
            if ($dups.Count) { Write-Host "   DUPLICATE frames (not evidence of distinct poses): $($dups -join '; ')" -ForegroundColor Red }
            if ($pngs.Count -ne $run.captured) { Write-Host "   pulled $($pngs.Count) PNG but the game reported $($run.captured)" -ForegroundColor Red }
        }
        if ($run.settleTimeouts -gt 0) { $result.warnings += "$light : $($run.settleTimeouts) frame(s) captured after the settle timeout (streaming not quiet)" }

        # ---------------------------------------------------- side by side with the reference photo
        Invoke-SideBySide $run $light $local $pngs 'phone' "phone $Serial"
    }
    $okRuns = @($result.runs | Where-Object { $_.status -eq 'DONE' -and $_.failed -eq 0 -and $_.captured -eq $planned.Count -and $_.pngs -eq $_.captured -and $_.duplicateFrames.Count -eq 0 })
    $result.valid = ($exit -eq 0 -and $okRuns.Count -eq $lightings.Count -and -not ($result.apk -and $result.apk.dirty))
    if ($result.apk -and $result.apk.dirty) { $result.warnings += 'APK is -dirty: frames are not gate evidence (rebuild from a clean commit)' }
}
finally {
    if ($ownLock) { Remove-Item $phoneLock -ErrorAction SilentlyContinue }
    Save-Result
}
foreach ($w in $result.warnings) { Write-Host "WARNING: $w" -ForegroundColor Yellow }
Write-Host "result $(Join-Path $outRoot 'g3poses-result.json'): valid=$($result.valid), exit $exit"
exit $exit
