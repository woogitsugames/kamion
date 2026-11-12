$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$jobs = (Get-Content "$PSScriptRoot/baseline.json" -Raw | ConvertFrom-Json).jobs
$out = "$PSScriptRoot/native-review"
New-Item -ItemType Directory -Force $out | Out-Null
$inventory = @()
foreach ($tier in @('Low','High')) {
    $wetJobs = @($jobs | Where-Object { $_.tier -eq $tier -and $_.lighting -eq 'overcast' })
    $ids = @($wetJobs | ForEach-Object { $_.cameras.Split(',') } | Select-Object -Unique)
    foreach ($id in $ids) {
        $args = @('-limit','thread','1','-limit','memory','64MiB','-limit','map','64MiB')
        $inputs = @()
        foreach ($job in @($wetJobs | Where-Object { $_.cameras.Split(',') -contains $id } | Sort-Object expectedWetness)) {
            $png = Join-Path $job.output "$id.png"
            if (-not (Test-Path -LiteralPath $png)) { throw "Missing reviewed baseline input $png" }
            $probe = (Get-Content (Join-Path $job.output 'lamp-probes.json') -Raw | ConvertFrom-Json).cameras | Where-Object camera -eq $id
            if ($null -eq $probe -or [Math]::Abs($probe.actualWetness-$job.expectedWetness) -gt 0.0001) { throw "Wetness evidence mismatch $png" }
            $label = "$tier wet=$($probe.actualWetness) / $id"
            $args += @('(', $png, '-resize','318x179','-background','#202020','-gravity','south','-splice','0x24','-fill','white','-pointsize','11','-annotate','0',$label,')')
            $inputs += @{png=$png;actualWetness=$probe.actualWetness;actualPuddleShare=$probe.actualPuddleShare}
        }
        if ($inputs.Count -ne 3) { throw "Expected all three wetness states for $tier/$id" }
        $contact = Join-Path $out "wet-$tier-$id.jpg"
        $args += @('+append',$contact)
        & magick @args
        if ($LASTEXITCODE) { throw "Contact failed $contact" }
        $inventory += @{contact=$contact;inputs=$inputs;scope='same camera and scene; native PNG comparisons; no calibrated photo metric'}
    }
    $clear = $jobs | Where-Object { $_.tier -eq $tier -and $_.lighting -eq 'clear' }
    $args = @('-limit','thread','1','-limit','memory','64MiB','-limit','map','64MiB')
    foreach ($id in $clear.cameras.Split(',')) {
        $png = Join-Path $clear.output "$id.png"
        if (-not (Test-Path -LiteralPath $png)) { throw "Missing fresh far-field input $png" }
        $args += @('(',$png,'-resize','478x269','-background','#202020','-gravity','south','-splice','0x24','-fill','white','-pointsize','11','-annotate','0',"$tier fresh main+light / $id",')')
    }
    $args += @('+append',(Join-Path $out "farfield-$tier.jpg"))
    & magick @args
    if ($LASTEXITCODE) { throw 'Far-field contact failed' }
}
$inventory | ConvertTo-Json -Depth 6 | Set-Content "$out/wet-inventory.json" -Encoding utf8
Write-Output "Prepared all 36 wetness captures and 4 far-field captures for visual review."
