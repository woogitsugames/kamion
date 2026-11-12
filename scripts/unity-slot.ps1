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
    [int]$PollSeconds = 60
)
$ErrorActionPreference = 'Stop'
$main = 'C:\Users\matma\Documents\Claude\kamion'
if ($MaxSlots -le 0) { $MaxSlots = if ($Pool -eq 'heavy') { 3 } else { 4 } }
$dir = Join-Path $main ("artifacts\locks\{0}-slots" -f $Pool)
$phone = Join-Path $main 'artifacts\locks\PHONE_RUN'
New-Item -ItemType Directory -Force $dir | Out-Null
$safe = ($Owner -replace '[^A-Za-z0-9._-]', '_')
$mine = Join-Path $dir "$safe.slot"

function Get-LiveSlots {
    Get-ChildItem $dir -Filter *.slot -ErrorAction SilentlyContinue | ForEach-Object {
        if (((Get-Date) - $_.LastWriteTime).TotalHours -gt $StaleHours) { Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue; Write-Host "removed stale slot $($_.Name)" }
        else { $_ }
    }
}

if ($Status) { Get-LiveSlots | ForEach-Object { "{0}  {1:HH:mm}" -f $_.BaseName, $_.LastWriteTime }; "phone: $(Test-Path $phone)"; exit 0 }

if ($Release) { Remove-Item $mine -Force -ErrorAction SilentlyContinue; "released $safe"; exit 0 }

if ($Acquire) {
    while ($true) {
        if (Test-Path $mine) { (Get-Item $mine).LastWriteTime = Get-Date; "slot already held by $safe (refreshed)"; exit 0 }
        $live = @(Get-LiveSlots)
        if (-not (Test-Path $phone) -and $live.Count -lt $MaxSlots) {
            "$safe $(Get-Date -Format o)" | Set-Content $mine
            Start-Sleep -Milliseconds (Get-Random -Minimum 200 -Maximum 900)   # settle a race between two acquirers
            if (@(Get-LiveSlots).Count -le $MaxSlots) { "acquired slot $safe ($($live.Count + 1)/$MaxSlots)"; exit 0 }
            Remove-Item $mine -Force
        }
        Write-Host ("waiting for a {3} slot ({0}/{1} busy, phone={2}) ..." -f $live.Count, $MaxSlots, (Test-Path $phone), $Pool)
        Start-Sleep -Seconds $PollSeconds
    }
}
Write-Host 'use -Acquire, -Release or -Status'; exit 2
