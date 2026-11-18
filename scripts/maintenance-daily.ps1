# Codzienne sprzątanie dysku Kamiona (s23, 17.11.2026 — po tym, jak worktree zapchały dysk do 122 GB wolnego).
# Użycie: pwsh scripts/maintenance-daily.ps1 [-WhatIf]
# Uruchamiaj raz dziennie (zadanie zaplanowane / cron sesji) i zawsze, gdy wolne < 150 GB.
# NIGDY nie rusza: Data/raw w main, .git, worktree z działającym procesem, worktree buildowego (win-build-*),
# artifacts/live, artifacts/logs, dwóch najnowszych buildów w artifacts/win.
param([switch]$WhatIf)
$ErrorActionPreference = 'Continue'
$Repo = (Resolve-Path "$PSScriptRoot/..").Path
$drive = $Repo.Substring(0, 1)
function Free { [math]::Round((Get-PSDrive $drive).Free / 1GB) }
$log = Join-Path $Repo 'artifacts\logs\maintenance.log'
New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null
function L($m) { $t = "$(Get-Date -Format s) $m"; $t | Add-Content $log; Write-Host $t }
function Del($path, $why) {
    if ($WhatIf) { L "WHATIF del $path ($why)"; return }
    # bezpiecznik: nie wchodzimy w junctiony
    Get-ChildItem $path -Recurse -Force -Attributes ReparsePoint -EA SilentlyContinue | ForEach-Object { [System.IO.Directory]::Delete($_.FullName) }
    Remove-Item $path -Recurse -Force -EA SilentlyContinue
    L "del $path ($why) ok=$(-not (Test-Path $path))"
}
$before = Free
L "START free=$before GB WhatIf=$WhatIf"

# 1) Scalone worktree agentów + Library bezczynnych (istniejący skrypt)
if ($WhatIf) { pwsh -NoProfile -File "$Repo\scripts\cleanup-disk.ps1" -WhatIf } else { pwsh -NoProfile -File "$Repo\scripts\cleanup-disk.ps1" }

# 2) Stare buildy: zostaw 2 najnowsze katalogi w artifacts\win (bez runs/)
$wins = Get-ChildItem "$Repo\artifacts\win" -Directory -EA SilentlyContinue | Where-Object Name -like 'kamion-*' | Sort-Object LastWriteTime -Descending
$wins | Select-Object -Skip 2 | ForEach-Object { Del $_.FullName 'stary build' }
Get-ChildItem "$Repo\artifacts\win\runs" -Directory -EA SilentlyContinue | Where-Object LastWriteTime -lt (Get-Date).AddDays(-7) | ForEach-Object { Del $_.FullName 'run > 7 dni' }

# 3) Artefakty zadań: foldery najwyżej 1 poziom w artifacts, nieruszane od 10 dni (rendery visual-qa, łańcuchy)
$keep = 'live', 'logs', 'locks', 'win', '_wt', 'tests', 'pc-budget-s23'
Get-ChildItem "$Repo\artifacts" -Directory -EA SilentlyContinue | Where-Object { $keep -notcontains $_.Name } | ForEach-Object {
    $newest = Get-ChildItem $_.FullName -Recurse -File -Force -EA SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($newest -and $newest.LastWriteTime -lt (Get-Date).AddDays(-10)) { Del $_.FullName "artefakt nieruszany od $($newest.LastWriteTime.ToString('yyyy-MM-dd'))" }
}

# 4) Pliki tymczasowe Claude i Unity (> 7 dni)
foreach ($t in "$env:TEMP\claude", "$env:LOCALAPPDATA\Temp\Unity", "$env:LOCALAPPDATA\Unity\cache") {
    Get-ChildItem $t -Directory -EA SilentlyContinue | Where-Object LastWriteTime -lt (Get-Date).AddDays(-7) | ForEach-Object { Del $_.FullName 'tmp > 7 dni' }
}

# 5) Cache uv: tylko nieużywane wpisy (bezpieczne przy działających venvach)
if (-not $WhatIf) { uv cache prune 2>&1 | Select-Object -Last 1 | ForEach-Object { L "uv: $_" } }

$after = Free
L "DONE free=$after GB (+$($after - $before))"
if ($after -lt 150) { L "ALARM: wolne < 150 GB — zgłoś właścicielowi i usuń worktree/artefakty ręcznie (lista: git worktree list)" ; exit 2 }
exit 0
