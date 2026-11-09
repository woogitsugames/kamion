<#
.SYNOPSIS
  Build the Android APK in Unity batchmode and optionally install/run it on attached phones.
.EXAMPLE
  pwsh scripts/build-android.ps1                         # build only
  pwsh scripts/build-android.ps1 -Install -Run            # build, install on the single attached phone, launch, logcat
  pwsh scripts/build-android.ps1 -Install -AllDevices -Run -LogcatSeconds 60
  pwsh scripts/build-android.ps1 -SkipBuild -Install -Serial RFGL34SJYDZ -Run -Tier Low -Fps 60
.NOTES
  Exit code 0 = everything requested succeeded. Build log: artifacts/logs/build-<ts>.log.
  APK: artifacts/apk/kamion-<version>-<sha>.apk (+ .sha256). Missing devices are skipped with a warning.
  -Run fails (exit 4) if the Unity logcat contains exceptions / fatal errors.
#>
param(
    [switch]$Install,
    [string[]]$Serial,
    [switch]$AllDevices,
    [switch]$Run,
    [switch]$Development,
    [switch]$SkipBuild,
    [int]$LogcatSeconds = 20,
    [ValidateSet('', 'Low', 'Medium', 'High', 'Ultra')] [string]$Tier = '',
    [int]$Fps = 0
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
$ts = Get-Timestamp
New-Item -ItemType Directory -Force $LogsDir, (Join-Path $ArtifactsDir 'apk') | Out-Null

$version = (Select-String -Path "$ProjectPath/ProjectSettings/ProjectSettings.asset" -Pattern '^\s*bundleVersion:\s*(.+)$').Matches[0].Groups[1].Value.Trim()
$sha = Get-GitShortSha
if (& git -C $RepoRoot status --porcelain --untracked-files=no) { $sha = "$sha-dirty" }
$apk = Join-Path $ArtifactsDir "apk/kamion-$version-$sha$(if ($Development) { '-dev' }).apk"

# ---------------------------------------------------------------- build
if (-not $SkipBuild) {
    # Vehicle audio WAVs (~47 MB) are generated, not committed: render them when missing (needs uv, ~30 s).
    # Unity imports them into Assets/_Project/Audio/Generated (gitignored) at build time (VehicleAudioImporter).
    $audioManifest = Join-Path $RepoRoot 'art-source/audio/generated/manifest.json'
    if (-not (Test-Path $audioManifest)) {
        if (Get-Command uv -ErrorAction SilentlyContinue) {
            Write-Host 'audio: art-source/audio/generated missing -> uv run python render_all.py'
            Push-Location (Join-Path $RepoRoot 'tools/audio')
            try { & uv run python render_all.py --no-previews 2>&1 | Out-File (Join-Path $LogsDir "audio-render-$ts.log") -Encoding utf8 }
            finally { Pop-Location }
            if (-not (Test-Path $audioManifest)) { Write-Warning "audio render failed (log artifacts/logs/audio-render-$ts.log) - the APK will be silent" }
        } else { Write-Warning 'uv not found: cannot render vehicle audio - the APK will be silent' }
    }
    $log = Join-Path $LogsDir "build-$ts.log"
    $unityArgs = @('-executeMethod', 'Game.Editor.Build.BuildCommands.BuildAndroidApk', '-buildOutput', $apk)
    if ($Development) { $unityArgs += '-development' }
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $code = Invoke-UnityBatch -LogFile $log -Arguments $unityArgs
    $result = Select-String -Path $log -Pattern 'BUILD_RESULT:.*' -ErrorAction SilentlyContinue | Select-Object -Last 1
    if ($code -ne 0 -or -not $result -or $result.Line -notmatch 'BUILD_RESULT: Succeeded' -or -not (Test-Path $apk)) {
        Write-Host "BUILD FAILED (exit $code) after $([int]$sw.Elapsed.TotalSeconds)s, log: $log" -ForegroundColor Red
        Show-UnityLogErrors $log
        exit ([Math]::Max(1, $code))
    }
    $hash = (Get-FileHash -Algorithm SHA256 $apk).Hash.ToLower()
    "$hash  $(Split-Path $apk -Leaf)" | Set-Content "$apk.sha256" -Encoding ascii
    Write-Host $result.Line
    Write-Host ("APK    {0} ({1:N1} MB) in {2}s" -f $apk, ((Get-Item $apk).Length / 1MB), [int]$sw.Elapsed.TotalSeconds)
    Write-Host "SHA256 $hash"
    Write-Host "log    $log"
} else {
    $apk = Get-ChildItem (Join-Path $ArtifactsDir 'apk') -Filter *.apk | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
    if (-not $apk) { throw 'no APK in artifacts/apk (run without -SkipBuild)' }
    Write-Host "using existing APK $apk"
}

if (-not ($Install -or $Run)) { exit 0 }

# ---------------------------------------------------------------- install / run
$devices = @(Resolve-TargetDevices -Serial $Serial -AllDevices:$AllDevices)
if ($devices.Count -eq 0) { Write-Warning 'no target device - install skipped'; exit 0 }

$failed = 0
foreach ($d in $devices) {
    $model = (& $Adb -s $d shell getprop ro.product.model).Trim()
    Write-Host "== $d ($model)"
    $out = & $Adb -s $d install -r -g $apk 2>&1
    if ($LASTEXITCODE -ne 0 -or ($out -join "`n") -notmatch 'Success') {
        Write-Host "  install FAILED: $($out -join ' ')" -ForegroundColor Red; $failed++; continue
    }
    Write-Host '  installed'
    if (-not $Run) { continue }
    if (-not (Test-DeviceUnlocked $d)) {
        Write-Host '  phone is LOCKED (keyguard) - unlock it and keep the screen on; run skipped' -ForegroundColor Red; $failed++; continue
    }

    $component = (& $Adb -s $d shell cmd package resolve-activity --brief $PackageName | Select-Object -Last 1).Trim()
    & $Adb -s $d shell am force-stop $PackageName | Out-Null
    & $Adb -s $d logcat -c
    $startArgs = @('shell', 'am', 'start', '-n', $component)
    if ($Tier) { $startArgs += @('-e', 'tier', $Tier) }
    if ($Fps -gt 0) { $startArgs += @('-e', 'fps', "$Fps") }
    & $Adb -s $d @startArgs | Out-Null
    Write-Host "  launched $component; collecting logcat for $LogcatSeconds s"
    Start-Sleep -Seconds $LogcatSeconds

    $logcat = Join-Path $LogsDir "logcat-$d-$ts.txt"
    & $Adb -s $d logcat -d -v threadtime -s Unity:V AndroidRuntime:E DEBUG:E libc:F CRASH:E ActivityManager:W | Set-Content $logcat -Encoding utf8
    $alive = [bool](& $Adb -s $d shell pidof $PackageName)
    $resumed = [bool]((& $Adb -s $d shell dumpsys activity activities) | Select-String "topResumedActivity=.*$PackageName")
    if (-not $resumed) { Write-Host '  app is not the resumed foreground activity (screen off / locked / backgrounded)' -ForegroundColor Red; $alive = $false }
    $bad = Select-String -Path $logcat -Pattern 'Exception|FATAL|signal \d+ \(SIG|ANR in|Crash' |
        Where-Object { $_.Line -notmatch 'Unity\s*:\s*\[DIAG\]' }
    Select-String -Path $logcat -Pattern '\[BOOT\]|\[DIAG\]' | Select-Object -Last 3 | ForEach-Object { Write-Host "  $($_.Line.Trim())" }
    if ($bad -or -not $alive) {
        Write-Host "  PROBLEMS (alive=$alive, suspicious lines=$(@($bad).Count)) - see $logcat" -ForegroundColor Red
        $bad | Select-Object -First 15 | ForEach-Object { Write-Host "    $($_.Line.Trim())" -ForegroundColor Red }
        $failed++
    } else {
        Write-Host "  OK: app alive, no exceptions in Unity logcat ($logcat)"
    }
}
if ($failed -gt 0) { exit 4 }
exit 0
