# Pakuje do ZIP wszystko z Kamiona, czego nie ma w gicie, na przenosiny na nowy komputer (s23, 17.11.2026).
# Użycie: pwsh scripts/pack-migration.ps1 [-Out C:\KAMION-PRZENOSINY] [-SkipDerived] [-SkipGugik]
# Wynik: <Out>\kamion-*.zip (bez kompresji — PNG/GLB i tak są skompresowane) + MANIFEST.txt z rozmiarami i SHA-256.
# Junctiony w worktree NIE są pakowane (pakujemy tylko main: Data\raw\*).
param(
    [string]$Out = 'C:\KAMION-PRZENOSINY',
    [switch]$SkipDerived,
    [switch]$SkipGugik
)
$ErrorActionPreference = 'Stop'
$Repo = (Resolve-Path "$PSScriptRoot/..").Path
New-Item -ItemType Directory -Force $Out | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
$log = Join-Path $Out 'MANIFEST.txt'
"Kamion — paczki przenosin, $(Get-Date -Format s), repo $Repo, main $(git -C $Repo rev-parse --short HEAD)" | Set-Content $log

function Pack([string]$name, [string[]]$sources) {
    $zip = Join-Path $Out "kamion-$name.zip"
    if (Test-Path $zip) { Remove-Item $zip }
    $stage = Join-Path $env:TEMP "kamion-pack-$name"
    if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
    New-Item -ItemType Directory -Force $stage | Out-Null
    foreach ($s in $sources) {
        if (-not (Test-Path $s.Split('|')[0])) { "  BRAK: $s" | Add-Content $log; continue }
        $src, $rel = $s.Split('|')
        $dst = Join-Path $stage $rel
        # /XJ = nie wchodź w junctiony; kopia, żeby zip miał ścieżki względne od korzenia
        robocopy $src $dst /E /XJ /NFL /NDL /NJH /NJS /R:1 /W:1 | Out-Null
    }
    [IO.Compression.ZipFile]::CreateFromDirectory($stage, $zip, [IO.Compression.CompressionLevel]::NoCompression, $false)
    Remove-Item $stage -Recurse -Force
    $h = (Get-FileHash $zip -Algorithm SHA256).Hash
    "{0}  {1:N2} GB  {2}" -f (Split-Path $zip -Leaf), ((Get-Item $zip).Length / 1GB), $h | Add-Content $log
    Write-Host "OK $zip"
}

$raw = Join-Path $Repo 'Data\raw'
$mem = 'C:\Users\matma\.claude\projects\C--Users-matma-Documents-Claude-kamion\memory'

# 1) Małe i niezastąpione: zdjęcia właściciela, produkty Fab, Mapillary, OSM, CC0 + pamięć sesji + pliki lokalne repo
Pack 'A-dane-male' @(
    "$raw\refs|Data\raw\refs",
    "$raw\fab|Data\raw\fab",
    "$raw\mapillary|Data\raw\mapillary",
    "$raw\osm|Data\raw\osm",
    "$raw\cc0|Data\raw\cc0",
    "$mem|_pamiec-claude\memory"
)
# 2) GUGiK (ortofoto, NMT, BDOT) — da się pobrać ponownie, ale to wiele godzin
if (-not $SkipGugik) { Pack 'B-gugik' @("$raw\gugik|Data\raw\gugik") }
# 3) Zbudowany świat (GLB kafli) — da się odbudować generatorem (~kilkanaście godzin), więc pakujemy
if (-not $SkipDerived) { Pack 'C-derived' @("$raw\derived|Data\raw\derived") }
# 4) Ostatni exe — najnowszy build z main\artifacts\win i z worktree buildowych
$exe = @(Get-ChildItem "$Repo\artifacts\win", "$Repo\.claude\worktrees\win-build*\artifacts\win" -Directory -EA SilentlyContinue | Where-Object Name -like 'kamion-*') | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($exe) { Pack 'D-ostatni-exe' @("$($exe.FullName)|artifacts\win\$($exe.Name)") }
# 5) Dowody agentów z gałęzi w toku (rendery, logi) — artifacts\ każdego worktree, bez Library
$e = @()
foreach ($w in Get-ChildItem "$Repo\.claude\worktrees" -Directory -EA SilentlyContinue) {
    if (Test-Path "$($w.FullName)\artifacts") { $e += "$($w.FullName)\artifacts|worktrees\$($w.Name)\artifacts" }
    if (Test-Path "$($w.FullName)\STATUS.md") { $e += "$($w.FullName)|worktrees\$($w.Name)\_status-only" }
}
if ($e) { Pack 'E-artefakty-agentow' ($e | Where-Object { $_ -notlike '*_status-only' }) }

Copy-Item "$Repo\docs\owner\NOWY-PC-KAMION.md" $Out -Force
"GOTOWE $(Get-Date -Format s)" | Add-Content $log
Get-Content $log
