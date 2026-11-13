<#
.SYNOPSIS
  ADR 0177: A16 (RFGL34SJYDZ) Low 30 FPS gate-3 drives for the p99 / frames>40 ms analysis and PSO recording.
.DESCRIPTION
  Takes artifacts/locks/PHONE_RUN in the MAIN repo for the whole batch (content: owner + time), removes it at the end (also on
  error). Does NOT wait for running Unity processes to exit (they may keep running; the lock only stops new ones), but
  retries adb when the daemon is restarted by Unity and the phone drops offline. Never types a PIN; a locked phone
  (keyguard) rejects the run. Never touches the S24+.
  Each run: optional install, thermal gate, device-metrics.ps1 drive of G3-A or G3-B (route autopilot 30 km/h, trailer 40 t),
  logcat (Unity tag) copied next to the CSV. -PullPso pulls pso_Vulkan_Low_<tag>.graphicsstate files afterwards.
  Run spec: "name=SEG:extras" separated by ';' (extras space-separated key=value launch arguments).
.EXAMPLE
  pwsh tools/perf/phone-p99.ps1 -Apk artifacts/apk/kamion-0.1.0-<sha>.apk -OutDir artifacts/perf-p99-0177/probe `
       -Runs "a1=A:spike_probe=1;b1=B:spike_probe=1"
  pwsh tools/perf/phone-p99.ps1 -Apk artifacts/apk/kamion-0.1.0-<sha>-dev.apk -OutDir artifacts/perf-p99-0177/trace `
       -Runs "traceA=A:pso_trace=90 pso_tag=g3a;traceB=B:pso_trace=95 pso_tag=g3b" -PullPso g3a,g3b
#>
param(
    [string]$Apk = '',
    [Parameter(Mandatory = $true)] [string]$OutDir,
    [Parameter(Mandatory = $true)] [string]$Runs,
    [string[]]$PullPso = @(),
    [string]$Owner = '0177',
    [string]$Tier = 'Low',
    [int]$Fps = 30,
    [int]$CoolBelowC = 34
)
$ErrorActionPreference = 'Stop'
$Serial = 'RFGL34SJYDZ'
$pkg = 'com.woogitsugames.kamion'
$wt = Split-Path (Split-Path $PSScriptRoot)
$main = 'C:\Users\matma\Documents\Claude\kamion'
$lock = Join-Path $main 'artifacts\locks\PHONE_RUN'
. (Join-Path $wt 'scripts/env.ps1')
$adb = $Adb
if (-not [IO.Path]::IsPathRooted($OutDir)) { $OutDir = Join-Path $main $OutDir }
if ($Apk -and -not [IO.Path]::IsPathRooted($Apk)) { $Apk = Join-Path $main $Apk }
New-Item -ItemType Directory -Force $OutDir | Out-Null
$log = Join-Path $OutDir 'phone-p99.log'
function L($m) { $s = "$(Get-Date -Format 'HH:mm:ss') $m"; Write-Host $s; Add-Content $log $s }
function Wait-Device {
    for ($i = 0; $i -lt 20; $i++) {
        & $adb start-server 2>&1 | Out-Null
        $st = "$((& $adb -s $Serial get-state) 2>&1)"
        if ($st -match '^device') { return }
        L "A16 not online ($st), retry in 30 s"; Start-Sleep -Seconds 30
    }
    throw 'A16 offline for 10 min'
}
function Test-Unlocked { Test-DeviceUnlocked $Serial }

while ($true) {
    if (-not (Test-Path $lock)) {
        try { New-Item -ItemType File $lock -ErrorAction Stop | Out-Null; Set-Content $lock "$Owner $(Get-Date -Format s) $OutDir"; break } catch { }
    }
    L "waiting for PHONE_RUN: $(Get-Content $lock -ErrorAction SilentlyContinue)"
    Start-Sleep -Seconds 60
}
L "lock taken ($Owner)"
try {
    Wait-Device
    if ($Apk) {
        L "install $Apk"
        & $adb -s $Serial install -r $Apk | Out-Null
        if ($LASTEXITCODE -ne 0) { Wait-Device; L 'install -r failed (signature/downgrade?) -> uninstall + install'; & $adb -s $Serial uninstall $pkg | Out-Null; & $adb -s $Serial install $Apk | Out-Null; if ($LASTEXITCODE -ne 0) { throw 'install failed' } }
    }
    $segs = (Get-Content (Join-Path $wt 'Data/Regions/bialystok-industrial-c/gate3_segment.json') -Raw | ConvertFrom-Json).segments
    foreach ($r in ($Runs -split ';' | Where-Object { $_ })) {
        $name, $spec = $r -split '=', 2
        $segId, $ex = $spec -split ':', 2
        $seg = $segs | Where-Object { $_.id -eq "G3-$segId" }
        if (-not $seg) { throw "segment G3-$segId missing" }
        $dur = 25 + [int][Math]::Ceiling($seg.length_m / (30 / 3.6) * 1.35)
        Wait-Device
        $t = 0
        for ($i = 0; $i -lt 15; $i++) {
            $t = [double](((& $adb -s $Serial shell dumpsys battery) | Select-String '^\s*temperature:\s*(\d+)' | Select-Object -First 1).Matches[0].Groups[1].Value) / 10
            if ($t -lt $CoolBelowC) { break }
            L "cooling: battery $t C"; & $adb -s $Serial shell am force-stop $pkg | Out-Null; Start-Sleep -Seconds 60
        }
        if (-not (Test-Unlocked)) { L "REJECTED ${name}: phone locked (keyguard) - unlock the A16"; continue }
        $extra = @('telemetry=1', "route_end=$($seg.s_end_m)")
        if ($seg.s_start_m -gt 30) { $extra += "route_s=$($seg.s_start_m)" }
        if ($ex) { $extra += ($ex -split ' ' | Where-Object { $_ }) }
        L "run $name G3-$segId ($dur s): $($extra -join ',') battery=$t C"
        & $adb -s $Serial logcat -c
        $dm = @('-NoProfile', '-File', (Join-Path $wt 'scripts/device-metrics.ps1'), '-Serial', $Serial, '-Launch', '-DurationSeconds', "$dur",
            '-WarmupSeconds', '25', '-Tier', $Tier, '-Scene', 'WorldC', '-Autopilot', 'route', '-Speed', '30', '-Trailer', '40',
            '-Extra', ($extra -join ','), '-Fps', "$Fps")
        $devRoot = Join-Path $wt "artifacts/device/$Serial"
        $before = @(Get-ChildItem $devRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object Name)
        & pwsh @dm | Out-Null
        $new = Get-ChildItem $devRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $before -notcontains $_.Name } | Sort-Object Name | Select-Object -Last 1
        $dst = Join-Path $OutDir $name
        New-Item -ItemType Directory -Force $dst | Out-Null
        if ($new) { Copy-Item "$($new.FullName)\*" $dst -Recurse -Force }
        & $adb -s $Serial logcat -d -v threadtime -s Unity:V | Set-Content (Join-Path $dst 'logcat.txt') -Encoding utf8
        if (-not (Test-Unlocked)) { L "WARNING ${name}: keyguard showing after the run - measurement REJECTED"; 'REJECTED keyguard' | Set-Content (Join-Path $dst 'REJECTED.txt') }
        & $adb -s $Serial shell am force-stop $pkg | Out-Null
        L "done $name -> $dst"
    }
    foreach ($tag in ($PullPso -join ',' -split ',' | Where-Object { $_ })) {
        $f = "pso_Vulkan_$($Tier)_$tag.graphicsstate"
        & $adb -s $Serial pull "/sdcard/Android/data/$pkg/files/$f" (Join-Path $OutDir $f) | Out-Null
        L "pull $f -> $(Test-Path (Join-Path $OutDir $f))"
    }
}
catch { L "ERROR $_" }
finally {
    & $adb -s $Serial shell am force-stop $pkg 2>&1 | Out-Null
    Remove-Item $lock -Force -ErrorAction SilentlyContinue
    L 'lock released'
}
