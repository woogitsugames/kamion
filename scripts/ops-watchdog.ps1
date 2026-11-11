<#
.SYNOPSIS
  Machine guard for many parallel agent sessions (GPT/Codex + Claude) on one PC. Enforces limits WITHOUT the sessions'
  cooperation (2026-11-11: ~13 parallel pytest/build_world runs froze the PC at 100 % CPU/RAM).
.DESCRIPTION
  Every -IntervalSeconds:
   1. python/Unity/uv/blender processes -> priority BelowNormal and CPU affinity on all but -ReservedCores logical cores
      (Windows, the desktop and the chat apps keep their cores).
   2. "Heavy" Python jobs = python.exe whose command line runs pytest, build_world.py, build_all.py or fidelity/run.py
      (a job = that process plus its child processes, e.g. multiprocessing workers). At most -MaxHeavy jobs run;
      the newest extra jobs are SUSPENDED (frozen, not killed) and resumed oldest-first when a slot frees.
   3. If free RAM < -MinFreeGB, the newest running heavy job is suspended too (resumed when free RAM > -ResumeFreeGB).
  Unity is not suspended (it holds GPU/licence state); use scripts/unity-slot.ps1 for Unity.
  Log: artifacts/logs/ops-watchdog.log. Stop: Ctrl+C or kill the pwsh process; all suspended jobs are resumed on exit.
#>
param(
    [int]$MaxHeavy = 3,
    [int]$ReservedCores = 4,
    [double]$MinFreeGB = 8,
    [double]$ResumeFreeGB = 14,
    [int]$IntervalSeconds = 15
)
$ErrorActionPreference = 'Continue'
$log = 'C:\Users\matma\Documents\Claude\kamion\artifacts\logs\ops-watchdog.log'
function Log($m) { $line = "{0:HH:mm:ss} {1}" -f (Get-Date), $m; Add-Content $log $line; Write-Host $line }

Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class NtProc {
  [DllImport("ntdll.dll")] public static extern int NtSuspendProcess(IntPtr h);
  [DllImport("ntdll.dll")] public static extern int NtResumeProcess(IntPtr h);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern IntPtr OpenProcess(uint a, bool i, int pid);
  [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr h);
  public static void Suspend(int pid){ var h=OpenProcess(0x0800,false,pid); if(h!=IntPtr.Zero){ NtSuspendProcess(h); CloseHandle(h);} }
  public static void Resume(int pid){ var h=OpenProcess(0x0800,false,pid); if(h!=IntPtr.Zero){ NtResumeProcess(h); CloseHandle(h);} }
}
'@

$cores = [Environment]::ProcessorCount
$mask = [IntPtr]([long]([math]::Pow(2, $cores - $ReservedCores) - 1))
$suspended = @{}   # root pid -> list of pids
$heavyRe = 'pytest|build_world\.py|build_all\.py|fidelity[\\/]run\.py'

function Get-Tree($rootPid, $all) {
    $ids = @($rootPid); $frontier = @($rootPid)
    while ($frontier.Count) { $next = @($all | Where-Object { $frontier -contains $_.ParentProcessId } | ForEach-Object ProcessId); $ids += $next; $frontier = $next }
    $ids
}
function Set-Tree($ids, [bool]$suspend) { foreach ($i in $ids) { if ($suspend) { [NtProc]::Suspend($i) } else { [NtProc]::Resume($i) } } }

try {
    Log "start MaxHeavy=$MaxHeavy ReservedCores=$ReservedCores/$cores MinFreeGB=$MinFreeGB"
    while ($true) {
        foreach ($p in Get-Process python, Unity, uv, blender -ErrorAction SilentlyContinue) {
            try { if ($p.PriorityClass -ne 'BelowNormal' -and $p.PriorityClass -ne 'Idle') { $p.PriorityClass = 'BelowNormal' }; $p.ProcessorAffinity = $mask } catch {}
        }
        $all = @(Get-CimInstance Win32_Process -Filter "name='python.exe'" | Select-Object ProcessId, ParentProcessId, CreationDate, CommandLine)
        $pyIds = $all | ForEach-Object ProcessId
        # roots: heavy python whose parent is not itself a heavy python
        $heavy = @($all | Where-Object { $_.CommandLine -match $heavyRe } | Where-Object { -not ($pyIds -contains $_.ParentProcessId -and ($all | Where-Object ProcessId -eq $_.ParentProcessId).CommandLine -match $heavyRe) } | Sort-Object CreationDate)
        $alive = $heavy | ForEach-Object ProcessId
        foreach ($k in @($suspended.Keys)) { if ($alive -notcontains $k) { $suspended.Remove($k) } }
        $running = @($heavy | Where-Object { -not $suspended.ContainsKey($_.ProcessId) })
        $freeGB = (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB
        $limit = $MaxHeavy
        if ($freeGB -lt $MinFreeGB) { $limit = [math]::Max(1, $running.Count - 1) }
        # suspend newest extras
        if ($running.Count -gt $limit) {
            foreach ($j in ($running | Select-Object -Last ($running.Count - $limit))) {
                $ids = Get-Tree $j.ProcessId $all; Set-Tree $ids $true; $suspended[$j.ProcessId] = $ids
                Log ("SUSPEND pid {0} ({1:N1} GB free): {2}" -f $j.ProcessId, $freeGB, ($j.CommandLine.Substring(0, [Math]::Min(140, $j.CommandLine.Length))))
            }
        }
        elseif ($suspended.Count -and $running.Count -lt $MaxHeavy -and $freeGB -gt $ResumeFreeGB) {
            $oldest = $heavy | Where-Object { $suspended.ContainsKey($_.ProcessId) } | Select-Object -First 1
            if ($oldest) { Set-Tree (Get-Tree $oldest.ProcessId $all) $false; $suspended.Remove($oldest.ProcessId); Log ("RESUME pid {0} ({1:N1} GB free)" -f $oldest.ProcessId, $freeGB) }
        }
        Start-Sleep -Seconds $IntervalSeconds
    }
}
finally {
    foreach ($k in @($suspended.Keys)) { Set-Tree $suspended[$k] $false }
    Log "stop - resumed $($suspended.Count) suspended job(s)"
}
