<#
.SYNOPSIS
  Machine-wide Unity concurrency limit for parallel agent sessions (GPT/Codex, Claude agents).
.DESCRIPTION
  One PC (64 GB RAM, one RTX 5070) runs many worktrees. Each Unity batch process (import, tests, renders, build) takes
  several GB of RAM and the GPU; more than a few at once makes everything slower and can crash imports.
  Before EVERY Unity invocation take a slot, release it right after:
      pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-light-r13      # blocks until a slot is free and no PHONE_RUN
      pwsh scripts/visual-qa.ps1 ...                                  # (any Unity command)
      pwsh scripts/unity-slot.ps1 -Release -Owner gpt-light-r13
  Heavy Python world jobs (build_world.py, build_all.py, pytest tests/gis|physics|gate3, fidelity/run.py) use -Pool heavy:
      pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner gpt-light-r13
      uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c
      pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner gpt-light-r13
  Slots live in the MAIN repo: artifacts/locks/unity-slots/<owner>.slot (works from any worktree).
  A slot older than -StaleHours (default 3 h) is treated as abandoned and removed.
  PHONE_RUN (a phone measurement; Unity kills the adb daemon) blocks new acquisitions.
#>
param(
    [switch]$Acquire,
    [switch]$Release,
    [switch]$Status,
    [string]$Owner = $env:USERNAME,
    # Pool: 'unity' (Unity batch: import, tests, renders, builds; max 4) or 'heavy' (Python world jobs:
    # build_world.py, build_all.py, pytest tests/gis|physics|gate3, fidelity/run.py; max 3 - each takes 1-8 GB and all cores).
    # 2026-11-11: ~13 parallel pytest/build_world runs froze the PC at 100 % CPU / RAM.
    [ValidateSet('unity', 'heavy')] [string]$Pool = 'unity',
    [int]$MaxSlots = 0,
    [double]$StaleHours = 3,
    [int]$PollSeconds = 60,
    # Leader integration: reserve the NEXT free slot of this pool (others wait while a reservation by another owner exists).
    [switch]$Priority
)
$ErrorActionPreference = 'Stop'
$main = 'C:\Users\matma\Documents\Claude\kamion'
if ($MaxSlots -le 0) { $MaxSlots = if ($Pool -eq 'heavy') { 3 } else { 4 } }
$dir = Join-Path $main ("artifacts\locks\{0}-slots" -f $Pool)
$phone = Join-Path $main 'artifacts\locks\PHONE_RUN'
New-Item -ItemType Directory -Force $dir | Out-Null
$safe = ($Owner -replace '[^A-Za-z0-9._-]', '_')
$mine = Join-Path $dir "$safe.slot"
$reserve = Join-Path $dir 'RESERVED.lock'   # content = owner; stale after -StaleHours

function Get-LiveSlots {
    Get-ChildItem $dir -Filter *.slot -ErrorAction SilentlyContinue | ForEach-Object {
        if (((Get-Date) - $_.LastWriteTime).TotalHours -gt $StaleHours) { Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue; Write-Host "removed stale slot $($_.Name)" }
        else { $_ }
    }
}

if ($Status) { Get-LiveSlots | ForEach-Object { "{0}  {1:HH:mm}" -f $_.BaseName, $_.LastWriteTime }; "phone: $(Test-Path $phone)"; exit 0 }

if ($Release) { Remove-Item $mine -Force -ErrorAction SilentlyContinue; "released $safe"; exit 0 }

if ($Acquire) {
    # 2026-11-12 s12: -Priority is honoured ONLY for the leader (owner 'lead-*'); GPT sessions used it in turns and starved
    # Claude agents for 2.5 h. Everyone else waits in a FIFO queue: a waiter may take a free slot only when fewer waiters
    # than free slots have been waiting longer. Tickets: <pool>-slots/queue/<owner>.wait (content = first-wait ticks,
    # LastWriteTime refreshed every poll; a ticket not refreshed for 10 min is dead and ignored/removed).
    $isLead = $safe -like 'lead-*'
    if ($Priority -and -not $isLead) { Write-Host "-Priority ignored for $safe (leader only); using FIFO queue" }
    $qdir = Join-Path $dir 'queue'; New-Item -ItemType Directory -Force $qdir | Out-Null
    $ticket = Join-Path $qdir "$safe.wait"
    $myTicks = if (Test-Path $ticket) { [long](Get-Content $ticket -Raw).Trim() } else { (Get-Date).Ticks }
    try {
        while ($true) {
            if (Test-Path $mine) { (Get-Item $mine).LastWriteTime = Get-Date; Remove-Item $ticket -Force -ErrorAction SilentlyContinue; "slot already held by $safe (refreshed)"; exit 0 }
            "$myTicks" | Set-Content $ticket
            $live = @(Get-LiveSlots)
            $resBy = $null
            if (Test-Path $reserve) {
                if (((Get-Date) - (Get-Item $reserve).LastWriteTime).TotalHours -gt $StaleHours) { Remove-Item $reserve -Force -ErrorAction SilentlyContinue }
                else { $resBy = (Get-Content $reserve -Raw).Trim() }
                if ($resBy -and $resBy -notlike 'lead-*') { Remove-Item $reserve -Force -ErrorAction SilentlyContinue; $resBy = $null }
            }
            if ($Priority -and $isLead -and -not $resBy) { $safe | Set-Content $reserve; $resBy = $safe; Write-Host "reserved next $Pool slot for $safe" }
            $blockedByReserve = $resBy -and $resBy -ne $safe
            $ahead = 0
            if (-not ($isLead -and $resBy -eq $safe)) {
                foreach ($t in Get-ChildItem $qdir -Filter *.wait -ErrorAction SilentlyContinue) {
                    if ($t.FullName -eq $ticket) { continue }
                    if (((Get-Date) - $t.LastWriteTime).TotalMinutes -gt 10) { Remove-Item $t.FullName -Force -ErrorAction SilentlyContinue; continue }
                    $tt = 0L; [void][long]::TryParse((Get-Content $t.FullName -Raw -ErrorAction SilentlyContinue), [ref]$tt)
                    if ($tt -gt 0 -and $tt -lt $myTicks) { $ahead++ }
                }
            }
            $free = $MaxSlots - $live.Count
            # PHONE_RUN blocks only the Unity pool (Unity kills the adb daemon); heavy Python jobs do not touch adb.
            $phoneBlocks = ($Pool -eq 'unity') -and (Test-Path $phone)
            if (-not $phoneBlocks -and -not $blockedByReserve -and $free -gt 0 -and $ahead -lt $free) {
                "$safe $(Get-Date -Format o)" | Set-Content $mine
                Start-Sleep -Milliseconds (Get-Random -Minimum 200 -Maximum 900)   # settle a race between two acquirers
                if (@(Get-LiveSlots).Count -le $MaxSlots) {
                    if ($resBy -eq $safe) { Remove-Item $reserve -Force -ErrorAction SilentlyContinue }
                    Remove-Item $ticket -Force -ErrorAction SilentlyContinue
                    "acquired slot $safe ($($live.Count + 1)/$MaxSlots)"; exit 0 }
                Remove-Item $mine -Force
            }
            Write-Host ("waiting for a {3} slot ({0}/{1} busy, phone={2}, reserved={4}, queue ahead={5}) ..." -f $live.Count, $MaxSlots, (Test-Path $phone), $Pool, $resBy, $ahead)
            Start-Sleep -Seconds $PollSeconds
        }
    } finally { Remove-Item $ticket -Force -ErrorAction SilentlyContinue }
}
Write-Host 'use -Acquire, -Release or -Status'; exit 2
