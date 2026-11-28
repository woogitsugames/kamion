param([Parameter(Mandatory)][ValidateSet('before','after')][string]$Phase)

. "$PSScriptRoot/common.ps1"
Initialize-WaveRuntime
$views = @(
    @{ Tile = 'dk65-04'; Neighbour = 'dk65-05'; Camera = 'top_szkolna' },
    @{ Tile = 'bialystok-mickiewicza'; Camera = 'wave15-mickiewicza-przewody'; Gate3 = "$waveDir/mickiewicza-cameras.json" },
    @{ Tile = 'bialystok-mickiewicza'; Neighbour = 'bialystok-bojary'; Camera = 'dk19_piastowska_seam_n'; Id = 'bojary-mickiewicza' },
    @{ Tile = 'dk65-monki-01'; Neighbour = 'dk65-monki-02'; Camera = 'dk65_west_edge_in'; Id = 'dk65-monki-01-02' },
    @{ Tile = 's8-04'; Neighbour = 's8-05'; Camera = 'route_s1980'; Id = 's8-04-05' },
    @{ Tile = 'dk65-01'; Neighbour = 'dk8-s8-jeroniki'; Camera = 's8_corner_eye,s8_corner_top'; Id = 'dk65-01-jeroniki' },
    @{ Tile = 'tykocin'; Camera = 'look_tykocin_czarniecki,czarniecki_figure_0320b,czarniecki_pedestal_0320b' },
    @{ Tile = 'bialystok-industrial-c' }
)
$imported = [System.Collections.Generic.HashSet[string]]::new()
foreach ($view in $views) {
    $tile = $view.Tile
    $viewId = if ($view.Id) { $view.Id } else { $tile }
    $sceneTiles = @($tile)
    if ($view.Neighbour) { $sceneTiles += $view.Neighbour }
    if ($Phase -eq 'after') {
        foreach ($sceneTile in $sceneTiles) {
            if (-not (Test-Path -LiteralPath "$stateDir/tiles/$sceneTile.done")) {
                throw "Brak ukończonego kafla $sceneTile."
            }
        }
    }
    $log = "$evidenceDir/logs/vqa-$Phase-$viewId.log"
    $scene = if ($tile -eq 'bialystok-industrial-c') { 'WorldC_High' } else { "World_${tile}_High" }
    $neighbours = if ($view.Neighbour) { $view.Neighbour } else { 'none' }
    $cameraArgs = @()
    if ($view.Camera) { $cameraArgs += '-Cameras', $view.Camera }
    if ($view.Gate3) { $cameraArgs += '-Gate3', $view.Gate3 }
    Invoke-WaveUnity "$waveName-vqa" $log {
        if ($Phase -eq 'before') {
            foreach ($sceneTile in $sceneTiles) {
                if ($imported.Add($sceneTile)) { Invoke-WaveImport $sceneTile $log }
            }
        }
        foreach ($lighting in @('clear','overcast')) {
            $destination = "$evidenceDir/vqa/$Phase/$viewId/High-$lighting"
            $started = [DateTime]::UtcNow
            Invoke-WaveStep "visual-qa $lighting" 'pwsh' (@('-NoProfile', '-File', 'scripts/visual-qa.ps1', '-Scene', $scene,
                '-BuildTarget', 'Win64', '-Tier', 'High', '-Pc', '-Width', '1920', '-Height', '1080',
                '-Neighbours', $neighbours, '-Wires', 'on', '-Lighting', $lighting, '-OutputDir', $destination) + $cameraArgs) $log
            $fresh = @(Get-ChildItem -LiteralPath $destination -Filter '*.png' -File |
                Where-Object LastWriteTimeUtc -ge $started)
            $missing = @($view.Camera -split ',' | Where-Object {
                $_ -and ($_ -replace '_','-') -notin ($fresh.BaseName -replace '_','-')
            })
            if (-not $fresh.Count -or $missing.Count) {
                throw "Visual-QA nie zapisał oczekiwanego PNG w $destination."
            }
        }
    }
}
