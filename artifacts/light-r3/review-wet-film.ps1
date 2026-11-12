$ErrorActionPreference = 'Stop'
$jobs = (Get-Content "$PSScriptRoot/wet-film.json" -Raw | ConvertFrom-Json).jobs
foreach ($tier in @('Low','High')) {
    foreach ($id in $jobs[0].cameras.Split(',')) {
        $args = @('-limit','thread','1','-limit','memory','64MiB','-limit','map','64MiB')
        foreach ($puddles in @(0.3,0.08)) {
            $args += '('
            foreach ($floor in @(0.52,0.35,0.2)) {
                $job = $jobs | Where-Object { $_.tier -eq $tier -and $_.wetFilmSmoothness -eq $floor -and $_.puddleShare -eq $puddles }
                $probe = (Get-Content (Join-Path $job.output 'lamp-probes.json') -Raw | ConvertFrom-Json).cameras | Where-Object camera -eq $id
                if ($null -eq $probe -or [Math]::Abs($probe.actualWetFilmSmoothness-$floor) -gt 0.0001 -or [Math]::Abs($probe.actualPuddleShare-$puddles) -gt 0.0001) { throw 'actual film/puddle state mismatch' }
                $args += @('(', (Join-Path $job.output "$id.png"), '-resize','318x179',
                    '-background','#202020','-gravity','south','-splice','0x24','-fill','white','-pointsize','11','-annotate','0',
                    "$tier film$floor puddles$puddles / $id", ')')
            }
            $args += @('+append',')')
        }
        $args += @('-append', "$PSScriptRoot/native-review/wet-film-$tier-$id.jpg")
        & magick @args
        if ($LASTEXITCODE) { throw 'contact failed' }
    }
}
