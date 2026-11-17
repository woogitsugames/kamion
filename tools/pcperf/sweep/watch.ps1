# pc-budget-s23 watchdog: wait (60 s poll, max 8 h) until no Unity.exe and no build_world.py run, then start run.ps1.
$Main = 'C:\Users\matma\Documents\Claude\kamion'
$Root = Join-Path $Main 'artifacts\pc-budget-s23'
$St = Join-Path $Root 'watch.status'
$Live = Join-Path $Main 'artifacts\live\pc-budget-s23.md'
function S([string]$m) { $l = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m"; Set-Content $St $l; Add-Content $Live "- watch: $l" }
$deadline = (Get-Date).AddHours(8); $idleNeeded = 3; $idle = 0
S "waiting for idle machine (pid $PID, deadline $($deadline.ToString('HH:mm')))"
while ((Get-Date) -lt $deadline) {
    $procs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
    $u = @($procs | Where-Object { $_.Name -ieq 'Unity.exe' }).Count
    $b = @($procs | Where-Object { $_.CommandLine -match 'build_world\.py' }).Count
    if ($u -eq 0 -and $b -eq 0) { $idle++ } else { $idle = 0 }
    Set-Content $St "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') WAITING Unity.exe=$u build_world=$b idle_checks=$idle/$idleNeeded deadline=$($deadline.ToString('HH:mm')) pid=$PID"
    if ($idle -ge $idleNeeded) {
        S "IDLE -> running run.ps1"
        & pwsh -NoProfile -File (Join-Path $Root 'run.ps1') *> (Join-Path $Root 'run.log')
        S "run.ps1 finished exit=$LASTEXITCODE"
        exit 0
    }
    Start-Sleep 60
}
S "TIMEOUT: machine not idle within 8 h - nothing measured"
exit 4
