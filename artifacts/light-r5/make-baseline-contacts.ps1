param([ValidateSet('baseline','final-native')][string]$Series='baseline')
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$limits=@('-limit','thread','1','-limit','memory','64MiB','-limit','map','64MiB')
$index=@()
foreach($tier in 'Low','High'){foreach($preset in 'clear','overcast','night'){
    $inputFolder="$PSScriptRoot/$Series/$tier-$preset"
    $outputFolder="$PSScriptRoot/review/$Series/$tier-$preset"
    $thumbFolder="$outputFolder/thumbs"
    New-Item -ItemType Directory -Force $thumbFolder|Out-Null
    $files=@(Get-ChildItem -LiteralPath $inputFolder -Filter '*.png'|Sort-Object Name)
    if($files.Count -ne 109){throw "Unexpected baseline count $($files.Count)"}
    $thumbs=@()
    foreach($file in $files){
        $thumb="$thumbFolder/$($file.BaseName).jpg"
        & magick @limits $file.FullName -thumbnail '480x222!' -quality 92 $thumb
        if($LASTEXITCODE){throw 'Thumbnail failed'}
        $thumbs+=$thumb
    }
    for($start=0;$start -lt $files.Count;$start+=20){
        $end=[Math]::Min($start+19,$files.Count-1)
        $sheet="$outputFolder/sheet-$('{0:D2}' -f ([int]($start/20)+1)).jpg"
        & magick montage @limits -label '%f' $thumbs[$start..$end] -tile 4x5 -geometry +2+2 -pointsize 13 -background '#dddddd' $sheet
        if($LASTEXITCODE){throw 'Sheet failed'}
        $index+=@{tier=$tier;preset=$preset;sheet=$sheet;cameras=@($files[$start..$end].BaseName)}
    }
    Write-Output "Contact sheets ready: $tier-$preset ($($files.Count) images)"
}}
$index|ConvertTo-Json -Depth 5|Set-Content "$PSScriptRoot/review/$Series/index.json" -Encoding utf8

