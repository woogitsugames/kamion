<#
.SYNOPSIS
  Crash reproduction matrix for the Windows player (crash-diag-s23, 16.11): N runs of an existing Kamion.exe with one
  graphics API / window mode / exit path, each with its own -logFile, counting "Crash!!!" and the faulting function.
.DESCRIPTION
  Does not build anything and does not touch ProjectSettings. Takes a 'unity' slot (scripts/unity-slot.ps1) for the
  whole batch, refuses to start while another Kamion.exe runs (the owner's game is never closed), backs up and restores
  %USERPROFILE%\AppData\LocalLow\woogitsugames\Kamion\settings_pc.json, and passes -logFile so the owner's Player.log
  is not rotated. Launch arguments -screen-* / -window-mode make the player ignore the saved display mode
  (StartupDisplayPolicy).
  Exit paths: 'quit' = -quit_t (Application.Quit, as DesktopAutoShot), 'close' = WM_CLOSE to the main window
  (window X / Alt+F4).
  -FocusSeconds > 0: after the world is loaded the script minimises and restores ONLY this player's window every
  -FocusPeriod seconds (ShowWindow on its own HWND; no system setting changes) — the focus-loss path of UUM-148214.
.EXAMPLE
  pwsh scripts/crash-repro.ps1 -Exe <dir>\Kamion.exe -Api d3d12 -Mode exclusive -Exit close -Runs 5 -FocusSeconds 60
#>
param(
    [Parameter(Mandatory)][string]$Exe,
    [ValidateSet('d3d12', 'd3d11')][string]$Api = 'd3d12',
    [ValidateSet('borderless', 'exclusive', 'windowed')][string]$Mode = 'borderless',
    [ValidateSet('quit', 'close')][string]$Exit = 'quit',
    [int]$Runs = 5,
    [string]$Scene = 'knyszyn',
    [string]$Tier = 'Ultra',
    [int]$Fps = 1000,
    [int]$Width = 0,
    [int]$Height = 0,
    [double]$LiveSeconds = 25,
    [double]$FocusSeconds = 0,
    [double]$FocusPeriod = 2,
    [string]$OutDir = '',
    [string]$Label = '',
    [double]$WaitMinutes = 15,
    [string[]]$ExtraArgs = @(),
    [switch]$NoSlot
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$mainRoot = (git -C $root worktree list --porcelain | Select-Object -First 1) -replace '^worktree ', ''
if (-not (Test-Path $Exe)) { throw "no exe: $Exe" }
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
if (-not $Label) { $Label = "$Api-$Mode-$Exit" + ($(if ($FocusSeconds -gt 0) { '-focus' } else { '' })) }
if (-not $OutDir) { $OutDir = Join-Path $root "artifacts/crash-diag-s23/repro/$ts-$Label" }
New-Item -ItemType Directory -Force $OutDir | Out-Null
$settings = Join-Path $env:USERPROFILE 'AppData\LocalLow\woogitsugames\Kamion\settings_pc.json'
$backup = Join-Path $OutDir 'settings_pc.json.orig'
if (Test-Path $settings) { Copy-Item $settings $backup -Force }

Add-Type -Namespace CrashRepro -Name W -MemberDefinition @'
[DllImport("user32.dll")] public static extern bool ShowWindow(System.IntPtr h, int cmd);
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(System.IntPtr h);
[DllImport("user32.dll")] public static extern System.IntPtr GetForegroundWindow();
'@

$owner = "crash-diag-s23"
if (-not $NoSlot) { pwsh -NoProfile -File (Join-Path $mainRoot 'scripts/unity-slot.ps1') -Acquire -Pool heavy -Owner $owner | Out-Null }
$rows = @()
try {
    for ($i = 1; $i -le $Runs; $i++) {
        $log = Join-Path $OutDir ("run{0:D2}.log" -f $i)
        $a = @('-logFile', $log, '-scene', $Scene, '-tier', $Tier, '-fps', "$Fps")
        if ($Api -eq 'd3d11') { $a += '-force-d3d11' } else { $a += '-force-d3d12' }
        switch ($Mode) {
            'windowed'   { $a += @('-screen-fullscreen', '0', '-screen-width', "$(if ($Width) { $Width } else { 1600 })", '-screen-height', "$(if ($Height) { $Height } else { 900 })") }
            'borderless' { $a += @('-screen-fullscreen', '1', '-window-mode', 'borderless') }
            'exclusive'  { $a += @('-screen-fullscreen', '1', '-window-mode', 'exclusive') }
        }
        if ($ExtraArgs) { $a += $ExtraArgs }
        if ($Width -and $Mode -ne 'windowed') { $a += @('-screen-width', "$Width", '-screen-height', "$Height") }
        $total = $LiveSeconds + $FocusSeconds
        if ($Exit -eq 'quit') { $a += @('-shot', (Join-Path $OutDir ("run{0:D2}.png" -f $i)), '-shot_t', "$([math]::Max(1, $total - 3))", '-quit_t', "$total") }
        # a clean run: no other player on the GPU (other agents / the owner); never close them - wait up to -WaitMinutes
        $waitEnd = (Get-Date).AddMinutes($WaitMinutes)
        while ((Get-Process Kamion -ErrorAction SilentlyContinue) -and (Get-Date) -lt $waitEnd) { Start-Sleep -Seconds 10 }
        $otherKamionStart = @(Get-Process Kamion -ErrorAction SilentlyContinue).Count
        $unityCount = @(Get-Process Unity -ErrorAction SilentlyContinue).Count
        $vram = (& nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader 2>$null) -join ' '
        $t0 = Get-Date
        $p = Start-Process -FilePath $Exe -ArgumentList $a -PassThru
        for ($w = 0; $w -lt 40 -and -not $p.HasExited; $w++) { Start-Sleep -Milliseconds 250; $p.Refresh(); if ($p.MainWindowHandle -ne [IntPtr]::Zero) { [CrashRepro.W]::ShowWindow($p.MainWindowHandle, 9) | Out-Null; [CrashRepro.W]::SetForegroundWindow($p.MainWindowHandle) | Out-Null; break } }
        # wait for the world (log line [START] region=) up to 120 s
        $deadline = (Get-Date).AddSeconds(120)
        while ((Get-Date) -lt $deadline -and -not $p.HasExited) {
            if ((Test-Path $log) -and (Select-String -Path $log -Pattern '^\[START\] region=' -Quiet)) { break }
            Start-Sleep -Milliseconds 500
        }
        $loaded = (Get-Date)
        $loadedOk = (Test-Path $log) -and (Select-String -Path $log -Pattern '^\[START\] region=' -Quiet)
        $otherKamionMid = @(Get-Process Kamion -ErrorAction SilentlyContinue | Where-Object Id -ne $p.Id).Count
        $p.Refresh(); $focusedAtLoad = ($p.MainWindowHandle -ne [IntPtr]::Zero) -and ([CrashRepro.W]::GetForegroundWindow() -eq $p.MainWindowHandle)
        if ($FocusSeconds -gt 0 -and -not $p.HasExited) {
            $end = $loaded.AddSeconds($FocusSeconds); $n = 0
            while ((Get-Date) -lt $end -and -not $p.HasExited) {
                $p.Refresh(); $h = $p.MainWindowHandle
                if ($h -ne [IntPtr]::Zero) {
                    [CrashRepro.W]::ShowWindow($h, 6) | Out-Null          # SW_MINIMIZE
                    Start-Sleep -Milliseconds ([int]($FocusPeriod * 500))
                    [CrashRepro.W]::ShowWindow($h, 9) | Out-Null          # SW_RESTORE
                    [CrashRepro.W]::SetForegroundWindow($h) | Out-Null
                    $n++
                }
                Start-Sleep -Milliseconds ([int]($FocusPeriod * 500))
            }
        }
        if ($Exit -eq 'close') {
            $stay = $loaded.AddSeconds($LiveSeconds + $FocusSeconds) - (Get-Date)
            if ($stay.TotalSeconds -gt 0 -and -not $p.HasExited) { Start-Sleep -Seconds $stay.TotalSeconds }
            if (-not $p.HasExited) { $p.Refresh(); $p.CloseMainWindow() | Out-Null }
        }
        if (-not $loadedOk -and -not $p.HasExited) { Write-Host "run $i : world not loaded (unfocused player pauses: runInBackground 0) - killing our own player"; $p.Kill() }
        if (-not $p.WaitForExit(90000)) { Write-Host "run $i hung - killing our own player $($p.Id)"; $p.Kill(); $p.WaitForExit() }
        $code = $p.ExitCode
        $txt = if (Test-Path $log) { Get-Content $log -Raw } else { '' }
        $crash = $txt -match 'Crash!!!'
        $where = if ($txt -match 'swapchain present failed') { 'present' } elseif ($txt -match 'Device failed') { 'device' } elseif ($crash) { 'crash' } else { '' }
        $atExit = $crash -and ($txt -match 'Input System module state changed to: Shutdown\.\s*\r?\nCrash!!!')
        $apiSeen = if ($txt -match "api='([^']+)'") { $Matches[1] } else { '?' }
        $row = [pscustomobject]@{
            run = $i; label = $Label; api = $apiSeen; focusedAtLoad = $focusedAtLoad; mode = $Mode; exit = $Exit; exitCode = $code; crash = $crash; crashAtExit = $atExit
            kind = $where; seconds = [int]((Get-Date) - $t0).TotalSeconds; otherUnity = $unityCount; otherKamionStart = $otherKamionStart; otherKamionMid = $otherKamionMid; gpuBefore = $vram
            valid = ($loadedOk -and $focusedAtLoad -and $otherKamionStart -eq 0 -and $otherKamionMid -eq 0)
        }
        $rows += $row
        $row | Format-List | Out-String | Write-Host
        $rows | Export-Csv (Join-Path $OutDir 'runs.csv')
        Start-Sleep -Seconds 3
    }
}
finally {
    if (Test-Path $backup) { Copy-Item $backup $settings -Force }
    if (-not $NoSlot) { pwsh -NoProfile -File (Join-Path $mainRoot 'scripts/unity-slot.ps1') -Release -Pool heavy -Owner $owner | Out-Null }
}
$v = @($rows | Where-Object valid); $k = @($v | Where-Object crash).Count
"RESULT label=$Label valid=$($v.Count)/$($rows.Count) crashes(valid)=$k atExit(valid)=$(@($v | Where-Object crashAtExit).Count) crashes(all)=$(@($rows | Where-Object crash).Count) out=$OutDir"



