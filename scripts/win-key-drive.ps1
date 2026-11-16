<#
.SYNOPSIS
  Evidence that the Windows player drives from the keyboard (ADR 0261): starts Kamion.exe windowed in a region,
  brings the window to the foreground, holds keys through SendInput (scan codes -> raw input -> Unity Input System),
  takes the player's own screenshot and quits. The [CONTROLS] input log and the HUD speed in the screenshot are the proof.
.EXAMPLE
  pwsh scripts/win-key-drive.ps1 -Exe artifacts/win/kamion-.../Kamion.exe -Scene knyszyn-w -Keys W -HoldSeconds 14
.NOTES
  Needs an interactive desktop session; do not touch keyboard / mouse during the run (the window must keep focus).
  Output: artifacts/win/runs/<ts>-keys/{shot.png, player.log}. No Unity editor, no adb.
#>
param(
    [Parameter(Mandatory)] [string]$Exe,
    [string]$Scene = 'knyszyn-w',
    [string[]]$Keys = @('W'),          # held together for -HoldSeconds
    [string[]]$TapFirst = @(),         # tapped once before the hold (e.g. Space = parking brake)
    [int]$LoadSeconds = 20,
    [int]$HoldSeconds = 14,
    [int]$Width = 1600,
    [int]$Height = 900,
    [string[]]$ExtraPlayerArgs = @()
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class KamionKeys {
    [StructLayout(LayoutKind.Sequential)] struct KEYBDINPUT { public ushort wVk; public ushort wScan; public uint dwFlags; public uint time; public IntPtr dwExtraInfo; }
    [StructLayout(LayoutKind.Explicit, Size = 40)] struct INPUT { [FieldOffset(0)] public uint type; [FieldOffset(8)] public KEYBDINPUT ki; }
    [DllImport("user32.dll", SetLastError = true)] static extern uint SendInput(uint n, INPUT[] inputs, int size);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    public static uint Key(ushort scan, bool down) {
        var i = new INPUT[1]; i[0].type = 1; i[0].ki.wScan = scan; i[0].ki.dwFlags = 0x0008u | (down ? 0u : 0x0002u);
        return SendInput(1, i, 40);
    }
}
'@
$scan = @{ W = 0x11; A = 0x1E; S = 0x1F; D = 0x20; C = 0x2E; T = 0x14; Space = 0x39; Esc = 0x01; '1' = 0x02; '2' = 0x03; '3' = 0x04 }
$ts = Get-Timestamp
$runDir = Join-Path $ArtifactsDir "win/runs/$ts-keys"
New-Item -ItemType Directory -Force $runDir | Out-Null
$log = Join-Path $runDir 'player.log'
$shot = Join-Path $runDir 'shot.png'
$total = $LoadSeconds + $HoldSeconds
$playerArgs = @('-screen-fullscreen', '0', '-screen-width', "$Width", '-screen-height', "$Height", '-logFile', $log,
    '-scene', $Scene, '-shot', $shot, '-shot_t', "$($total - 1)", '-quit_t', "$($total + 6)") + $ExtraPlayerArgs
$p = Start-Process -FilePath (Resolve-Path $Exe).Path -ArgumentList $playerArgs -PassThru
$null = $p.Handle
Start-Sleep -Seconds $LoadSeconds
$p.Refresh()
[void][KamionKeys]::ShowWindow($p.MainWindowHandle, 9)
[void][KamionKeys]::SetForegroundWindow($p.MainWindowHandle)
Start-Sleep -Milliseconds 800
$focused = [KamionKeys]::GetForegroundWindow() -eq $p.MainWindowHandle
Write-Host "window focused: $focused"
if (-not $focused) {
    # Windows refuses SetForegroundWindow from a background process: never send keys to somebody else's window.
    Write-Host 'player window is not in the foreground - no keys sent (run from an interactive console, hands off)' -ForegroundColor Red
    if (-not $p.WaitForExit(($HoldSeconds + 60) * 1000)) { $p.Kill() }
    exit 4
}
foreach ($k in $TapFirst) { [void][KamionKeys]::Key($scan[$k], $true); Start-Sleep -Milliseconds 120; [void][KamionKeys]::Key($scan[$k], $false); Start-Sleep -Milliseconds 400 }
foreach ($k in $Keys) { [void][KamionKeys]::Key($scan[$k], $true) }
Start-Sleep -Seconds $HoldSeconds
foreach ($k in $Keys) { [void][KamionKeys]::Key($scan[$k], $false) }
if (-not $p.WaitForExit(60000)) { $p.Kill(); Write-Host 'player killed (did not quit)' -ForegroundColor Red }
Select-String -Path $log -Pattern '^\[CONTROLS\] (in|input|ev)|\[AUTOSHOT\] screenshot|\[START\]' -ErrorAction SilentlyContinue | Select-Object -First 25 | ForEach-Object { Write-Host "  $($_.Line.Trim())" }
Write-Host "run dir $runDir (focused=$focused, exit=$($p.ExitCode))"
if (-not $focused -or -not (Test-Path $shot)) { exit 4 }
exit 0
