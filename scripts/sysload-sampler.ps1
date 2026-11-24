<#
.SYNOPSIS
  Background system-load probe for player measurement runs (ADR 0333): once per interval writes total CPU, the game's CPU,
  CPU of everything else, the top-N other processes and the foreground window owner to sysload.csv; plus GPU utilisation / clocks /
  P-state / power (nvidia-smi) in the same row. Lets tools/pcperf/pacing_attribution.py
  tell "the game hitched" from "something else on the PC took the CPU/GPU" (build #5 idle rerun, s24: 579 of 597 frames
  > 40 ms fell into windows in which other agents' Unity/robocopy/Defender work ran).
.EXAMPLE
  pwsh scripts/sysload-sampler.ps1 -GameName Kamion -OutDir artifacts/win/runs/<ts>            # waits for Kamion.exe, stops when it exits
  Start-Process pwsh -ArgumentList '-NoProfile','-File','scripts/sysload-sampler.ps1','-GamePid',"$($p.Id)",'-OutDir',$runDir -WindowStyle Hidden
.NOTES
  Cost (measured s24 on i5-10400F, 330 processes): one Process.GetProcesses() + TotalProcessorTime pass ~21 ms of one core per
  sample; one nvidia-smi query ~66 ms wall (separate short process). The probe runs at BelowNormal priority and never touches the game process
  except reading its counters. WMI perf classes (Win32_PerfFormattedData_*) were rejected: ~2.9 s per sample and WmiPrvSE load.
  CPU percentages are of the WHOLE machine (100 % = all logical CPUs busy), like Task Manager.
#>
param(
    [int]$GamePid = 0,
    [string]$GameName = 'Kamion',
    [Parameter(Mandatory = $true)] [string]$OutDir,
    [int]$IntervalMs = 1000,
    [int]$TopN = 5,
    [int]$WaitForGameSeconds = 120,
    [int]$MaxSeconds = 14400,
    [switch]$NoNvidiaSmi
)
$ErrorActionPreference = 'Stop'
try { [Diagnostics.Process]::GetCurrentProcess().PriorityClass = 'BelowNormal' } catch { }
New-Item -ItemType Directory -Force $OutDir | Out-Null
$OutDir = (Resolve-Path $OutDir).Path
$inv = [Globalization.CultureInfo]::InvariantCulture

Add-Type -Namespace KamionProbe -Name Win -MemberDefinition @'
[DllImport("user32.dll")] public static extern System.IntPtr GetForegroundWindow();
[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(System.IntPtr hWnd, out uint pid);
'@

# --- find the game process ---------------------------------------------------------------------------------------------
$game = $null
$deadline = (Get-Date).AddSeconds($WaitForGameSeconds)
while (-not $game -and (Get-Date) -lt $deadline) {
    if ($GamePid -gt 0) { $game = Get-Process -Id $GamePid -ErrorAction SilentlyContinue }
    else { $game = Get-Process -Name $GameName -ErrorAction SilentlyContinue | Sort-Object StartTime -Descending | Select-Object -First 1 }
    if (-not $game) { Start-Sleep -Milliseconds 250 }
}
if (-not $game) { Write-Warning "sysload: game process not found ($GamePid / $GameName)"; exit 2 }
$gameStart = $game.StartTime
$ncpu = [Environment]::ProcessorCount

# --- GPU: nvidia-smi queried in the loop (a long-lived "-lms -f" instance lost its buffered output when killed) -----------
$smi = $null
if (-not $NoNvidiaSmi) { $smi = Get-Command nvidia-smi -ErrorAction SilentlyContinue }
$gpuQuery = '--query-gpu=utilization.gpu,clocks.gr,clocks.mem,pstate,power.draw,temperature.gpu'

$meta = [ordered]@{
    tool = 'scripts/sysload-sampler.ps1'; adr = '0333'; gamePid = $game.Id; gameName = $game.ProcessName
    gameStartLocal = $gameStart.ToString('o'); logicalCpus = $ncpu; intervalMs = $IntervalMs
    note = 'cpu_* in % of the whole machine; t_game_s = wall - game process StartTime (Unity realtimeSinceStartup starts ~0.3-1 s later, UNVERIFIED offset)'
}
$meta | ConvertTo-Json | Set-Content (Join-Path $OutDir 'sysload-meta.json') -Encoding utf8NoBOM

$csvPath = Join-Path $OutDir 'sysload.csv'
$sw = [IO.StreamWriter]::new($csvPath, $false, [Text.UTF8Encoding]::new($false))
$sw.AutoFlush = $true
$sw.WriteLine('wall,t_game_s,cpu_total_pct,cpu_game_pct,cpu_other_pct,game_fg,fg_name,mem_avail_mb,gpu_util_pct,gpu_clock_mhz,mem_clock_mhz,gpu_pstate,gpu_power_w,gpu_temp_c,top_other')

$prev = @{}; $names = @{}
$prevT = [Diagnostics.Stopwatch]::StartNew()
$t0 = Get-Date
function Sample-Cpu {
    $cur = @{}
    foreach ($p in [Diagnostics.Process]::GetProcesses()) {
        if ($p.Id -eq 0) { continue }   # Idle
        try { $cur[$p.Id] = $p.TotalProcessorTime.TotalMilliseconds; $names[$p.Id] = $p.ProcessName } catch { }
        $p.Dispose()
    }
    return $cur
}
$prev = Sample-Cpu
$prevT.Restart()
$memCounter = $null
try { $memCounter = [Diagnostics.PerformanceCounter]::new('Memory', 'Available MBytes') } catch { }   # name localisation: may fail on PL Windows

while ($true) {
    Start-Sleep -Milliseconds $IntervalMs
    $game.Refresh()
    if ($game.HasExited) { break }
    if (((Get-Date) - $t0).TotalSeconds -gt $MaxSeconds) { break }
    $cur = Sample-Cpu
    $dtMs = $prevT.Elapsed.TotalMilliseconds; $prevT.Restart()
    $cap = $dtMs * $ncpu
    $total = 0.0; $gameMs = 0.0; $others = [Collections.Generic.List[object]]::new()
    foreach ($id in $cur.Keys) {
        if (-not $prev.ContainsKey($id)) { continue }
        $d = $cur[$id] - $prev[$id]
        if ($d -le 0) { continue }
        $total += $d
        if ($id -eq $game.Id) { $gameMs += $d } else { $others.Add([pscustomobject]@{ n = $names[$id]; id = $id; d = $d }) }
    }
    $prev = $cur
    $fgPid = [uint32]0
    $null = [KamionProbe.Win]::GetWindowThreadProcessId([KamionProbe.Win]::GetForegroundWindow(), [ref]$fgPid)
    $fgName = if ($names.ContainsKey([int]$fgPid)) { $names[[int]$fgPid] } else { "pid$fgPid" }
    $top = ($others | Sort-Object d -Descending | Select-Object -First $TopN |
        ForEach-Object { '{0}:{1}={2}' -f $_.n, $_.id, (100.0 * $_.d / $cap).ToString('F1', $inv) }) -join ';'
    $mem = if ($memCounter) { try { [int]$memCounter.NextValue() } catch { '' } } else { '' }
    $gq = ',,,,,'
    if ($smi) {
        $q = & $smi.Source $gpuQuery '--format=csv,noheader,nounits' 2>$null | Select-Object -First 1
        if ($q) { $gq = (($q -split ',\s*') | ForEach-Object { $_.Trim() }) -join ',' }
    }
    $tg = ((Get-Date) - $gameStart).TotalSeconds
    $sw.WriteLine(('{0},{1},{2},{3},{4},{5},{6},{7},{9},{8}' -f (Get-Date).ToString('o'), $tg.ToString('F2', $inv),
        (100.0 * $total / $cap).ToString('F1', $inv), (100.0 * $gameMs / $cap).ToString('F1', $inv),
        (100.0 * ($total - $gameMs) / $cap).ToString('F1', $inv), [int]($fgPid -eq $game.Id), $fgName, $mem, $top, $gq))
}
$sw.Dispose()
exit 0
