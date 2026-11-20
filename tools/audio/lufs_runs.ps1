<#
.SYNOPSIS
  D92 / ADR 0311: cab loudness measurement runs of a Windows player (DrivingLab, autopilot, 40 t combination).
.DESCRIPTION
  Runs the player once per (sound set x scenario), records the listener mix (-audio_capture, ADR 0286; after the cab
  bus gain of ADR 0311) and measures it with pc_capture.py (BS.1770-4) + lufs_calibrate.py (ffmpeg ebur128 cross-check).
  Scenarios:
    straight = autopilot straight080 -speed 50: idle (settle), full-throttle launch 0 -> 50 km/h, hold 50, emergency stop,
               idle until quit. THE calibration scenario of D92 (whole capture integrated).
    circle   = autopilot circle50: launch, then a steady 50 km/h drive on the pad circle.
  One player at a time (take the heavy slot outside this script). Output: <OutDir>/<label>-<set>-<scenario>/
  (capture.wav, player.log, *_report.json, *_spectrogram.png, *_calib.json).
.EXAMPLE
  pwsh tools/audio/lufs_runs.ps1 -Exe artifacts/win/before/Kamion.exe -OutDir artifacts/audio-lufs-s24/before -Label before
  pwsh tools/audio/lufs_runs.ps1 -Exe ... -Label a0 -GainDb 0       # -audio_cab_gain_db override (A/B, ADR 0311)
#>
param(
    [Parameter(Mandatory)][string]$Exe,
    [Parameter(Mandatory)][string]$OutDir,
    [string]$Label = 'run',
    [string[]]$Sets = @('el', 'synth'),
    [string[]]$Scenarios = @('straight', 'circle'),
    [string]$GainDb = '',          # '' = build default (CabinLoudness constants)
    [double]$CurrentDb = 0,        # gain the build applies for the calibration print (lufs_calibrate --current-db)
    [int]$CaptureT0 = 8,
    [int]$CaptureSeconds = 62,
    [string]$Tier = 'Medium'
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$audio = Join-Path $repo 'tools/audio'
$exePath = (Resolve-Path $Exe).Path
$runSeconds = $CaptureT0 + $CaptureSeconds + 4
foreach ($set in $Sets) {
    foreach ($sc in $Scenarios) {
        $dir = Join-Path $OutDir "$Label-$set-$sc"
        New-Item -ItemType Directory -Force $dir | Out-Null
        $dir = (Resolve-Path $dir).Path
        $wav = Join-Path $dir 'capture.wav'
        $log = Join-Path $dir 'player.log'
        $ap = if ($sc -eq 'straight') { @('-autopilot', 'straight080', '-speed', '50') } else { @('-autopilot', 'circle50') }
        $pa = @('-screen-fullscreen', '0', '-screen-width', '1600', '-screen-height', '900', '-logFile', $log,
            '-quit_t', "$runSeconds", '-tier', $Tier, '-fps', '60', '-scene', 'DrivingLab', '-trailer', '40',
            '-engine_audio', $set, '-audio_capture', $wav, '-audio_capture_t0', "$CaptureT0",
            '-audio_capture_s', "$CaptureSeconds", '-audio_view', 'cab', '-audio_stats', '1') + $ap
        if ($GainDb -ne '') { $pa += @('-audio_cab_gain_db', $GainDb) }
        Write-Host "run $Label/$set/$sc : $($pa -join ' ')"
        $p = Start-Process -FilePath $exePath -ArgumentList $pa -PassThru
        $null = $p.Handle
        if (-not $p.WaitForExit(($runSeconds + 90) * 1000)) { $p.Kill(); $p.WaitForExit(); Write-Warning "killed (hang): $dir" }
        if (-not (Test-Path $wav)) { Write-Warning "no capture: $dir"; continue }
        Push-Location $audio
        try {
            uv run python pc_capture.py $wav $dir --label "$Label-$set-$sc" --seg "all:0:$CaptureSeconds" 2>&1 | Out-File (Join-Path $dir 'pc_capture.txt') -Encoding utf8
            uv run python lufs_calibrate.py $wav --seg "all:0:$CaptureSeconds" --current-db $CurrentDb --out $dir --label "$Label-$set-$sc" 2>&1 |
                Tee-Object (Join-Path $dir 'calib.txt')
        } finally { Pop-Location }
    }
}
