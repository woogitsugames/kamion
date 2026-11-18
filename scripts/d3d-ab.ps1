# D3D11 vs D3D12 (DRAFT-d3d11 §4): pc-metrics High60 (klasa zalecany) i bez limitu, przeplatane, + cykle start/wyjście.
param([Parameter(Mandatory)][string]$Exe, [int]$Reps = 2, [int]$QuitCycles = 3, [string]$Repo = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\win-build', [string]$Out = 'C:\Users\matma\Documents\Claude\kamion\artifacts\d3d-ab')
$A = $Out
New-Item -ItemType Directory -Force $A | Out-Null
$st = "$A\d3d-ab.status"
function Log($m) { "$(Get-Date -f s) $m" | Out-File "$A\d3d-ab.log" -Append; "RUNNING $m" | Out-File $st }
function Busy { @(Get-Process Unity, Kamion -ErrorAction SilentlyContinue).Count }
Set-Location $Repo
try {
    for ($r = 1; $r -le $Reps; $r++) {
        foreach ($api in @('d3d12', 'd3d11')) {
            foreach ($cfg in @(@{n = 'high60'; fps = 60; cls = 'zalecany'}, @{n = 'uncapped'; fps = 1000; cls = ''})) {
                $label = "$api-$($cfg.n)-r$r"
                $pre = Busy
                $args = @('-NoProfile', '-File', 'scripts/pc-metrics.ps1', '-Exe', $Exe, '-Scene', 'knyszyn', '-Tier', 'High', '-Fps', $cfg.fps,
                    '-VSync', '0', '-Width', '1920', '-Height', '1080', '-DurationSeconds', '90', '-Label', $label,
                    '-OutDir', "$A\$label", '-Extra', "force-$api,stream=1,autopilot=route,speed=50")
                if ($cfg.cls) { $args += @('-Class', $cfg.cls) }
                pwsh @args *> "$A\$label.out"
                $c = $LASTEXITCODE
                $post = @(Get-Process Unity -ErrorAction SilentlyContinue).Count
                Log "$label exit=$c unity_before=$pre unity_after=$post"
            }
        }
    }
    foreach ($api in @('d3d12', 'd3d11')) {
        for ($i = 1; $i -le $QuitCycles; $i++) {
            $log = "$A\$api-quit$i.log"
            $p = Start-Process $Exe -ArgumentList "-force-$api", '-scene', 'knyszyn', '-screen-width', '1920', '-screen-height', '1080', '-screen-fullscreen', '0', '-quit_t', '30', '-logFile', $log -PassThru
            $null = $p.Handle
            if (-not $p.WaitForExit(180000)) { $p.Kill(); $ec = 'timeout' } else { $ec = $p.ExitCode }
            $crash = (Select-String -Path $log -Pattern 'Crash!!!|Received signal|Device failed|887a|access violation' -Quiet)
            Log "$api-quit$i exit=$ec crashMarker=$crash"
            Start-Sleep 5
        }
    }
    "D3D_DONE" | Out-File $st
} catch { Log "ERROR $_"; "D3D_DONE error" | Out-File $st }
