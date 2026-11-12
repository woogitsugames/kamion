$ErrorActionPreference = 'Stop'
$template = (Get-Content "$PSScriptRoot/wet-local-v2.json" -Raw | ConvertFrom-Json).jobs
$jobs = @()
foreach ($tier in @('Low','High')) {
    foreach ($floor in @(0.52,0.35,0.2)) {
        foreach ($puddles in @(0.3,0.08)) {
            $job = $template | Where-Object { $_.tier -eq $tier -and $_.expectedWetness -eq 1 -and -not $_.wetLocalReflections }
            $job = $job | ConvertTo-Json -Depth 8 | ConvertFrom-Json
            $job.output = "artifacts/light-r3/wet-film/$tier-film$floor-puddles$puddles"
            $job.cameras = 'light-night-driver,light-wet-left,light-wet-right,r10_block_3,stretch-03,sbs-g3-a-cm92458760'
            $job | Add-Member overrideWetFilm $true
            $job | Add-Member wetFilmSmoothness $floor
            $job | Add-Member puddleShare $puddles
            $jobs += $job
        }
    }
}
@{jobs=$jobs} | ConvertTo-Json -Depth 8 | Set-Content "$PSScriptRoot/wet-film.json" -Encoding utf8
