<#
.SYNOPSIS
  Build the Windows x64 player in Unity batchmode (ADR 0260 / 0261) and optionally run it.
.EXAMPLE
  pwsh scripts/build-windows.ps1                                           # Boot + DrivingLab + WorldC (+ High content)
  pwsh scripts/build-windows.ps1 -Regions 'd67,knyszyn-w,dk65-monki-01'     # + region scenes (ADR 0229)
  pwsh scripts/build-windows.ps1 -RegionsFile Data/build_regions.json [-RegionsAllowMissing]
  pwsh scripts/build-windows.ps1 -SkipBuild -Run -Scene knyszyn-w -Autopilot route -Speed 50 -Fps 1000 -RunSeconds 90 -ShotSeconds 45
.NOTES
  Exit code 0 = everything requested succeeded. Build log: artifacts/logs/build-win-<ts>.log.
  Output: artifacts/win/kamion-<version>-<sha>[-low][-regions][-dev]/Kamion.exe + Kamion.exe.sha256 + build.json
  (file count, total size) + Kamion-okno.cmd / Kamion-knyszyn.cmd launchers (windowed; the project default is fullscreen).
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
$regionSpec = (@($Regions) | Where-Object { $_ }) -join ','
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
    # Not part of the player: debug symbols of the Burst / IL2CPP step (Unity writes them next to the exe).
    Get-ChildItem $outDir -Directory -Filter '*_DoNotShip' | Remove-Item -Recurse -Force
    $hash = (Get-FileHash -Algorithm SHA256 $exePath).Hash.ToLower()
    "$hash  Kamion.exe" | Set-Content "$exePath.sha256" -Encoding ascii
    # Windowed launchers: ProjectSettings default is fullscreen (not changed here, ADR 0261).
    "@echo off`r`nstart `"`" `"%~dp0Kamion.exe`" -screen-fullscreen 0 -screen-width 1600 -screen-height 900 %*`r`n" | Set-Content (Join-Path $outDir 'Kamion-okno.cmd') -Encoding ascii -NoNewline
    "@echo off`r`nstart `"`" `"%~dp0Kamion.exe`" -screen-fullscreen 0 -screen-width 1600 -screen-height 900 -scene knyszyn-w %*`r`n" | Set-Content (Join-Path $outDir 'Kamion-knyszyn.cmd') -Encoding ascii -NoNewline
    $files = @(Get-ChildItem $outDir -Recurse -File)
    $bytes = ($files | Measure-Object Length -Sum).Sum
    [ordered]@{
        name = $name; version = $version; sha = $sha; exe = $exePath; exeSha256 = $hash
        files = $files.Count; totalBytes = $bytes; totalMB = [Math]::Round($bytes / 1MB, 1)
        regions = $regionSpec; regionsFile = $RegionsFile; worldHigh = (-not $WorldLow); development = [bool]$Development
        buildSeconds = [int]$sw.Elapsed.TotalSeconds; log = $log; result = $result.Line
    } | ConvertTo-Json | Set-Content (Join-Path $outDir 'build.json') -Encoding utf8
    Write-Host $result.Line
    Write-Host ("EXE    {0} (folder {1:N1} MB, {2} files) in {3}s" -f $exePath, ($bytes / 1MB), $files.Count, [int]$sw.Elapsed.TotalSeconds)
    Write-Host "SHA256 $hash"
    Write-Host "log    $log"
} elseif ($exeArg) {
    if (-not (Test-Path $exeArg)) { throw "-Exe not found: $exeArg" }
    $exePath = (Resolve-Path $exeArg).Path
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
