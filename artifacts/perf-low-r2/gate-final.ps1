<#
  ADR 0113 final A16 runs (RFGL34SJYDZ only): gate3 Low A/B with the clean APK, then same-APK "before" runs
  (-BeforeExtra, default rq_forestfast=0 + pso_warm=0, capped 30) for G3-A and G3-B Low. Waits for no PHONE_RUN and no Unity.exe; holds the lock.
#>
param([Parameter(Mandatory = $true)] [string]$Apk, [string]$Tag = 'final', [string]$BeforeExtra = 'rq_forestfast=0,pso_warm=0', [string[]]$Tiers = @('Low'))
$ErrorActionPreference = 'Stop'
$Serial = 'RFGL34SJYDZ'
$main = 'C:\Users\matma\Documents\Claude\kamion'
$wt = Split-Path (Split-Path $PSScriptRoot)
$lock = Join-Path $main 'artifacts\locks\PHONE_RUN'
. (Join-Path $wt 'scripts/env.ps1')
$log = Join-Path $PSScriptRoot "$Tag.log"
function L($m) { $s = "$(Get-Date -Format 'HH:mm:ss') $m"; Write-Host $s; Add-Content $log $s }
while ($true) {
    $unity = @(Get-Process Unity -ErrorAction SilentlyContinue)
    if (-not (Test-Path $lock) -and $unity.Count -eq 0) {
        try { New-Item -ItemType File $lock -ErrorAction Stop | Out-Null; Set-Content $lock "perf-low-r2 $(Get-Date -Format s) $Tag"; break } catch { }
    }
    L "waiting: lock=$(Test-Path $lock) unity=$($unity.Count)"; Start-Sleep -Seconds 60
}
L 'lock taken'
try {
    & $Adb start-server | Out-Null
    $first = $true
    foreach ($run in @(foreach ($tt in $Tiers) { ,@($tt, 'A'); ,@($tt, 'B') })) {
        $t = [double](((& $Adb -s $Serial shell dumpsys battery) | Select-String '^\s*temperature:\s*(\d+)' | Select-Object -First 1).Matches[0].Groups[1].Value) / 10
        L "gate3 $($run[0]) $($run[1]) battery=$t C"
        $a = @('-NoProfile', '-File', (Join-Path $wt 'scripts/gate3-run.ps1'), '-Serial', $Serial, '-Segment', $run[1], '-Tier', $run[0], '-Fps', '30', '-SkipBuild', '-Apk', $Apk, '-SkipCameras')
        & pwsh @a 2>&1 | Select-String -Pattern 'gate3|frames|p95|valid|REJECT|ERROR|WARN' | ForEach-Object { L "  $_" }
        L "  exit $LASTEXITCODE"
        & $Adb -s $Serial shell am force-stop com.woogitsugames.kamion | Out-Null
    }
    # same-APK "before" (forest fast path off, no PSO warm-up), G3-A and G3-B capped 30
    foreach ($segId in 'A', 'B') {
        $seg = (Get-Content (Join-Path $wt 'Data/Regions/bialystok-industrial-c/gate3_segment.json') -Raw | ConvertFrom-Json).segments | Where-Object { $_.id -eq "G3-$segId" }
        $dur = 25 + [int][Math]::Ceiling($seg.length_m / (30 / 3.6) * 1.35)
        $ex = "telemetry=1,route_end=$($seg.s_end_m)"
        if ($seg.s_start_m -gt 30) { $ex += ",route_s=$($seg.s_start_m)" }
        if ($BeforeExtra) { $ex += ",$BeforeExtra" }
        L "before Low $segId $ex"
        $before = @(Get-ChildItem (Join-Path $ArtifactsDir "device/$Serial") -Directory -ErrorAction SilentlyContinue | ForEach-Object Name)
        & $Adb -s $Serial logcat -c
        & pwsh -NoProfile -File (Join-Path $wt 'scripts/device-metrics.ps1') -Serial $Serial -Launch -DurationSeconds $dur -WarmupSeconds 25 -Tier Low -Fps 30 `
            -Scene WorldC -Autopilot route -Speed 30 -Trailer 40 -Extra $ex | Out-Null
        $new = Get-ChildItem (Join-Path $ArtifactsDir "device/$Serial") -Directory | Where-Object { $before -notcontains $_.Name } | Sort-Object Name | Select-Object -Last 1
        $dst = Join-Path $PSScriptRoot "$Tag/before-Low-$segId"; New-Item -ItemType Directory -Force $dst | Out-Null
        if ($new) { Copy-Item "$($new.FullName)\*" $dst -Recurse -Force }
        & $Adb -s $Serial logcat -d -v threadtime -s Unity:V | Set-Content (Join-Path $dst 'logcat.txt') -Encoding utf8
        & $Adb -s $Serial shell am force-stop com.woogitsugames.kamion | Out-Null
        L "  done -> $dst"
    }
}
catch { L "ERROR $_" }
finally {
    & $Adb -s $Serial shell am force-stop com.woogitsugames.kamion | Out-Null
    Remove-Item $lock -Force -ErrorAction SilentlyContinue
    L 'lock released'
}
