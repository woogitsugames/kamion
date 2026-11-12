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

# ---- wait for the phone (lead s12): PHONE_RUN only once no Unity.exe runs; held for the measurement only
function Run-T([string]$exe, [string[]]$argv, [int]$sec, [string]$out = '') {
    $pa = @{ FilePath = $exe; ArgumentList = $argv; PassThru = $true; NoNewWindow = $true }
    if ($out) { $pa.RedirectStandardOutput = $out }
    $p = Start-Process @pa
    if (-not $p.WaitForExit($sec * 1000)) { L "timeout ${sec}s: $exe $($argv -join ' ')"; try { $p.Kill($true) } catch { } }
}
while ($true) {
    $unity = @(Get-Process Unity -ErrorAction SilentlyContinue)
    if (-not (Test-Path $lock) -and $unity.Count -eq 0) {
        try { New-Item -ItemType File $lock -ErrorAction Stop | Out-Null; Set-Content $lock "a16-perf $(Get-Date -Format s) $OutTag"; break } catch { }
    }
    L "waiting: lock=$(Test-Path $lock) unity=$($unity.Count)"
    Start-Sleep -Seconds 20
}
L "lock taken"
try {
    & $adb start-server | Out-Null
    $st = (& $adb -s $Serial get-state) 2>&1
    if ("$st" -notmatch 'device') { throw "A16 not online: $st" }
    if ($Apk) { L "install $Apk"; & $adb -s $Serial install -r -d $Apk | Out-Null; if ($LASTEXITCODE -ne 0) { throw 'install failed' } }
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
        $extra = @('telemetry=1', "route_end=$($seg.s_end_m)")   # r2: rq_landscape=1 removed after ADR 0147 (pass it in -Runs if needed)
        if ($seg.s_start_m -gt 30) { $extra += "route_s=$($seg.s_start_m)" }
        if ($ex) { $extra += ($ex -split ' ' | Where-Object { $_ }) }
        L "run $name ($dur s): $($extra -join ',') battery=$t C"
        & $adb -s $Serial logcat -c
        $dm = @('-NoProfile', '-File', (Join-Path $wt 'scripts/device-metrics.ps1'), '-Serial', $Serial, '-Launch', '-DurationSeconds', "$dur",
            '-WarmupSeconds', '25', '-Tier', $Tier, '-Scene', 'WorldC', '-Autopilot', 'route', '-Speed', '30', '-Trailer', '40', '-Extra', ($extra -join ','))
        if ($Uncapped) { $dm += '-Uncapped' } else { $dm += @('-Fps', "$Fps") }
        $before = @(Get-ChildItem (Join-Path $wt "artifacts/device/$Serial") -Directory -ErrorAction SilentlyContinue | ForEach-Object Name)
        Run-T 'pwsh' $dm ($dur + 150) (Join-Path $env:TEMP "a16perf-dm-$name.txt")
        $new = Get-ChildItem (Join-Path $wt "artifacts/device/$Serial") -Directory | Where-Object { $before -notcontains $_.Name } | Sort-Object Name | Select-Object -Last 1
        $dst = Join-Path $PSScriptRoot "$OutTag/$name"
        New-Item -ItemType Directory -Force $dst | Out-Null
        if ($new) { Copy-Item "$($new.FullName)\*" $dst -Recurse -Force -Exclude 'screen.png'; if (Test-Path "$($new.FullName)\screen.png") { Copy-Item "$($new.FullName)\screen.png" "$dst\screen.png" } }
        Run-T $adb @('-s', $Serial, 'logcat', '-d', '-v', 'threadtime', '-s', 'Unity:V') 60 (Join-Path $dst 'logcat.txt')
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
