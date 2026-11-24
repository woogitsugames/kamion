<#
.SYNOPSIS
  ADR 0345: record a whole autopilot drive (default Bialystok C -> Tykocin) as a YouTube-ready MP4 with the game's own
  sound: the player records its audio output (-record_audio, no WASAPI loopback / "Stereo Mix" on the dev PC), ffmpeg
  records the screen, the script stops both after "Cel osiagniety" and muxes video + WAV with the offset from the clocks.
.EXAMPLE
  pwsh scripts/record-drive.ps1 -Exe artifacts/win/kamion-0.1.0-<sha>-regions/Kamion.exe            # full drive (~60 min)
  pwsh scripts/record-drive.ps1 -Exe <Kamion.exe> -MaxSeconds 150 -Out artifacts/recorder-s24/test    # short test
  pwsh scripts/record-drive.ps1 -Exe <build #7> -LegacyAudioCapture -MaxSeconds 150                   # build before ADR 0345
.NOTES
  Player: borderless 1920x1080, High, -fps 60, -autopilot route -speed 50 -stream 1 -route_to tykocin -nav_log 5
  -record_audio <Out>/audio.wav; Windows power throttling switched off for the player (scripts/set-power-throttling.ps1,
  ADR 0333). Video: ddagrab (Desktop Duplication) of monitor -Monitor, encoder probed in the order h264_nvenc ->
  h264_mf (NVIDIA H.264 Encoder MFT; nvenc of ffmpeg 9 needs driver >= 610) -> libx264; 60 fps CFR, ~40 Mb/s, High
  profile; written to video.mkv (survives a crash). The recording starts after the first [NAV] status line (world
  loaded) + -StartDelaySeconds and stops -AfterArrivalSeconds after "[NAV] arrived" (or the last-leg status line with
  remaining <= 20 m, builds before ADR 0345), BEFORE the player is closed, so neither the loading desktop nor the
  desktop after quit is in the video. Do not use the PC during the drive: ddagrab records the screen, a window on top of
  the game would be in the video (the script brings the game back to the front every 30 s and logs it).
  Sync: video first frame = ffmpeg wallclock start (input "start:" of -use_wallclock_as_timestamps), audio sample 0 =
  firstBlockUtc of <wav>.sync.json; offset = audio - video (adelay / atrim). Drives >= 10 min also correct the sound
  card clock drift (asetrate from frames vs UTC). Result: <Out>/<Name>.mp4 (H.264 copy + AAC 320k, faststart) +
  sync.log / sync.json. Exit 0 = arrived and MP4 written, 2 = MP4 written without arrival (max time), 3 = failed.
#>
param(
    [Parameter(Mandatory)][string]$Exe,
    [string]$Scene = 'bialystok-industrial-c',
    [string]$RouteTo = 'tykocin',
    [string]$Speed = '50',
    [ValidateSet('Low', 'Medium', 'High', 'Ultra')] [string]$Tier = 'High',
    [int]$Fps = 60,
    [int]$Width = 1920,
    [int]$Height = 1080,
    [string]$Out = '',
    [string]$Name = 'kamion-bialystok-tykocin-1080p60',
    [int]$MaxSeconds = 5400,            # recording watchdog (C -> Tykocin took ~3460 s in build #6)
    [int]$LoadTimeoutSeconds = 600,
    [int]$StartDelaySeconds = 3,
    [int]$AfterArrivalSeconds = 10,
    [int]$Monitor = 0,                  # ddagrab output_idx
    [ValidateSet('auto', 'h264_nvenc', 'h264_mf', 'libx264')] [string]$Encoder = 'auto',
    [string]$VideoBitrate = '40M',
    [int]$Cq = 19,                      # h264_nvenc constant quality / libx264 crf
    [ValidateSet('float', 'pcm16')] [string]$AudioFormat = 'float',
    [string]$AudioBitrate = '320k',
    # Final MP4 video: 'auto' = copy when the capture already used h264_nvenc (CQ), else re-encode offline with libx264
    # (-FinalPreset/-FinalCrf, CPU after the drive, nothing competes with the game); 'copy' / 'x264' force one.
    [ValidateSet('auto', 'copy', 'x264')] [string]$FinalVideo = 'auto',
    [string]$FinalPreset = 'slow',
    [int]$FinalCrf = 18,
    [switch]$LegacyAudioCapture,        # builds before ADR 0345: -audio_capture (whole buffer in RAM, written at quit, sync +-0.5 s)
    [switch]$NoRefocus,
    [switch]$NoPowerThrottlingOptOut,
    [string]$FFmpeg = '',
    [string[]]$ExtraPlayerArgs = @()
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
$ci = [Globalization.CultureInfo]::InvariantCulture
$ts = Get-Timestamp
if (-not $Out) { $Out = Join-Path $ArtifactsDir "record/$ts" }
New-Item -ItemType Directory -Force $Out | Out-Null
$Out = (Resolve-Path $Out).Path
$exePath = (Resolve-Path $Exe).Path
$syncLog = Join-Path $Out 'sync.log'
function Log([string]$m) { $l = "$((Get-Date).ToString('HH:mm:ss')) $m"; Write-Host $l; Add-Content -LiteralPath $syncLog -Value $l -Encoding utf8 }

# ---------------------------------------------------------------- ffmpeg + encoder
if (-not $FFmpeg) { $FFmpeg = $env:KAMION_FFMPEG }
if (-not $FFmpeg) { $c = Get-Command ffmpeg -ErrorAction SilentlyContinue; if ($c) { $FFmpeg = $c.Source } }
if (-not $FFmpeg) {
    $FFmpeg = Get-ChildItem "$env:LOCALAPPDATA/Microsoft/WinGet/Packages" -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $FFmpeg -or -not (Test-Path $FFmpeg)) { throw 'ffmpeg not found (-FFmpeg, KAMION_FFMPEG, PATH or winget Gyan.FFmpeg)' }
$FFprobe = Join-Path (Split-Path $FFmpeg -Parent) 'ffprobe.exe'

function Invoke-FF([string]$exe, [string[]]$a) {
    $psi = [Diagnostics.ProcessStartInfo]::new($exe)
    foreach ($x in $a) { $psi.ArgumentList.Add($x) }
    $psi.UseShellExecute = $false; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true; $psi.CreateNoWindow = $true
    $p = [Diagnostics.Process]::Start($psi)
    $errTask = $p.StandardError.ReadToEndAsync()
    $o = $p.StandardOutput.ReadToEnd(); $p.WaitForExit()
    return @{ Code = $p.ExitCode; Out = $o; Err = $errTask.Result }
}

# encoder arguments for ddagrab's D3D11 frames (bgra); the MF and x264 paths download and convert to nv12 / yuv420p
$encoders = [ordered]@{
    h264_nvenc = @('-c:v', 'h264_nvenc', '-preset', 'p5', '-tune', 'hq', '-rc', 'vbr', '-cq', "$Cq", '-b:v', '0',
                   '-maxrate', '60M', '-bufsize', '120M', '-profile:v', 'high', '-g', '120', '-bf', '2')
    h264_mf    = @('-vf', 'hwdownload,format=bgra,format=nv12', '-c:v', 'h264_mf', '-hw_encoding', '1', '-profile:v', '100',
                   '-rate_control', 'u_vbr', '-b:v', $VideoBitrate, '-g', '120')
    libx264    = @('-vf', 'hwdownload,format=bgra,format=yuv420p', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', "$Cq",
                   '-profile:v', 'high', '-g', '120')
}
$order = if ($Encoder -eq 'auto') { @($encoders.Keys) } else { @($Encoder) }
$enc = $null
foreach ($e in $order) {
    $probeArgs = @('-hide_banner', '-v', 'error', '-f', 'lavfi', '-i', "ddagrab=output_idx=${Monitor}:framerate=${Fps}:draw_mouse=0",
        '-frames:v', '3') + $encoders[$e] + @('-f', 'null', '-')
    $r = Invoke-FF $FFmpeg $probeArgs
    if ($r.Code -eq 0) { $enc = $e; break }
    Log "encoder $e unavailable: $((@($r.Err -split "`n") | Where-Object { $_ -match '\S' } | Select-Object -First 2) -join ' | ')"
}
if (-not $enc) { Log 'FAIL: no working encoder with ddagrab'; exit 3 }
Log "ffmpeg $FFmpeg, capture ddagrab output_idx=$Monitor, encoder $enc"

# ---------------------------------------------------------------- player
$wav = Join-Path $Out 'audio.wav'
$video = Join-Path $Out 'video.mkv'
$playerLog = Join-Path $Out 'player.log'
foreach ($f in @($wav, "$wav.sync.json", $video, $playerLog)) { Remove-Item -LiteralPath $f -ErrorAction SilentlyContinue }
$playerArgs = @('-screen-fullscreen', '1', '-window-mode', 'borderless', '-screen-width', "$Width", '-screen-height', "$Height",
    '-logFile', $playerLog, '-tier', $Tier, '-fps', "$Fps", '-scene', $Scene, '-autopilot', 'route', '-speed', $Speed,
    '-stream', '1', '-route_to', $RouteTo, '-nav_log', '5', '-quit_t', "$($MaxSeconds + $LoadTimeoutSeconds + 300)")
if ($LegacyAudioCapture) {
    $playerArgs += @('-audio_capture', $wav, '-audio_capture_t0', '0', '-audio_capture_s', "$($MaxSeconds + $LoadTimeoutSeconds + 120)")
} else {
    $playerArgs += @('-record_audio', $wav, '-record_audio_format', $AudioFormat)
}
$playerArgs += $ExtraPlayerArgs
Log "player: $exePath $($playerArgs -join ' ')"
$playerStartUtc = [DateTime]::UtcNow
$p = Start-Process -FilePath $exePath -ArgumentList $playerArgs -PassThru
$null = $p.Handle
if (-not $NoPowerThrottlingOptOut) {
    $pt = & pwsh -NoProfile -File (Join-Path $PSScriptRoot 'set-power-throttling.ps1') -TargetPid $p.Id -Mode Off 2>&1
    Log "$pt"
}

Add-Type -Namespace KamionRec -Name Win -MemberDefinition @'
[DllImport("user32.dll")] public static extern System.IntPtr GetForegroundWindow();
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(System.IntPtr h);
[DllImport("user32.dll")] public static extern bool ShowWindow(System.IntPtr h, int cmd);
[DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, System.UIntPtr extra);
'@ -ErrorAction SilentlyContinue
function Get-GameWindow { $p.Refresh(); return $p.MainWindowHandle }
function Set-GameFront {
    $h = Get-GameWindow
    if ($h -eq [IntPtr]::Zero) { return $false }
    if ([KamionRec.Win]::GetForegroundWindow() -eq $h) { return $true }
    [KamionRec.Win]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero); [KamionRec.Win]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero)  # ALT: lets SetForegroundWindow through
    [void][KamionRec.Win]::ShowWindow($h, 9)
    [void][KamionRec.Win]::SetForegroundWindow($h)
    Start-Sleep -Milliseconds 300
    return ([KamionRec.Win]::GetForegroundWindow() -eq $h)
}

# incremental reader of the live player log
$script:logPos = 0L
function Read-NewLog {
    if (-not (Test-Path -LiteralPath $playerLog)) { return @() }
    try {
        $fs = [IO.FileStream]::new($playerLog, 'Open', 'Read', 'ReadWrite')
        try {
            if ($fs.Length -le $script:logPos) { return @() }
            $fs.Seek($script:logPos, 'Begin') | Out-Null
            $sr = [IO.StreamReader]::new($fs, [Text.Encoding]::UTF8)
            $txt = $sr.ReadToEnd()
            $cut = $txt.LastIndexOf("`n")
            if ($cut -lt 0) { return @() }
            $script:logPos += [Text.Encoding]::UTF8.GetByteCount($txt.Substring(0, $cut + 1))
            return @($txt.Substring(0, $cut) -split "`r?`n")
        } finally { $fs.Dispose() }
    } catch { return @() }
}
$reArrived = '\[NAV\] arrived t='
$reLastLeg = '\[NAV\] status t=\d+s tile=\S+ trip=\S+ leg=(\d+)/(\d+) route=True onRoute=True remaining=(\d+) m'
function Test-Arrived([string]$line) {
    if ($line -match $reArrived) { return $true }
    if ($line -match $reLastLeg -and $Matches[1] -eq $Matches[2] -and [int]$Matches[3] -le 20) { return $true }
    return $false
}

# ---------------------------------------------------------------- wait for the world
$sw = [Diagnostics.Stopwatch]::StartNew()
$loaded = $false; $arrived = $false
while ($sw.Elapsed.TotalSeconds -lt $LoadTimeoutSeconds) {
    if ($p.HasExited) { break }
    foreach ($l in (Read-NewLog)) {
        if ($l -match '^\[BOOT\] Kamion|\[RECORD\]|\[AUDIO-PC\] capture|\[START\] region') { Log "  player: $($l.Trim())" }
        if ($l -match '^\[NAV\] status t=') { $loaded = $true }
        if (Test-Arrived $l) { $arrived = $true }
    }
    if ($loaded) { break }
    Start-Sleep -Milliseconds 500
}
if (-not $loaded) {
    Log "FAIL: no [NAV] status line within $LoadTimeoutSeconds s (player exited=$($p.HasExited))"
    if (-not $p.HasExited) { $p.Kill() }
    exit 3
}
Log "world loaded after $([int]$sw.Elapsed.TotalSeconds) s; foreground=$(Set-GameFront)"
Start-Sleep -Seconds $StartDelaySeconds
if (-not $NoRefocus) { [void](Set-GameFront) }

# ---------------------------------------------------------------- record
$ffArgs = @('-hide_banner', '-y', '-use_wallclock_as_timestamps', '1', '-f', 'lavfi', '-i',
    "ddagrab=output_idx=${Monitor}:framerate=${Fps}:draw_mouse=0") + $encoders[$enc] +
    @('-fps_mode', 'cfr', '-r', "$Fps", '-metadata', "title=$Name", '-f', 'matroska', $video)
$psi = [Diagnostics.ProcessStartInfo]::new($FFmpeg)
foreach ($x in $ffArgs) { $psi.ArgumentList.Add($x) }
$psi.UseShellExecute = $false; $psi.RedirectStandardInput = $true; $psi.RedirectStandardError = $true; $psi.CreateNoWindow = $true; $psi.WorkingDirectory = $Out
$psi.Environment['FFREPORT'] = 'file=ffmpeg.log:level=32'
$ff = [Diagnostics.Process]::Start($psi)
$null = $ff.StandardError.BaseStream.CopyToAsync([IO.Stream]::Null)   # progress lines: the full log is FFREPORT ffmpeg.log
$recStartUtc = [DateTime]::UtcNow
Log "ffmpeg pid $($ff.Id) started (report $Out\ffmpeg.log)"
$recSw = [Diagnostics.Stopwatch]::StartNew()
$reason = 'max'; $nextFront = 30; $notFront = 0
while ($true) {
    foreach ($l in (Read-NewLog)) {
        if ($l -match '^\[RECORD\]|^\[NAV\] arrived') { Log "  player: $($l.Trim())" }
        if (Test-Arrived $l) { $arrived = $true }
    }
    if ($arrived) { $reason = 'arrived'; break }
    if ($p.HasExited) { $reason = "player exited ($($p.ExitCode))"; break }
    if ($ff.HasExited) { $reason = "ffmpeg exited ($($ff.ExitCode))"; break }
    if ($recSw.Elapsed.TotalSeconds -ge $MaxSeconds) { $reason = 'max'; break }
    if ($recSw.Elapsed.TotalSeconds -ge $nextFront) {
        $nextFront += 30
        $h = Get-GameWindow
        if ($h -ne [IntPtr]::Zero -and [KamionRec.Win]::GetForegroundWindow() -ne $h) {
            $notFront++
            $ok = if ($NoRefocus) { $false } else { Set-GameFront }
            Log "WARNING: game not in front at $([int]$recSw.Elapsed.TotalSeconds) s (refocus=$ok) - another window may be in the video"
        }
    }
    Start-Sleep -Seconds 2
}
Log "stop: $reason after $([int]$recSw.Elapsed.TotalSeconds) s of video"
if ($reason -eq 'arrived' -and $AfterArrivalSeconds -gt 0) { Start-Sleep -Seconds $AfterArrivalSeconds }

# video first (the desktop after quit must not be in it), then the player (its OnApplicationQuit closes the WAV)
if (-not $ff.HasExited) {
    try { $ff.StandardInput.Write('q'); $ff.StandardInput.Flush() } catch { }
    if (-not $ff.WaitForExit(30000)) { Log 'ffmpeg did not stop on q within 30 s - killed (MKV stays readable)'; $ff.Kill(); $ff.WaitForExit() }
}
Log "ffmpeg exit $($ff.ExitCode)"
if (-not $p.HasExited) {
    [void]$p.CloseMainWindow()
    if (-not $p.WaitForExit(90000)) { Log 'player did not quit within 90 s - killed (WAV valid up to its last checkpoint)'; $p.Kill(); $p.WaitForExit() }
}
Log "player exit $($p.ExitCode)"
foreach ($l in (Read-NewLog)) { if ($l -match '^\[RECORD\]|\[AUDIO-PC\] capture') { Log "  player: $($l.Trim())" } }

# ---------------------------------------------------------------- sync
$ffLog = Join-Path $Out 'ffmpeg.log'
$vStart = $null
if (Test-Path $ffLog) {
    $m = Select-String -LiteralPath $ffLog -Pattern 'Duration: N/A, start: (\d+\.\d+)' | Select-Object -First 1
    if ($m) { $vStart = [double]::Parse($m.Matches[0].Groups[1].Value, $ci) }
}
if (-not $vStart) { $vStart = ([DateTimeOffset]$recStartUtc).ToUnixTimeMilliseconds() / 1000.0; Log 'WARNING: no wallclock start in ffmpeg.log - using the script clock (+-0.5 s)' }
if (-not (Test-Path $wav) -or (Get-Item $wav).Length -lt 1000) { Log "FAIL: no audio at $wav"; exit 3 }
$rate = 48000; $drift = 0.0; $syncNote = ''
if ($LegacyAudioCapture) {
    # -audio_capture starts at realtimeSinceStartup t0; the player clock starts ~process start (approximate)
    $m = Select-String -LiteralPath $playerLog -Pattern '\[AUDIO-PC\] capture start t=(\d+\.\d+)' | Select-Object -First 1
    $rt = if ($m) { [double]::Parse($m.Matches[0].Groups[1].Value, $ci) } else { 0.0 }
    $p0 = ([DateTimeOffset]$p.StartTime.ToUniversalTime()).ToUnixTimeMilliseconds() / 1000.0
    $aStart = $p0 + $rt
    $syncNote = 'legacy -audio_capture: audio start = process start + realtime of [AUDIO-PC] capture start (approximate, +-0.5 s)'
} else {
    $sj = Get-Content -LiteralPath "$wav.sync.json" -Raw | ConvertFrom-Json
    $rate = [int]$sj.sampleRate
    $fb = [DateTimeOffset]::Parse("$($sj.firstBlockUtc)", $ci, [Globalization.DateTimeStyles]::AssumeUniversal)
    $aStart = $fb.ToUnixTimeMilliseconds() / 1000.0 + ($fb.Ticks % 10000) / 1e7
    $lp = [DateTimeOffset]::Parse("$($sj.lastPushUtc)", $ci, [Globalization.DateTimeStyles]::AssumeUniversal)
    $span = ($lp - $fb).TotalSeconds
    if ($span -ge 600) {
        $measured = [double]$sj.lastPushFramesStart / $span
        $drift = ($measured / $rate - 1.0) * 1e6
    }
    $syncNote = "record_audio: firstBlockUtc $($sj.firstBlockUtc), frames $($sj.framesWritten), dropped $($sj.droppedSamples), zeroFilled $($sj.zeroFilledSamples), closed $($sj.closed)"
}
$offset = $aStart - $vStart          # > 0: audio starts after the first video frame
Log ([string]::Format($ci, "sync: video first frame {0:F3}, audio sample 0 {1:F3} (unix s) -> offset {2:+0.000;-0.000} s; drift {3:F1} ppm; {4}", $vStart, $aStart, $offset, $drift, $syncNote))

# ---------------------------------------------------------------- mux
$af = @()
if ([Math]::Abs($drift) -ge 5) { $af += "asetrate=$([Math]::Round($rate * (1 + $drift / 1e6)))" }
$af += "aresample=48000"
if ($offset -gt 0.0005) { $af += ("adelay=delays={0}:all=1" -f [Math]::Round($offset * 1000)) }
elseif ($offset -lt -0.0005) { $af += ("atrim=start={0},asetpts=PTS-STARTPTS" -f (-$offset).ToString('F4', $ci)) }
$af += 'apad'
$mp4 = Join-Path $Out "$Name.mp4"
$finalMode = if ($FinalVideo -ne 'auto') { $FinalVideo } elseif ($enc -eq 'h264_nvenc') { 'copy' } else { 'x264' }
$vOut = if ($finalMode -eq 'copy') { @('-c:v', 'copy') } else {
    @('-c:v', 'libx264', '-preset', $FinalPreset, '-crf', "$FinalCrf", '-profile:v', 'high', '-pix_fmt', 'yuv420p',
      '-g', "$($Fps * 2)", '-bf', '2', '-x264-params', 'keyint_min=30', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709')
}
Log "final video: $finalMode$(if ($finalMode -eq 'x264') { " (libx264 $FinalPreset crf $FinalCrf, offline)" })"
$muxSw = [Diagnostics.Stopwatch]::StartNew()
$muxArgs = @('-hide_banner', '-y', '-i', $video, '-i', $wav, '-filter_complex', "[1:a]$($af -join ',')[a]",
    '-map', '0:v:0', '-map', '[a]') + $vOut + @('-c:a', 'aac', '-b:a', $AudioBitrate, '-ar', '48000', '-shortest',
    '-movflags', '+faststart', '-metadata', "title=$Name", $mp4)
Log "mux: ffmpeg $($muxArgs -join ' ')"
$r = Invoke-FF $FFmpeg $muxArgs
$r.Err | Set-Content (Join-Path $Out 'mux.log') -Encoding utf8
if ($r.Code -ne 0 -or -not (Test-Path $mp4)) { Log "FAIL: mux exit $($r.Code) (mux.log)"; exit 3 }
Log ("mux took {0:F0} s" -f $muxSw.Elapsed.TotalSeconds)
$pr = Invoke-FF $FFprobe @('-v', 'error', '-show_entries', 'format=duration,size,bit_rate:stream=codec_name,width,height,r_frame_rate,sample_rate,channels', '-of', 'json', $mp4)
$info = $pr.Out | ConvertFrom-Json
$vs = $info.streams | Where-Object { $_.codec_name -eq 'h264' } | Select-Object -First 1
# (comma binds tighter than / in PowerShell: every computed argument is precomputed)
$durS = [double]$info.format.duration; $sizeMB = [double]$info.format.size / 1MB; $mbps = [double]$info.format.bit_rate / 1e6
$aDesc = (($info.streams | Where-Object { $_.codec_name -eq 'aac' } | ForEach-Object { "aac $($_.sample_rate) Hz $($_.channels) ch" }) -join '')
Log ([string]::Format($ci, 'MP4 {0}: {1:F1} s, {2:F0} MB, {3:F1} Mb/s, video {4}x{5} {6}, audio {7}', $mp4, $durS, $sizeMB, $mbps,
    $vs.width, $vs.height, $vs.r_frame_rate, $aDesc))
[ordered]@{
    exe = $exePath; scene = $Scene; routeTo = $RouteTo; tier = $Tier; fps = $Fps; encoder = $enc; monitor = $Monitor
    reason = $reason; arrived = $arrived; notInFrontWarnings = $notFront
    playerStartUtc = $playerStartUtc.ToString('o'); recordStartUtc = $recStartUtc.ToString('o')
    videoFirstFrameUnix = $vStart; audioSample0Unix = $aStart; offsetSeconds = [Math]::Round($offset, 4); driftPpm = [Math]::Round($drift, 1)
    audioFilter = ($af -join ','); syncNote = $syncNote; legacyAudio = [bool]$LegacyAudioCapture; finalVideo = $finalMode; muxSeconds = [int]$muxSw.Elapsed.TotalSeconds
    mp4 = $mp4; durationSeconds = [double]$info.format.duration; sizeBytes = [long]$info.format.size
} | ConvertTo-Json | Set-Content (Join-Path $Out 'sync.json') -Encoding utf8
if ($reason -eq 'arrived') { Log 'OK: arrived, MP4 written'; exit 0 }
Log "MP4 written without arrival ($reason)"; exit 2
