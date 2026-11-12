$ErrorActionPreference='Stop'
$root=$PSScriptRoot;$series="$root/tone-native-world";$out="$root/review/cab-roi"
New-Item -ItemType Directory -Force "$out/crops"|Out-Null
$limits=@('-limit','thread','1','-limit','memory','64MiB','-limit','map','64MiB')
# Manually selected and visually checked native2340x1080 image coordinates. Rectangles, not segmentation.
$views=@(
    @{camera='cab-driver';regions=@(@{name='sky-through-windscreen';rect='650x150+600+25'},@{name='asphalt-through-windscreen';rect='250x120+1050+600'},@{name='paving-through-windscreen';rect='400x180+1800+560'},@{name='opaque-dash';rect='500x100+1550+930'})},
    @{camera='cab-dash';regions=@(@{name='asphalt-through-windscreen';rect='120x150+850+270'},@{name='paving-through-windscreen';rect='500x150+1550+230'},@{name='opaque-dash';rect='320x100+1570+600'},@{name='opaque-wheel';rect='200x100+800+800'})}
)
function Mean($file){$v=& magick @limits $file -alpha off -format '%[fx:mean*255]' info:;if($LASTEXITCODE){throw 'Mean failed'};return [double]::Parse($v,[Globalization.CultureInfo]::InvariantCulture)}
function Diff($a,$b){$v=& magick @limits $a $b -alpha off -compose difference -composite -format '%[fx:mean*255] %[fx:maxima*255]' info:;if($LASTEXITCODE){throw 'Diff failed'};$n=$v.Split(' ');return @{mean=[double]::Parse($n[0],[Globalization.CultureInfo]::InvariantCulture);max=[double]::Parse($n[1],[Globalization.CultureInfo]::InvariantCulture)}}
$entries=@();$sources=@()
foreach($preset in 'clear','overcast','night'){foreach($view in $views){
    $thumbs=@();$id=$view.camera
    foreach($region in $view.regions){
        $crops=@{};$means=@{}
        foreach($variant in @(@{name='High-HDR';folder="High-HDR-$preset"},@{name='Low-base';folder="Low-$preset"},@{name='Low-native';folder="Low-$preset-lut32"})){
            $source="$series/$($variant.folder)/$id.png";$crop="$out/crops/$preset-$id-$($region.name)-$($variant.name).png"
            & magick @limits $source -gravity northwest -crop $region.rect +repage -alpha off $crop
            if($LASTEXITCODE){throw 'Crop failed'}
            $crops[$variant.name]=$crop;$means[$variant.name]=Mean $crop
            $thumb="$out/crops/$preset-$id-$($region.name)-$($variant.name).jpg"
            & magick @limits $crop -resize '500x180' -background '#dddddd' -gravity center -extent '500x180' -gravity south -splice '0x24' -fill black -pointsize 13 -annotate +0+3 "$($region.name) | $($variant.name)" -quality 95 $thumb
            if($LASTEXITCODE){throw 'Thumbnail failed'};$thumbs+=$thumb
            $sources+=@{file=$source;sha256=(Get-FileHash -LiteralPath $source).Hash}
        }
        $entries+=@{preset=$preset;camera=$id;region=$region.name;rect=$region.rect;meanRgbCodes=$means;baselineVsHdr=(Diff $crops['Low-base'] $crops['High-HDR']);nativeVsHdr=(Diff $crops['Low-native'] $crops['High-HDR'])}
    }
    & magick montage @limits @thumbs -tile 3x4 -geometry +2+2 "$out/$preset-$id.jpg"
    if($LASTEXITCODE){throw 'ROI sheet failed'}
}}
@{scope='Manual rectangular ROIs of existing twelve-camera ablation, not material/glass segmentation or photometric calibration. Through-windscreen regions include glass composition; opaque regions still have tier/shadow/geometry differences.';entries=$entries;sources=@($sources|Sort-Object file -Unique)}|ConvertTo-Json -Depth 9|Set-Content "$root/cab-roi-comparison.json" -Encoding utf8
$entries|Where-Object preset -eq 'overcast'|ForEach-Object {[pscustomobject]@{camera=$_.camera;region=$_.region;before=$_.baselineVsHdr.mean;after=$_.nativeVsHdr.mean;high=$_.meanRgbCodes['High-HDR'];native=$_.meanRgbCodes['Low-native']}}
