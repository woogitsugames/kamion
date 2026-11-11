# ADR 0113: phone video of the forest in motion (G3-A, Low, 30 FPS), forest fast path on vs off (same APK). A16 only.
param([string]$Apk)
$ErrorActionPreference = 'Stop'
$d = $PSScriptRoot; $wt = Split-Path (Split-Path $d); $Serial = 'RFGL34SJYDZ'
$lock = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
. (Join-Path $wt 'scripts/env.ps1')
while ($true) { if (-not (Test-Path $lock) -and @(Get-Process Unity -ErrorAction SilentlyContinue).Count -eq 0) { try { New-Item -ItemType File $lock -ErrorAction Stop | Out-Null; Set-Content $lock "perf-low-r2 $(Get-Date -Format s) shimmer"; break } catch {} }; Start-Sleep 60 }
try {
    New-Item -ItemType Directory -Force "$d/shimmer" | Out-Null
    foreach ($r in @(@('after', ''), @('before', 'rq_forestfast=0'))) {
        $ex = 'telemetry=1,route_end=450' + $(if ($r[1]) { ",$($r[1])" } else { '' })
        $job = Start-Job -ScriptBlock { param($Adb, $Serial) Start-Sleep 30; & $Adb -s $Serial shell screenrecord --time-limit 20 --bit-rate 24000000 /sdcard/kamion_shimmer.mp4 } -ArgumentList $Adb, $Serial
        & pwsh -NoProfile -File (Join-Path $wt 'scripts/device-metrics.ps1') -Serial $Serial -Launch -DurationSeconds 55 -WarmupSeconds 25 -Tier Low -Fps 30 `
            -Scene WorldC -Autopilot route -Speed 30 -Trailer 40 -Extra $ex | Out-Null
        Wait-Job $job | Out-Null
        & $Adb -s $Serial pull /sdcard/kamion_shimmer.mp4 "$d/shimmer/$($r[0]).mp4" | Out-Null
        & $Adb -s $Serial shell am force-stop com.woogitsugames.kamion | Out-Null
    }
} finally {
    & $Adb -s $Serial shell am force-stop com.woogitsugames.kamion | Out-Null
    Remove-Item $lock -Force -ErrorAction SilentlyContinue
    'done' | Out-File "$d/shimmer.done"
}
