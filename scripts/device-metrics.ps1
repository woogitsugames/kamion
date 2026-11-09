<#
.SYNOPSIS
  Collect metrics from the running game on attached phones: frame-time CSV + summary JSON written
  by the Boot diagnostics, screenshot, dumpsys meminfo/thermal/battery/gfxinfo, device props.
.EXAMPLE
  pwsh scripts/device-metrics.ps1                                 # app already running, single phone
  pwsh scripts/device-metrics.ps1 -Launch -DurationSeconds 90     # (re)start app, wait 90 s, collect
  pwsh scripts/device-metrics.ps1 -AllDevices -Launch -DurationSeconds 1800 -Tier Medium -Fps 30
  pwsh scripts/device-metrics.ps1 -Launch -DurationSeconds 90 -Scene DrivingLab -Autopilot circle50 -Speed 40   # scripted driving
.NOTES
  Output: artifacts/device/<serial>/<ts>/ (metrics.json = computed p50/p95/p99 after warm-up).
#>
param(
    [string[]]$Serial,
    [switch]$AllDevices,
    [switch]$Launch,
    [int]$DurationSeconds = 0,
    [int]$WarmupSeconds = 5,
    [ValidateSet('', 'Low', 'Medium', 'High', 'Ultra')] [string]$Tier = '',
    [int]$Fps = 0,
    [string]$Scene = '',
    [string]$Autopilot = '',
    [int]$Speed = 0
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
$ts = Get-Timestamp
$devices = @(Resolve-TargetDevices -Serial $Serial -AllDevices:$AllDevices)
if ($devices.Count -eq 0) { Write-Warning 'no device attached - nothing to collect'; exit 0 }

function Get-Percentile([double[]]$sorted, [double]$p) {
    $rank = [Math]::Ceiling($p * $sorted.Count); if ($rank -lt 1) { $rank = 1 }
    return $sorted[[int]$rank - 1]
}

if ($Launch) {
    foreach ($d in $devices) {
        if (-not (Test-DeviceUnlocked $d)) { Write-Warning "$d is LOCKED (keyguard) - unlock it; measurements would be invalid" }
        $component = (& $Adb -s $d shell cmd package resolve-activity --brief $PackageName | Select-Object -Last 1).Trim()
        & $Adb -s $d shell am force-stop $PackageName | Out-Null
        $startArgs = @('shell', 'am', 'start', '-n', $component)
        if ($Tier) { $startArgs += @('-e', 'tier', $Tier) }
        if ($Fps -gt 0) { $startArgs += @('-e', 'fps', "$Fps") }
        if ($Scene) { $startArgs += @('-e', 'scene', $Scene) }
        if ($Autopilot) { $startArgs += @('-e', 'autopilot', $Autopilot) }
        if ($Speed -gt 0) { $startArgs += @('-e', 'speed', "$Speed") }
        & $Adb -s $d @startArgs | Out-Null
        Write-Host "$d launched $component"
    }
}
if ($DurationSeconds -gt 0) { Write-Host "waiting $DurationSeconds s ..."; Start-Sleep -Seconds $DurationSeconds }

$exit = 0
foreach ($d in $devices) {
    $out = Join-Path $ArtifactsDir "device/$d/$ts"
    New-Item -ItemType Directory -Force $out | Out-Null
    Write-Host "== $d -> $out"

    # Screenshot: screencap to file on device + pull (PowerShell pipes would corrupt binary stdout).
    & $Adb -s $d shell screencap -p /sdcard/kamion_screen.png
    & $Adb -s $d pull /sdcard/kamion_screen.png (Join-Path $out 'screen.png') | Out-Null
    & $Adb -s $d shell rm /sdcard/kamion_screen.png

    # Diagnostics files from Application.persistentDataPath (external app files dir).
    $remote = "/sdcard/Android/data/$PackageName/files/diag"
    & $Adb -s $d pull "$remote/frametimes.csv" (Join-Path $out 'frametimes.csv') 2>&1 | Out-Null
    & $Adb -s $d pull "$remote/summary.json" (Join-Path $out 'summary.json') 2>&1 | Out-Null
    if (-not (Test-Path (Join-Path $out 'frametimes.csv'))) {
        # Debuggable builds: fall back to run-as.
        & $Adb -s $d shell run-as $PackageName cat "files/diag/frametimes.csv" 2>$null | Set-Content (Join-Path $out 'frametimes.csv')
    }

    $props = [ordered]@{}
    foreach ($p in 'ro.product.model', 'ro.product.manufacturer', 'ro.soc.model', 'ro.build.version.release', 'ro.build.version.sdk', 'ro.hardware.egl') {
        $props[$p] = (& $Adb -s $d shell getprop $p).Trim()
    }
    & $Adb -s $d shell dumpsys meminfo $PackageName | Set-Content (Join-Path $out 'meminfo.txt')
    & $Adb -s $d shell dumpsys thermalservice | Set-Content (Join-Path $out 'thermal.txt')
    & $Adb -s $d shell dumpsys battery | Set-Content (Join-Path $out 'battery.txt')
    & $Adb -s $d shell dumpsys gfxinfo $PackageName | Set-Content (Join-Path $out 'gfxinfo.txt')
    & $Adb -s $d logcat -d -v threadtime -s Unity:V | Select-String '\[BOOT\]|\[DIAG\]' | ForEach-Object Line | Set-Content (Join-Path $out 'diag-logcat.txt')

    $pssKb = $null
    $m = Select-String -Path (Join-Path $out 'meminfo.txt') -Pattern 'TOTAL PSS:\s+(\d+)' | Select-Object -First 1
    if (-not $m) { $m = Select-String -Path (Join-Path $out 'meminfo.txt') -Pattern '^\s*TOTAL\s+(\d+)' | Select-Object -First 1 }
    if ($m) { $pssKb = [int64]$m.Matches[0].Groups[1].Value }
    $batt = Select-String -Path (Join-Path $out 'battery.txt') -Pattern '^\s*temperature:\s*(\d+)' | Select-Object -First 1
    $battC = if ($batt) { [double]$batt.Matches[0].Groups[1].Value / 10 } else { $null }
    $therm = Select-String -Path (Join-Path $out 'thermal.txt') -Pattern 'Thermal Status:\s*(\d+)' | Select-Object -First 1
    $thermStatus = if ($therm) { [int]$therm.Matches[0].Groups[1].Value } else { $null }

    $metrics = [ordered]@{
        serial = $d; timestamp = $ts; device = $props
        pssMb = if ($pssKb) { [Math]::Round($pssKb / 1024, 1) } else { $null }
        batteryTempC = $battC; thermalStatus = $thermStatus
    }
    $csv = Join-Path $out 'frametimes.csv'
    if ((Test-Path $csv) -and (Get-Item $csv).Length -gt 20) {
        $rows = Import-Csv $csv | Where-Object { [double]$_.t_s -ge $WarmupSeconds }
        $ms = [double[]]($rows | ForEach-Object { [double]::Parse($_.frame_ms, [Globalization.CultureInfo]::InvariantCulture) } | Sort-Object)
        if ($ms.Count -gt 0) {
            $span = [double]$rows[-1].t_s - [double]$rows[0].t_s
            $metrics.frameTime = [ordered]@{
                samples = $ms.Count; warmupSeconds = $WarmupSeconds; spanSeconds = [Math]::Round($span, 1)
                meanFps = [Math]::Round($ms.Count / [Math]::Max($span, 0.001), 2)
                p50Ms = Get-Percentile $ms 0.50; p95Ms = Get-Percentile $ms 0.95; p99Ms = Get-Percentile $ms 0.99; maxMs = $ms[-1]
                over33ms = @($ms | Where-Object { $_ -gt 33.4 }).Count; over50ms = @($ms | Where-Object { $_ -gt 50 }).Count
            }
        }
    } else {
        Write-Warning "$d : frametimes.csv not available (app not run yet, or storage not readable)"
        $exit = 2
    }
    if (Test-Path (Join-Path $out 'summary.json')) { $metrics.gameSummary = Get-Content (Join-Path $out 'summary.json') -Raw | ConvertFrom-Json }
    $metrics | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $out 'metrics.json') -Encoding utf8

    $ft = $metrics.frameTime
    if ($ft) { Write-Host ("  frames {0} over {1}s: mean {2} fps, p50 {3:F2} / p95 {4:F2} / p99 {5:F2} / max {6:F2} ms" -f $ft.samples, $ft.spanSeconds, $ft.meanFps, $ft.p50Ms, $ft.p95Ms, $ft.p99Ms, $ft.maxMs) }
    Write-Host ("  PSS {0} MB, battery {1} C, thermal status {2}" -f $metrics.pssMb, $battC, $thermStatus)
    Write-Host "  screenshot $(Join-Path $out 'screen.png')"
}
exit $exit
