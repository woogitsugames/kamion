param([string]$Jobs='artifacts/light-r6/baseline.json')
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')); Set-Location $repo
. "$repo/scripts/env.ps1"
$spec=Get-Content -LiteralPath $Jobs -Raw|ConvertFrom-Json
$series=[IO.Path]::GetFileNameWithoutExtension($Jobs)
$limits=@('-limit','thread','1','-limit','memory','64MiB','-limit','map','64MiB')
$index=@()
foreach($job in $spec.jobs){
    $inputFolder=[IO.Path]::GetFullPath($job.output,$repo)
    if(-not $inputFolder.StartsWith($PSScriptRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){
        throw 'Input must be inside this round artifacts'
    }
    $files=@(Get-ChildItem -LiteralPath $inputFolder -Filter '*.png'|Where-Object Name -NotMatch '(_envcube|_mask)\.png$'|Sort-Object Name)
    if($files.Count -ne [int]$spec.expectedCamerasPerJob){throw "Unexpected image count $($files.Count): $inputFolder"}
    $label=$inputFolder.Substring($PSScriptRoot.Length+1).Replace('\','_').Replace('/','_')
    $outputFolder=Join-Path $PSScriptRoot "review/$series/$label"
    $thumbFolder=Join-Path $outputFolder 'thumbs'
    New-Item -ItemType Directory -Force $thumbFolder|Out-Null
    $thumbs=@();$sourceProof=@()
    foreach($file in $files){
        $thumb=Join-Path $thumbFolder "$($file.BaseName).jpg"
        & magick @limits $file.FullName -thumbnail '480x222!' -quality 92 $thumb
        if($LASTEXITCODE){throw "Thumbnail failed: $($file.Name)"}
        $thumbs+=$thumb
        $sourceProof+=@{id=$file.BaseName;path=$file.FullName;sha=(Get-FileHash -LiteralPath $file.FullName).Hash}
    }
    for($start=0;$start -lt $files.Count;$start+=20){
        $end=[Math]::Min($start+19,$files.Count-1)
        $sheet=Join-Path $outputFolder ("sheet-{0:D2}.jpg" -f ([int]($start/20)+1))
        & magick montage @limits -label '%f' $thumbs[$start..$end] -tile 4x5 -geometry +2+2 -pointsize 13 -background '#dddddd' $sheet
        if($LASTEXITCODE){throw 'Contact sheet failed'}
        $index+=@{tier=$job.tier;preset=$job.lighting;jobOutput=$job.output;sheet=$sheet;sha=(Get-FileHash -LiteralPath $sheet).Hash;cameras=@($sourceProof[$start..$end])}
    }
    Write-Output "Contact sheets ready: $($job.output), $($files.Count) images"
}
$index|ConvertTo-Json -Depth 7|Set-Content "$PSScriptRoot/review/$series/index.json" -Encoding utf8
Write-Output "Prepared $($index.Count) sheets. They still require direct visual review."
