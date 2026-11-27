param([Parameter(Mandatory)][ValidateSet('before','after')][string]$Phase)

. "$PSScriptRoot/common.ps1"
Initialize-WaveRuntime
$views = @(
    @{ Tile = 'dk65-04'; Neighbour = 'dk65-05'; Camera = 'top_szkolna' },
    @{ Tile = 'bialystok-mickiewicza'; Camera = 'wave15-mickiewicza-przewody'; Gate3 = "$waveDir/mickiewicza-cameras.json" },
    @{ Tile = 'tykocin'; Camera = 'look_tykocin_czarniecki' },
    @{ Tile = 'bialystok-industrial-c' }
)
foreach ($view in $views) {
    $tile = $view.Tile
    $sceneTiles = @($tile)
    if ($view.Neighbour) { $sceneTiles += $view.Neighbour }
    if ($Phase -eq 'after') {
        foreach ($sceneTile in $sceneTiles) {
            if (-not (Test-Path -LiteralPath "$stateDir/tiles/$sceneTile.done")) {
                throw "Brak ukończonego kafla $sceneTile."
            }
        }
    }
    $log = "$evidenceDir/logs/vqa-$Phase-$tile.log"
    $scene = if ($tile -eq 'bialystok-industrial-c') { 'WorldC_High' } else { "World_${tile}_High" }
    $neighbours = if ($view.Neighbour) { $view.Neighbour } else { 'none' }
    $cameraArgs = @()
    if ($view.Camera) { $cameraArgs += '-Cameras', $view.Camera }
    if ($view.Gate3) { $cameraArgs += '-Gate3', $view.Gate3 }
    Invoke-WaveUnity "$waveName-vqa" $log {
        if ($Phase -eq 'before') {
            foreach ($sceneTile in $sceneTiles) { Invoke-WaveImport $sceneTile $log }
        }
        foreach ($lighting in @('clear','overcast')) {
            $destination = "$evidenceDir/vqa/$Phase/$tile/High-$lighting"
            $started = [DateTime]::UtcNow
            Invoke-WaveStep "visual-qa $lighting" 'pwsh' (@('-NoProfile', '-File', 'scripts/visual-qa.ps1', '-Scene', $scene,
                '-BuildTarget', 'Win64', '-Tier', 'High', '-Pc', '-Width', '1920', '-Height', '1080',
                '-Neighbours', $neighbours, '-Wires', 'on', '-Lighting', $lighting, '-OutputDir', $destination) + $cameraArgs) $log
            $fresh = @(Get-ChildItem -LiteralPath $destination -Filter '*.png' -File |
                Where-Object LastWriteTimeUtc -ge $started)
            if (-not $fresh.Count -or ($view.Camera -and ($view.Camera -replace '_','-') -notin ($fresh.BaseName -replace '_','-'))) {
                throw "Visual-QA nie zapisał oczekiwanego PNG w $destination."
            }
        }
    }
}
