<#
  ADR 0136: A16 Low A/B and diagnostic runs (only RFGL34SJYDZ). Waits for: no PHONE_RUN lock, no Unity.exe. Holds the lock
  for the whole batch, force-stops the game and removes the lock at the end (also on error).
  Usage: pwsh artifacts/a16-perf/phone-diag.ps1 -Apk <path> -Runs <name=extras;...> [-Segment B] [-Uncapped]
#>
param(
    [string]$Apk = '',
    [string]$OutTag = 'diag',
    [string]$Segment = 'B',
    [string]$Tier = 'Low',
    [switch]$Uncapped,
    [int]$Fps = 30,
    [string]$Runs = 'base=',   # ';'-separated name=extras (extras space-separated)
    [int]$CoolBelowC = 34
)
$ErrorActionPreference = 'Stop'
$Serial = 'RFGL34SJYDZ'
$main = 'C:\Users\matma\Documents\Claude\kamion'
$wt = Split-Path (Split-Path $PSScriptRoot)
$lock = Join-Path $main 'artifacts\locks\PHONE_RUN'
$adb = (Get-Command adb -ErrorAction SilentlyContinue).Source
if (-not $adb) { . (Join-Path $wt 'scripts/env.ps1'); $adb = $Adb }
$log = Join-Path $PSScriptRoot "$OutTag.log"
function L($m) { $s = "$(Get-Date -Format 'HH:mm:ss') $m"; Write-Host $s; Add-Content $log $s }

# ---- wait for the phone: take PHONE_RUN first (blocks new unity-pool slots), then wait until running Unity exits
while ($true) {
    if (-not (Test-Path $lock)) {
        try { New-Item -ItemType File $lock -ErrorAction Stop | Out-Null; Set-Content $lock "a16-perf $(Get-Date -Format s) $OutTag"; break } catch { }
    }
    L "waiting: lock held by $(Get-Content $lock -ErrorAction SilentlyContinue)"
    Start-Sleep -Seconds 30
}
L "lock taken"
try {
    for ($w = 0; @(Get-Process Unity -ErrorAction SilentlyContinue).Count -gt 0; $w++) {
        if ($w % 4 -eq 0) { L "waiting for running Unity.exe to exit: $(@(Get-Process Unity).Count)" }
        Start-Sleep -Seconds 15
    }
    if (@(Get-Process Unity -ErrorAction SilentlyContinue).Count -gt 0) { throw 'Unity started right after the lock' }
    & $adb start-server | Out-Null
    $st = (& $adb -s $Serial get-state) 2>&1
    if ("$st" -notmatch 'device') { throw "A16 not online: $st" }
    if ($Apk) { L "install $Apk"; & $adb -s $Serial install -r $Apk | Out-Null; if ($LASTEXITCODE -ne 0) { throw 'install failed' } }
    $seg = (Get-Content (Join-Path $wt 'Data/Regions/bialystok-industrial-c/gate3_segment.json') -Raw | ConvertFrom-Json).segments | Where-Object { $_.id -eq "G3-$Segment" }
    $dur = 25 + [int][Math]::Ceiling($seg.length_m / (30 / 3.6) * 1.35)
    foreach ($r in ($Runs -split ';' | Where-Object { $_ })) {
        $name, $ex = $r -split '=', 2
        # thermal gate between runs (battery temperature)
        for ($i = 0; $i -lt 15; $i++) {
            $t = [double](((& $adb -s $Serial shell dumpsys battery) | Select-String '^\s*temperature:\s*(\d+)' | Select-Object -First 1).Matches[0].Groups[1].Value) / 10
            if ($t -lt $CoolBelowC) { break }
            L "cooling: battery $t C"; & $adb -s $Serial shell am force-stop com.woogitsugames.kamion | Out-Null; Start-Sleep -Seconds 60
        }
        $extra = @('telemetry=1', "route_end=$($seg.s_end_m)")
        if ($seg.s_start_m -gt 30) { $extra += "route_s=$($seg.s_start_m)" }
        if ($ex) { $extra += ($ex -split ' ' | Where-Object { $_ }) }
        L "run $name ($dur s): $($extra -join ',') battery=$t C"
        & $adb -s $Serial logcat -c
        $dm = @('-NoProfile', '-File', (Join-Path $wt 'scripts/device-metrics.ps1'), '-Serial', $Serial, '-Launch', '-DurationSeconds', "$dur",
            '-WarmupSeconds', '25', '-Tier', $Tier, '-Scene', 'WorldC', '-Autopilot', 'route', '-Speed', '30', '-Trailer', '40', '-Extra', ($extra -join ','))
        if ($Uncapped) { $dm += '-Uncapped' } else { $dm += @('-Fps', "$Fps") }
        $before = @(Get-ChildItem (Join-Path $wt "artifacts/device/$Serial") -Directory -ErrorAction SilentlyContinue | ForEach-Object Name)
        & pwsh @dm | Out-Null
        $new = Get-ChildItem (Join-Path $wt "artifacts/device/$Serial") -Directory | Where-Object { $before -notcontains $_.Name } | Sort-Object Name | Select-Object -Last 1
        $dst = Join-Path $PSScriptRoot "$OutTag/$name"
        New-Item -ItemType Directory -Force $dst | Out-Null
        if ($new) { Copy-Item "$($new.FullName)\*" $dst -Recurse -Force -Exclude 'screen.png'; if (Test-Path "$($new.FullName)\screen.png") { Copy-Item "$($new.FullName)\screen.png" "$dst\screen.png" } }
        & $adb -s $Serial logcat -d -v threadtime -s Unity:V | Set-Content (Join-Path $dst 'logcat.txt') -Encoding utf8
        $g = @(& $adb -s $Serial shell 'cat /proc/gpufreq/gpufreq_var_dump 2>/dev/null | head -5; cat /sys/kernel/ged/hal/current_freqency 2>/dev/null' 2>&1)
        $g | Set-Content (Join-Path $dst 'gpufreq.txt')
        & $adb -s $Serial shell am force-stop com.woogitsugames.kamion | Out-Null
        L "done $name -> $dst"
    }
}
catch { L "ERROR $_" }
finally {
    & $adb -s $Serial shell am force-stop com.woogitsugames.kamion | Out-Null
    Remove-Item $lock -Force -ErrorAction SilentlyContinue
    L 'lock released'
}
