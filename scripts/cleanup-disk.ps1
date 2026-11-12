<#
.SYNOPSIS
  Free disk space safely: removes merged agent worktrees, clears Unity Library caches
  of idle worktrees, prunes old APKs. Never touches main's data, active agents or git history.

.DESCRIPTION
  1. Worktree whose branch is merged into main and no running process uses it:
     copy missing artifacts to main, unlink Data/raw junctions, git worktree remove.
  2. Unmerged worktree, no running process, last commit older than -IdleHours:
     delete only game/Library (Unity cache, rebuilt on next open).
  3. artifacts/apk: keep the newest -KeepApks .apk files; older .apk deleted (their .sha256/.json/.txt kept).
  Run with -WhatIf to only list what would be removed.

.EXAMPLE
  pwsh scripts/cleanup-disk.ps1
  pwsh scripts/cleanup-disk.ps1 -WhatIf
#>
param(
    [switch]$WhatIf,
    [int]$IdleHours = 2,
    [int]$KeepApks = 6
)
$ErrorActionPreference = 'Continue'
$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo
function Free { '{0:N1}' -f ((Get-PSDrive ($repo.Substring(0, 1))).Free / 1GB) }
function Log($m) { "$(Get-Date -f HH:mm:ss) $m" }
Log "start free=$(Free) GB  WhatIf=$WhatIf"

# Worktrees used by running processes (Unity, python, pwsh, bash, dotnet, java/gradle)
$busy = @{}
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'worktrees[\\/]([^\\/ "'']+)' } | ForEach-Object { $busy[$matches[1]] = $true }

$wts = @(); $cur = $null
foreach ($line in (git worktree list --porcelain)) {
    if ($line -like 'worktree *') { $cur = @{ path = $line.Substring(9) -replace '/', '\' } ; $wts += $cur }
    elseif ($line -like 'branch *') { $cur.branch = $line.Substring(7) -replace '^refs/heads/', '' }
}
$mainPath = (Resolve-Path $repo).Path
foreach ($w in $wts) {
    $p = $w.path
    if ($p -eq $mainPath -or $p -notmatch '\\\.claude\\worktrees\\') { continue }
    $name = Split-Path $p -Leaf
    if ($busy[$name]) { Log "keep   $name (process running)"; continue }
    $merged = $false
    if ($w.branch) { git merge-base --is-ancestor $w.branch main 2>$null; $merged = ($LASTEXITCODE -eq 0) }
    if ($merged) {
        if ($WhatIf) { Log "WOULD remove merged worktree $name"; continue }
        $lib = Join-Path $p 'game\Library'
        if (Test-Path $lib) { cmd /c rmdir /s /q "`"$lib`"" }
        $art = Join-Path $p 'artifacts'
        if (Test-Path $art) { robocopy $art (Join-Path $repo 'artifacts') /E /XC /XN /XO /XF *.pkl /XD locks live /NFL /NDL /NJH /NJS /NP | Out-Null }
        Get-ChildItem (Join-Path $p 'Data\raw') -Force -ErrorAction SilentlyContinue | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint } | ForEach-Object { cmd /c rmdir "`"$($_.FullName)`"" }
        $left = Get-ChildItem (Join-Path $p 'Data\raw') -Force -ErrorAction SilentlyContinue | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }
        if ($left) { Log "SKIP   $name (junction still present)"; continue }
        git worktree remove --force --force $p
        Log "removed merged worktree $name  free=$(Free)"
    } else {
        $lib = Join-Path $p 'game\Library'
        if (-not (Test-Path $lib)) { continue }
        $last = git -C $p log -1 --format=%ct 2>$null
        $ageH = if ($last) { ((Get-Date) - [DateTimeOffset]::FromUnixTimeSeconds([long]$last).LocalDateTime).TotalHours } else { 999 }
        if ($ageH -lt $IdleHours) { Log "keep   $name (active: last commit $([int]($ageH*60)) min ago)"; continue }
        if ($WhatIf) { Log "WOULD clear Library of idle unmerged $name"; continue }
        cmd /c rmdir /s /q "`"$lib`""
        Log "cleared Library of $name (unmerged, kept)  free=$(Free)"
    }
}
git worktree prune

# Old APKs
$apkDir = Join-Path $repo 'artifacts\apk'
$apks = Get-ChildItem $apkDir -Filter *.apk -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
foreach ($a in ($apks | Select-Object -Skip $KeepApks)) {
    # only the .apk itself; .sha256/.content.json/.top.txt stay as the record (rebuildable from the sha)
    if ($WhatIf) { Log "WOULD delete $($a.Name)"; continue }
    Remove-Item $a.FullName -Force
}
if (-not $WhatIf -and $apks.Count -gt $KeepApks) { Log "deleted $($apks.Count - $KeepApks) old APKs (kept newest $KeepApks)" }
Log "done free=$(Free) GB"
