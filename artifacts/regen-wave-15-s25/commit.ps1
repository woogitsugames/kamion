[CmdletBinding(DefaultParameterSetName='Tiles')]
param(
    [Parameter(ParameterSetName='Tiles')][string[]]$Tile,
    [Parameter(Mandatory, ParameterSetName='Sources')][switch]$Sources,
    [Parameter(Mandatory, ParameterSetName='Final')][switch]$Final
)

. "$PSScriptRoot/common.ps1"
Initialize-WaveRuntime
$lock = Enter-WaveLock 'git'
try {
    if (git diff --cached --name-only) { throw 'Indeks Git zawiera zmiany. Uporządkuj je przed commitem fali.' }
    $paths = @()
    if ($Sources) {
        if (-not (Test-Path -LiteralPath "$stateDir/sources.done")) { throw 'Najpierw uruchom prepare.ps1.' }
        $paths = $sourcePaths
        $label = 'schemat 2 źródeł streetscape i linie OSM'
        $next = 'pwsh -NoProfile -File artifacts/regen-wave-15-s25/chain.ps1 -Chain A'
    }
    elseif ($Final) {
        if (-not (Test-Path -LiteralPath "$stateDir/final.checked")) { throw 'Najpierw uruchom final.ps1.' }
        $streaming = 'game/Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming'
        $paths += "$streaming/route_links.json", "$streaming/tile_graph.json",
                  'game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json'
        $label = 'streaming i katalog regionów'
        $next = 'git log -5 --oneline'
    }
    else {
        if ($Tile | Where-Object { $_ -cnotin $queue.tile }) { throw 'Kafel poza kolejką.' }
        $doneTiles = @($queue.tile | Where-Object {
            (-not $Tile -or $_ -cin $Tile) -and (Test-Path -LiteralPath "$stateDir/tiles/$_.done")
        })
        foreach ($id in $doneTiles) {
            $nav = "game/Assets/_Project/UI/Resources/CabDisplay/Nav/$id"
            $paths += "Data/Regions/$id/generated", "Data/Regions/$id/route_start.json",
                      "Data/SourceManifests/$id-far-field.manifest.json",
                      "$nav.bytes", "$nav.bytes.meta", "${nav}_route.bytes", "${nav}_route.bytes.meta"
        }
        $label = "kafle gotowe ($($doneTiles.Count))"
        $next = 'pwsh -NoProfile -File artifacts/regen-wave-15-s25/final.ps1'
    }
    $changed = @($paths | Where-Object { git status --porcelain -- $_ })
    if (-not $changed.Count) { Write-Host "Brak zmian do zapisania ($label)."; return }
    if ((git diff --name-only -- STATUS.md)) { throw 'STATUS.md ma lokalne zmiany.' }
    Add-Content -LiteralPath 'STATUS.md' -Value ('- {0} {1} — {2}. Następny krok: `{3}`' -f
        (Get-Date -Format s), $waveName, $label, $next)
    git add -- @changed STATUS.md
    if ($LASTEXITCODE) { throw 'git add nie powiódł się.' }
    git commit -m "wip(${waveName}): $label"
    if ($LASTEXITCODE) { throw 'git commit nie powiódł się.' }
}
finally { $lock.Dispose() }
