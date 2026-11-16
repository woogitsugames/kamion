<#
.SYNOPSIS
  Build the Windows x64 player in Unity batchmode (ADR 0260 / 0261) and optionally run it.
.EXAMPLE
  pwsh scripts/build-windows.ps1                                           # Boot + DrivingLab + WorldC (+ High content)
  pwsh scripts/build-windows.ps1 -Regions 'd67,knyszyn-w,dk65-monki-01'     # + region scenes (ADR 0229)
  pwsh scripts/build-windows.ps1 -RegionsFile Data/build_regions.json [-RegionsAllowMissing]
  pwsh scripts/build-windows.ps1 -SkipBuild -Run -Scene knyszyn-w -Autopilot route -Speed 50 -Fps 1000 -RunSeconds 90 -ShotSeconds 45
  pwsh scripts/build-windows.ps1 -Slot -Regions d67-full -Package [-PackageArgs '--allow-dirty']   # + tester zip (ADR 0271)
.NOTES
  Exit code 0 = everything requested succeeded. Build log: artifacts/logs/build-win-<ts>.log.
  Output: artifacts/win/kamion-<version>-<sha>[-low][-regions][-dev]/Kamion.exe + Kamion.exe.sha256 + build.json
  (file count, total size, content hash, region ids) + build-id.json + launchers (windowed; the project default is fullscreen).
  ADR 0276 (scripts/postbuild-windows.py, needs Python 3.10+ via uv / python): Kamion.exe is the same Unity stub in every
  build, so its sha256 does not identify a build; contentHash = 12 hex digits of the sha256 manifest of Kamion_Data,
  written to build-id.json next to the exe (outside the hashed folder) and shown by the player (menu, "Informacje",
  [BOOT] log). Launchers: Kamion-okno.cmd (menu) + Kamion-<region>.cmd (-scene <region>) for every region whose scene is
  in the build (after the expansion of -Regions sets / aliases / ranges, read from the build log).
  Burst debug symbols (*_DoNotShip) are moved to artifacts/win/symbols/<name>/ (crash analysis), not deleted.
  PC content: High world scenes and High vehicle material sets ship unless -WorldLow.
  -Slot takes a machine-wide Unity slot (scripts/unity-slot.ps1, waits for PHONE_RUN) and releases it afterwards.
  The first run in a checkout whose Library was imported for Android re-imports every asset for Win64 (long).
  -Run: starts the player windowed with -logFile, waits for it to quit (quit_t), prints the [BOOT]/[START]/[DIAG] lines;
  player log artifacts/logs/win-run-<ts>.log, screenshot artifacts/win/runs/<ts>/shot.png. No adb, no phone.
#>
param(
    [switch]$Development,
    [switch]$WorldLow,
    [string[]]$ExtraUnityArgs = @(),
    [switch]$SkipBuild,
    [string]$Exe = '',            # with -SkipBuild: run exactly this Kamion.exe (default: the one this commit would build)
    [string[]]$Regions = @(),     # ADR 0229
    [string]$RegionsFile = '',
    [switch]$RegionsAllowMissing,
    [switch]$Slot,
    [switch]$Package,             # ADR 0271/0276: scripts/package-windows.py on the build folder (zip for testers)
    [string[]]$PackageArgs = @(), # e.g. '--allow-dirty', '--dry-run' 
    [string]$SlotOwner = 'build-windows',
    [switch]$Run,
    [ValidateSet('', 'Low', 'Medium', 'High', 'Ultra')] [string]$Tier = '',
    [int]$Fps = 0,                # 0 = player default (60); 1000 = effectively uncapped (measurement)
    [string]$Scene = '',          # region id / alias / scene name, e.g. knyszyn-w
    [string]$Autopilot = '',      # route = follow the region start route
    [string]$Speed = '',
    [int]$Width = 1600,
    [int]$Height = 900,
    [int]$RunSeconds = 60,
    [int]$ShotSeconds = 30,
    [string[]]$ExtraPlayerArgs = @()
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
$ts = Get-Timestamp
$winDir = Join-Path $ArtifactsDir 'win'
New-Item -ItemType Directory -Force $LogsDir, $winDir | Out-Null

$exeArg = $Exe
$version = (Select-String -Path "$ProjectPath/ProjectSettings/ProjectSettings.asset" -Pattern '^\s*bundleVersion:\s*(.+)$').Matches[0].Groups[1].Value.Trim()
$sha = Get-GitShortSha
if (& git -C $RepoRoot status --porcelain --untracked-files=no) { $sha = "$sha-dirty" }
# "-Regions a,b" binds as an array. Spaces, NBSP and semicolons are separators too (ADR 0229 par. 2, review #129 P2-1: the
# same normalisation as build-android.ps1); -Regions given but empty is an error before Unity starts.
$regionSpec = ((((@($Regions) | Where-Object { $_ }) -join ',') -replace '[\s\u00A0;]+', ',') -replace ',{2,}', ',').Trim(',')
if ($PSBoundParameters.ContainsKey('Regions') -and -not $regionSpec) { throw "-Regions given but empty after normalisation ('$($Regions -join ',')')" }
if ($RegionsFile) {
    # Relative to the current directory first, then to the repo root; Unity gets an absolute path (it runs elsewhere).
    $rf = @($RegionsFile, (Join-Path $RepoRoot $RegionsFile)) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    if (-not $rf) { throw "-RegionsFile not found: $RegionsFile (current directory $(Get-Location), repo root $RepoRoot)" }
    $RegionsFile = (Resolve-Path -LiteralPath $rf).Path
}

# Python for the post-build step (ADR 0276): uv (doctor.ps1 checks it), else python / python3 / py -3.
function Invoke-RepoPython([string[]]$PyArgs) {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        $out = & uv run --no-project python @PyArgs
        return @{ Code = $LASTEXITCODE; Out = $out }
    }
    foreach ($c in @(@('python'), @('python3'), @('py', '-3'))) {
        if (Get-Command $c[0] -ErrorAction SilentlyContinue) {
            $pre = @($c | Select-Object -Skip 1)
            $out = & $c[0] @pre @PyArgs
            return @{ Code = $LASTEXITCODE; Out = $out }
        }
    }
    return @{ Code = 127; Out = $null }
}
$name = "kamion-$version-$sha$(if ($WorldLow) { '-low' })$(if ($regionSpec -or $RegionsFile) { '-regions' })$(if ($Development) { '-dev' })"
$outDir = Join-Path $winDir $name
$exePath = Join-Path $outDir 'Kamion.exe'

# ---------------------------------------------------------------- build
if (-not $SkipBuild) {
    $audioManifest = Join-Path $RepoRoot 'art-source/audio/generated/manifest.json'
    if (-not (Test-Path $audioManifest)) {
        if (Get-Command uv -ErrorAction SilentlyContinue) {
            Write-Host 'audio: art-source/audio/generated missing -> uv run python render_all.py'
            Push-Location (Join-Path $RepoRoot 'tools/audio')
            try { & uv run python render_all.py --no-previews 2>&1 | Out-File (Join-Path $LogsDir "audio-render-$ts.log") -Encoding utf8 }
            finally { Pop-Location }
            if (-not (Test-Path $audioManifest)) { Write-Warning "audio render failed (log artifacts/logs/audio-render-$ts.log) - the player will be silent" }
        } else { Write-Warning 'uv not found: cannot render vehicle audio - the player will be silent' }
    }
    $log = Join-Path $LogsDir "build-win-$ts.log"
    $unityArgs = @('-executeMethod', 'Game.Editor.Build.BuildCommands.BuildWindowsPlayer', '-buildOutput', $exePath)
    if ($Development) { $unityArgs += '-development' }
    if ($WorldLow) { $unityArgs += '-worldLow' }
    if ($regionSpec) { $unityArgs += @('-regions', $regionSpec) }
    if ($RegionsFile) { $unityArgs += @('-regionsFile', $RegionsFile) }
    if ($RegionsAllowMissing) { $unityArgs += '-regionsAllowMissing' }
    if ($ExtraUnityArgs) { $unityArgs += $ExtraUnityArgs }
    if (Test-Path $outDir) { Remove-Item $outDir -Recurse -Force }   # a stale *_Data folder would be merged into the new player
    $sw = [Diagnostics.Stopwatch]::StartNew()
    if ($Slot) { & pwsh -NoProfile -File "$PSScriptRoot/unity-slot.ps1" -Acquire -Pool unity -Owner $SlotOwner | Out-Host }
    try { $code = Invoke-UnityBatch -LogFile $log -Arguments $unityArgs -BuildTarget 'Win64' }
    finally { if ($Slot) { & pwsh -NoProfile -File "$PSScriptRoot/unity-slot.ps1" -Release -Pool unity -Owner $SlotOwner | Out-Host } }
    $result = Select-String -Path $log -Pattern 'BUILD_RESULT:.*' -ErrorAction SilentlyContinue | Select-Object -Last 1
    if ($code -ne 0 -or -not $result -or $result.Line -notmatch 'BUILD_RESULT: Succeeded' -or -not (Test-Path $exePath)) {
        Write-Host "BUILD FAILED (exit $code) after $([int]$sw.Elapsed.TotalSeconds)s, log: $log" -ForegroundColor Red
        if ($result) { Write-Host $result.Line -ForegroundColor Red }
        Show-UnityLogErrors $log
        exit ([Math]::Max(1, $code))
    }
    # Not part of the player: debug symbols of the Burst / IL2CPP step (Unity writes them next to the exe). Kept per build
    # for crash analysis (ADR 0271 proposal), outside the player folder so package-windows.py never sees them.
    $symDir = Join-Path $winDir "symbols/$name"
    foreach ($d in @(Get-ChildItem $outDir -Directory -Filter '*_DoNotShip')) {
        New-Item -ItemType Directory -Force $symDir | Out-Null
        $dst = Join-Path $symDir $d.Name
        if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
        Move-Item -LiteralPath $d.FullName -Destination $dst
    }
    # Kamion.exe is the Unity launcher stub: the same sha256 in every build (kept for completeness, not an identity).
    $hash = (Get-FileHash -Algorithm SHA256 $exePath).Hash.ToLower()
    "$hash  Kamion.exe" | Set-Content "$exePath.sha256" -Encoding ascii
    # ADR 0276: content hash of Kamion_Data -> build-id.json (read by the player) + windowed launchers per region
    # (Kamion-okno.cmd + Kamion-<region>.cmd; ProjectSettings default is fullscreen, not changed here, ADR 0261).
    $post = Invoke-RepoPython @("$RepoRoot/scripts/postbuild-windows.py", $outDir, '--log', $log, '--git-sha', $sha)
    $pbLine = @($post.Out) | Where-Object { "$_" -match '^\{' } | Select-Object -Last 1
    if ($post.Code -ne 0 -or -not $pbLine) {
        Write-Host "POSTBUILD FAILED (exit $($post.Code)): scripts/postbuild-windows.py - the player is built but has no content hash / launchers" -ForegroundColor Red
        exit 5
    }
    $pb = $pbLine | ConvertFrom-Json
    $files = @(Get-ChildItem $outDir -Recurse -File)
    $bytes = ($files | Measure-Object Length -Sum).Sum
    [ordered]@{
        name = $name; version = $version; sha = $sha; exe = $exePath; exeSha256 = $hash
        contentHash = $pb.contentHash; contentSha256 = $pb.contentSha256; contentFiles = $pb.contentFiles; contentBytes = $pb.contentBytes
        files = $files.Count; totalBytes = $bytes; totalMB = [Math]::Round($bytes / 1MB, 1)
        regions = $regionSpec; regionsFile = $RegionsFile; regionIds = @($pb.regionIds); launchers = @($pb.launchers)
        worldHigh = (-not $WorldLow); development = [bool]$Development
        buildSeconds = [int]$sw.Elapsed.TotalSeconds; log = $log; result = $result.Line
    } | ConvertTo-Json | Set-Content (Join-Path $outDir 'build.json') -Encoding utf8
    Write-Host $result.Line
    Write-Host ("EXE    {0} (folder {1:N1} MB, {2} files) in {3}s" -f $exePath, ($bytes / 1MB), $files.Count, [int]$sw.Elapsed.TotalSeconds)
    Write-Host "CONTENT $($pb.contentHash) (Kamion_Data, $($pb.contentFiles) files; Kamion.exe sha256 $hash is the Unity stub, same in every build)"
    Write-Host "RUN    $(@($pb.launchers) -join ', ')"
    if (@($pb.skippedRegionIds).Count) { Write-Warning "no launcher for region id(s): $(@($pb.skippedRegionIds) -join ', ')" }
    Write-Host "log    $log"
} elseif ($exeArg) {
    if (-not (Test-Path $exeArg)) { throw "-Exe not found: $exeArg" }
    $exePath = (Resolve-Path $exeArg).Path
}

if ($Package) {
    if (-not (Test-Path $exePath)) { throw "-Package: no player at $exePath" }
    $pkg = Invoke-RepoPython (@("$RepoRoot/scripts/package-windows.py", (Split-Path $exePath -Parent)) + $PackageArgs)
    @($pkg.Out) | ForEach-Object { Write-Host $_ }
    if ($pkg.Code -ne 0) { Write-Host "PACKAGE FAILED (exit $($pkg.Code))" -ForegroundColor Red; exit 6 }
}

if (-not $Run) { exit 0 }

# ---------------------------------------------------------------- run (windowed, timed, screenshot)
if (-not (Test-Path $exePath)) { throw "no player at $exePath (build first or pass -Exe)" }
$runDir = Join-Path $winDir "runs/$ts"
New-Item -ItemType Directory -Force $runDir | Out-Null
$playerLog = Join-Path $LogsDir "win-run-$ts.log"
$shot = Join-Path $runDir 'shot.png'
$playerArgs = @('-screen-fullscreen', '0', '-screen-width', "$Width", '-screen-height', "$Height", '-logFile', $playerLog,
    '-shot', $shot, '-shot_t', "$ShotSeconds", '-quit_t', "$RunSeconds")
if ($Tier) { $playerArgs += @('-tier', $Tier) }
if ($Fps -gt 0) { $playerArgs += @('-fps', "$Fps") }
if ($Scene) { $playerArgs += @('-scene', $Scene) }
if ($Autopilot) { $playerArgs += @('-autopilot', $Autopilot) }
if ($Speed) { $playerArgs += @('-speed', $Speed) }
if ($ExtraPlayerArgs) { $playerArgs += $ExtraPlayerArgs }
Write-Host "run: $exePath $($playerArgs -join ' ')"
$p = Start-Process -FilePath $exePath -ArgumentList $playerArgs -PassThru
$null = $p.Handle
if (-not $p.WaitForExit(($RunSeconds + 120) * 1000)) {
    Write-Host "player did not quit within $($RunSeconds + 120) s - killed" -ForegroundColor Red
    $p.Kill(); $p.WaitForExit(); $hung = $true
}
Copy-Item $playerLog (Join-Path $runDir 'player.log') -ErrorAction SilentlyContinue
$diagDir = Join-Path $env:USERPROFILE 'AppData\LocalLow'
$summary = Get-ChildItem $diagDir -Recurse -Filter summary.json -ErrorAction SilentlyContinue |
    Where-Object { $_.DirectoryName -match 'diag$' -and $_.LastWriteTime -gt (Get-Date).AddSeconds(-($RunSeconds + 300)) } |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($summary) {
    Copy-Item $summary.FullName (Join-Path $runDir 'summary.json')
    Copy-Item (Join-Path $summary.DirectoryName 'frametimes.csv') (Join-Path $runDir 'frametimes.csv') -ErrorAction SilentlyContinue
}
Select-String -Path $playerLog -Pattern '^\[BOOT\] Kamion|\[START\] region|\[LAB\] DrivingLab ready|\[AUTOSHOT\] screenshot' -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  $($_.Line.Trim())" }
Select-String -Path $playerLog -Pattern '^\[DIAG\] t=' -ErrorAction SilentlyContinue | Select-Object -Last 3 | ForEach-Object { Write-Host "  $($_.Line.Trim())" }
$bad = Select-String -Path $playerLog -Pattern 'Exception|Crash!!!|NullReference|Shader error|ArgumentException' -ErrorAction SilentlyContinue
$exit = if ($hung) { -1 } else { $p.ExitCode }
if ($hung -or $exit -ne 0 -or $bad -or -not (Test-Path $shot)) {
    Write-Host "  PROBLEMS (exit=$exit, suspicious lines=$(@($bad).Count), screenshot=$(Test-Path $shot)) - see $playerLog" -ForegroundColor Red
    $bad | Select-Object -First 15 | ForEach-Object { Write-Host "    $($_.Line.Trim())" -ForegroundColor Red }
    exit 4
}
Write-Host "  OK: player quit with 0, no exceptions; screenshot $shot; log $playerLog; run dir $runDir"
exit 0
