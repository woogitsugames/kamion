param([string]$Series='native-grade-lab-v5')
$ErrorActionPreference='Stop'
$root=Join-Path $PSScriptRoot $Series
$out=Join-Path $PSScriptRoot "review/$Series"
New-Item -ItemType Directory -Force "$out/thumbs"|Out-Null
$limits=@('-limit','thread','1','-limit','memory','64MiB','-limit','map','64MiB')
foreach($preset in 'Clear','Overcast','LowSun','Dusk','Night'){
    $thumbs=@()
    foreach($suffix in 'High-reference','High-HDR-intermediate','High-legacy-ARGB32','Low-baseline','Low-native32','Low-shared-native32','capture-reference','capture-native-bypass'){
        $thumb="$out/thumbs/$preset-$suffix.jpg"
        & magick @limits "$root/$preset-$suffix.png" -resize '512x384!' -background '#dddddd' -fill black -gravity south -splice 0x24 -pointsize 18 -annotate +0+3 $suffix -quality 96 $thumb
        if($LASTEXITCODE){throw 'Thumbnail failed'}
        $thumbs+=$thumb
    }
    & magick montage @limits @thumbs -tile 2x4 -geometry +2+2 "$out/$preset-holdout.jpg"
    if($LASTEXITCODE){throw 'Montage failed'}
    $thumbs=@()
    foreach($suffix in 'High-reference','High-legacy-ARGB32','High-HDR-intermediate','Low-baseline','Low-native32'){
        $thumb="$out/thumbs/$preset-gradient-$suffix.jpg"
        & magick @limits "$root/$preset-gradient-$suffix.png" -background '#dddddd' -fill black -gravity south -splice 0x24 -pointsize 18 -annotate +0+3 $suffix -quality 96 $thumb
        if($LASTEXITCODE){throw 'Gradient thumbnail failed'}
        $thumbs+=$thumb
    }
    & magick montage @limits @thumbs -tile 1x5 -geometry +2+2 "$out/$preset-gradients.jpg"
    if($LASTEXITCODE){throw 'Gradient montage failed'}
    Write-Output "Contacts ready: $preset"
}
