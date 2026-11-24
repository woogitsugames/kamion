<#
.SYNOPSIS
  ADR 0333 experiment helper: switch Windows power throttling (EcoQoS: execution speed + "ignore timer resolution")
  OFF (or back to system default) for a running process, e.g. the Kamion player, without rebuilding it.
.EXAMPLE
  pwsh scripts/set-power-throttling.ps1 -ProcessName Kamion -Mode Off      # opt out (what a game build would do itself)
  pwsh scripts/set-power-throttling.ps1 -TargetPid 1234 -Mode Default             # let Windows decide again
.NOTES
  SetProcessInformation(ProcessPowerThrottling) with PROCESS_POWER_THROTTLING_STATE {Version 1, ControlMask, StateMask}:
  ControlMask = EXECUTION_SPEED (0x1) | IGNORE_TIMER_RESOLUTION (0x4); StateMask 0 = never throttle. Mode Default = ControlMask 0.
#>
param([int]$TargetPid = 0, [string]$ProcessName = 'Kamion', [ValidateSet('Off', 'Default')] [string]$Mode = 'Off', [int]$WaitSeconds = 60)
$ErrorActionPreference = 'Stop'
Add-Type -Namespace KamionProbe -Name Power -MemberDefinition @'
[System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)]
public struct PROCESS_POWER_THROTTLING_STATE { public uint Version; public uint ControlMask; public uint StateMask; }
[DllImport("kernel32.dll", SetLastError = true)] public static extern System.IntPtr OpenProcess(uint access, bool inherit, int pid);
[DllImport("kernel32.dll", SetLastError = true)] public static extern bool CloseHandle(System.IntPtr h);
[DllImport("kernel32.dll", SetLastError = true)] public static extern bool SetProcessInformation(System.IntPtr h, int cls, ref PROCESS_POWER_THROTTLING_STATE info, int size);
'@
$deadline = (Get-Date).AddSeconds($WaitSeconds); $p = $null
while (-not $p -and (Get-Date) -lt $deadline) {
    $p = if ($TargetPid -gt 0) { Get-Process -Id $TargetPid -ErrorAction SilentlyContinue } else { Get-Process -Name $ProcessName -ErrorAction SilentlyContinue | Sort-Object StartTime -Descending | Select-Object -First 1 }
    if (-not $p) { Start-Sleep -Milliseconds 250 }
}
if (-not $p) { Write-Warning "process not found"; exit 2 }
$h = [KamionProbe.Power]::OpenProcess(0x0200, $false, $p.Id)   # PROCESS_SET_INFORMATION
if ($h -eq [IntPtr]::Zero) { Write-Warning "OpenProcess failed: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())"; exit 3 }
$s = New-Object KamionProbe.Power+PROCESS_POWER_THROTTLING_STATE
$s.Version = 1; $s.ControlMask = if ($Mode -eq 'Off') { 0x5 } else { 0 }; $s.StateMask = 0
$ok = [KamionProbe.Power]::SetProcessInformation($h, 4, [ref]$s, [Runtime.InteropServices.Marshal]::SizeOf($s))
$err = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
[void][KamionProbe.Power]::CloseHandle($h)
"power throttling $Mode for $($p.ProcessName) pid $($p.Id): ok=$ok err=$err"
if (-not $ok) { exit 4 }
