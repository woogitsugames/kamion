<#
.SYNOPSIS
  PC measurement run (ADR 0266): start the Windows player with -metrics, sample process RAM / VRAM while it runs,
  collect frames.csv / memory.csv / run.json / screen.png / Player.log and build the report (tools/pcperf/pc_metrics.py).
  Desktop counterpart of scripts/device-metrics.ps1. SZKIC — written without Windows/pwsh at hand, not run yet.
.EXAMPLE
  pwsh scripts/pc-metrics.ps1 -Exe artifacts/win/kamion-<ver>-<sha>-regions/Kamion.exe                  # Boot scene, 90 s, no budget
  pwsh scripts/pc-metrics.ps1 -Exe <exe> -Scene knyszyn-w -Tier High -Fps 60 -Width 1920 -Height 1080 -Class zalecany
  pwsh scripts/pc-metrics.ps1 -Exe <exe> -Scene knyszyn-w -Tier Low -Fps 30 -Class min -DurationSeconds 1800      # 30 min (Etap 5), D74 min = Low 1080p30
  pwsh scripts/pc-metrics.ps1 -Exe <exe> -Scene DrivingLab -Extra autopilot=circle50,speed=40,trailer=40 -Fps 240 -VSync 0   # uncapped headroom
.NOTES
  Output: artifacts/pc/<machine>/<ts>/ (pc-report.md / .json; exit code of the parser: 0 in budget, 1 over budget, 2 invalid).
  This script only takes the path to an already built .exe - building is scripts/build-windows.ps1 (ADR 0261), whose output
  is artifacts/win/kamion-<version>-<sha>[-low][-regions][-dev]/Kamion.exe. The region must be in that build (-Regions).
  Do not pass the DesktopAutoShot arguments (-shot / -quit_t) here: the recorder quits the player itself after
  -metricsSeconds and writes screen.png. Without -Tier / -Fps a desktop player starts at High / 60 fps (ADR 0261), so
  for the "min" class pass -Tier Low -Fps 30 or the parser reports a context mismatch.
  Rules (docs/03): player only (never the editor), window in focus for the whole run, nothing else rendering on the machine,
  same machine + same route for before/after comparisons. The developer RTX 5070 machine is a measuring machine, NOT the
  reference PC (ADR 0260) - its reports say "informacyjny" until the owner names reference hardware.
#>
param(
    [Parameter(Mandatory = $true)] [string]$Exe,
    [string]$Scene = '',
    [ValidateSet('', 'Low', 'Medium', 'High', 'Ultra')] [string]$Tier = '',
    [int]$Fps = 0,
    [int]$Width = 1920,
    [int]$Height = 1080,
    [ValidateSet('borderless', 'exclusive', 'windowed')] [string]$WindowMode = 'borderless',
    [int]$DurationSeconds = 90,
    [int]$WarmupSeconds = 5,
    [ValidateSet('', 'boot', 'region')] [string]$Start = '',
    [ValidateRange(-1, 1)] [int]$VSync = -1,
    # Budget class from tools/pcperf/budgets/pc-budgets.json (min | zalecany | wysoki); empty = numbers only.
    [string]$Class = '',
    [switch]$AllowContextMismatch,
    [string]$Label = '',
    # Extra game launch arguments "key=value" -> "-key value" (e.g. autopilot=circle50,speed=40, rq_msaa=1).
    [string[]]$Extra = @(),
    # Max wait for the region before the player gives up (player exit code 3).
    [int]$StartupTimeoutSeconds = 300,
    [int]$SampleSeconds = 1,
    [switch]$NoNvidiaSmi,
    [switch]$NoParse,
    [string]$OutDir = ''
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"

$exePath = (Resolve-Path $Exe).Path
if (-not (Test-Path $exePath -PathType Leaf)) { throw "player not found: $Exe" }
$procName = [IO.Path]::GetFileNameWithoutExtension($exePath)
if (Get-Process -Name $procName -ErrorAction SilentlyContinue) {
    throw "$procName is already running - close it first (one player per measurement)"
}

$ts = Get-Timestamp
$machine = ($env:COMPUTERNAME -replace '[^A-Za-z0-9_-]', '_')
if (-not $OutDir) { $OutDir = Join-Path $ArtifactsDir "pc/$machine/$ts" }
New-Item -ItemType Directory -Force $OutDir | Out-Null
$OutDir = (Resolve-Path $OutDir).Path
Write-Host "== pc-metrics -> $OutDir"

# --- launch arguments ----------------------------------------------------------------------------------------------
$fullscreen = if ($WindowMode -eq 'windowed') { '0' } else { '1' }
$argv = @(
    '-metrics', $OutDir,
    '-metricsSeconds', "$DurationSeconds",
    '-metricsWarmup', "$WarmupSeconds",
    '-metricsTimeout', "$StartupTimeoutSeconds",
    '-logFile', (Join-Path $OutDir 'Player.log'),
    '-screen-width', "$Width", '-screen-height', "$Height",
    '-screen-fullscreen', $fullscreen
)
if ($WindowMode -ne 'windowed') { $argv += @('-window-mode', $WindowMode) }
if ($Label) { $argv += @('-metricsLabel', $Label) } elseif ($Class) { $argv += @('-metricsLabel', $Class) }
if ($Start) { $argv += @('-metricsStart', $Start) }
if ($VSync -ge 0) { $argv += @('-metricsVsync', "$VSync") }
if ($Tier) { $argv += @('-tier', $Tier) }
if ($Fps -gt 0) { $argv += @('-fps', "$Fps") }
if ($Scene) { $argv += @('-scene', $Scene) }
foreach ($kv in ($Extra -split ',' | Where-Object { $_ })) { $k, $v = $kv -split '=', 2; $argv += @("-$k", $v) }

$sha = (Get-FileHash -Algorithm SHA256 $exePath).Hash.ToLowerInvariant()
$meta = [ordered]@{
    tool = 'scripts/pc-metrics.ps1'; adr = '0266'; timestamp = $ts; machine = $machine
    exe = $exePath; exeSha256 = $sha; arguments = $argv; class = $Class
    gitSha = (Get-GitShortSha)
}

# --- run + sample process memory / VRAM ----------------------------------------------------------------------------
$nvsmi = $null
if (-not $NoNvidiaSmi) { $nvsmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue }
# Quote arguments with spaces (Start-Process joins the array with spaces).
$argLine = ($argv | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join ' '
Write-Host "start: $exePath $argLine"
$p = Start-Process -FilePath $exePath -ArgumentList $argLine -PassThru
$t0 = Get-Date
$deadline = $t0.AddSeconds($DurationSeconds + $StartupTimeoutSeconds + 60)
$rows = [System.Collections.Generic.List[string]]::new()
$rows.Add('t_s,working_set_mb,private_mb,gpu_dedicated_mb,gpu_shared_mb,gpu_temp_c,gpu_util_pct')
$inv = [Globalization.CultureInfo]::InvariantCulture
$timedOut = $false
while (-not $p.HasExited) {
    if ((Get-Date) -gt $deadline) { $timedOut = $true; Write-Warning 'player did not finish in time - killing'; $p.Kill(); break }
    try {
        $p.Refresh()
        $ws = $p.WorkingSet64 / 1MB; $priv = $p.PrivateMemorySize64 / 1MB
        # Sampling cost: one CIM query (+ nvidia-smi) per second on the same machine - small but not zero; keep it identical
        # for before/after comparisons (use -SampleSeconds 5 for long runs).
        # GPU memory per process: WMI class of the "GPU Process Memory" counter set (names not localized, unlike Get-Counter
        # paths on a Polish Windows). Instances are pid_<pid>_luid_..._phys_N - summed over adapters. UNVERIFIED on the target PC.
        $ded = $null; $shr = $null
        $gpuMem = Get-CimInstance -ClassName Win32_PerfFormattedData_GPUPerformanceCounters_GPUProcessMemory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like "pid_$($p.Id)_*" }
        if ($gpuMem) {
            $ded = (($gpuMem | Measure-Object -Property DedicatedUsage -Sum).Sum) / 1MB
            $shr = (($gpuMem | Measure-Object -Property SharedUsage -Sum).Sum) / 1MB
        }
        $temp = ''; $util = ''
        if ($nvsmi) {
            $q = & $nvsmi.Source --query-gpu=temperature.gpu,utilization.gpu --format=csv,noheader,nounits 2>$null | Select-Object -First 1
            if ($q) { $parts = $q -split ',\s*'; $temp = $parts[0].Trim(); $util = $parts[1].Trim() }
        }
        $t = ((Get-Date) - $t0).TotalSeconds
        $f = { param($x) if ($null -eq $x) { '' } else { ([double]$x).ToString('F1', $inv) } }
        $rows.Add(('{0},{1},{2},{3},{4},{5},{6}' -f $t.ToString('F2', $inv), (& $f $ws), (& $f $priv), (& $f $ded), (& $f $shr), $temp, $util))
    } catch {
        if (-not $p.HasExited) { Write-Warning "sample failed: $($_.Exception.Message)" }
    }
    Start-Sleep -Seconds $SampleSeconds
}
$p.WaitForExit()
$playerExit = if ($timedOut) { -1 } else { $p.ExitCode }
$rows | Set-Content (Join-Path $OutDir 'process.csv') -Encoding utf8NoBOM
$meta.playerExitCode = $playerExit
$meta.wallSeconds = [Math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
$meta.processSamples = $rows.Count - 1
$meta | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $OutDir 'pc-metrics-meta.json') -Encoding utf8NoBOM
Write-Host "player exit $playerExit after $($meta.wallSeconds) s; process samples $($meta.processSamples)"

foreach ($f in 'run.json', 'frames.csv', 'memory.csv') {
    if (-not (Test-Path (Join-Path $OutDir $f))) { Write-Warning "missing $f (player exit $playerExit) - see Player.log" }
}
if ($playerExit -eq 3) { Write-Warning 'player: region did not load within the startup timeout (-scene name? scene in this build?)' }
if (-not (Test-Path (Join-Path $OutDir 'run.json'))) { exit 2 }
if ($NoParse) { exit 0 }

# --- report ----------------------------------------------------------------------------------------------------------
$parser = Join-Path $RepoRoot 'tools/pcperf/pc_metrics.py'
$pargs = @('run', '--no-project', 'python', $parser, $OutDir)
if ($Class) { $pargs += @('--class', $Class) }
if ($AllowContextMismatch) { $pargs += '--allow-context-mismatch' }
& uv @pargs
$code = $LASTEXITCODE
Write-Host "report: $(Join-Path $OutDir 'pc-report.md') (exit $($code): 0 in budget / 1 over budget / 2 invalid)"
exit $code
