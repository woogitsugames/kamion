param([string]$Series='tone-world-v3',[switch]$Native)
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$root="$PSScriptRoot/$Series";$out="$PSScriptRoot/review/$Series"
New-Item -ItemType Directory -Force "$out/thumbs"|Out-Null
$limits=@('-limit','thread','1','-limit','memory','64MiB','-limit','map','64MiB')
function ReadBudget([string]$path){
    $items=@{}
    foreach($line in Get-Content -LiteralPath $path){
        if($line -match '^(?<id>[^:]+): objects=(?<objects>\d+) drawsEst=(?<draws>\d+) shadowDrawsEst=(?<shadow>\d+) trisK=(?<tris>\d+)'){
            $items[$Matches.id]=@{objects=[int]$Matches.objects;draws=[int]$Matches.draws;shadow=[int]$Matches.shadow;triangles=[int]$Matches.tris*1000;instancedDraws=0;instancedTriangles=0;instances=0}
        }elseif($line -match '^\s+(?<id>\S+) instanced .*draws (?<draws>\d+), instances (?<instances>\d+), triangles (?<tris>\d+)k'){
            if(-not $items.ContainsKey($Matches.id)){throw 'Missing primary budget'}
            $items[$Matches.id].instancedDraws=[int]$Matches.draws;$items[$Matches.id].instances=[int]$Matches.instances;$items[$Matches.id].instancedTriangles=[int]$Matches.tris*1000
        }
    }
    return $items
}
function Difference([string]$a,[string]$b){
    $metric=& magick @limits $a $b -alpha off -compose difference -composite -format '%[fx:mean*255] %[fx:maxima*255]' info:
    if($LASTEXITCODE){throw 'Difference failed'}
    $v=$metric.Split(' ')
    return @{mean=[double]::Parse($v[0],[Globalization.CultureInfo]::InvariantCulture);max=[double]::Parse($v[1],[Globalization.CultureInfo]::InvariantCulture)}
}
$budget=@();$pixels=@();$cube=@();$sheets=@()
foreach($preset in 'clear','overcast','night'){
    $baseline="$root/Low-$preset";$candidate="$root/Low-$preset-lut32";$high="$root/High-$preset"
    $b=ReadBudget "$baseline/stats.txt";$a=ReadBudget "$candidate/stats.txt"
    if($a.Count -ne 12 -or $b.Count -ne 12){throw 'Expected12 route cameras'}
    $hdr="$root/High-HDR-$preset"
    $proof=Get-Content "$candidate/opaque-grade-proof.json" -Raw|ConvertFrom-Json
    if($proof.frames.Count -ne 12 -or @($proof.frames|Where-Object {$_.enabled -ne 1 -or $_.physicalCaptureBypass -ne 0}).Count){throw 'Incomplete actual LUT proof'}
    if($Native){$hp=Get-Content "$hdr/hdr-reference-proof.json" -Raw|ConvertFrom-Json;if($hp.frames.Count -ne 12 -or @($hp.frames|Where-Object {$_.colorBeforePostFormat -ne "R16G16B16A16_SFloat"}).Count){throw "Invalid actual HDR proof"}}
    $thumbs=@();$ids=@($a.Keys|Sort-Object)
    foreach($id in $ids){
        if(-not $b.ContainsKey($id)){throw 'Camera mismatch'}
        $x=$b[$id];$y=$a[$id]
        $draw=$y.draws+$y.shadow+$y.instancedDraws-$x.draws-$x.shadow-$x.instancedDraws
        $tri=100.0*($y.triangles+$y.instancedTriangles-$x.triangles-$x.instancedTriangles)/[Math]::Max(1,$x.triangles+$x.instancedTriangles)
        $budget+=@{preset=$preset;camera=$id;before=$x;after=$y;totalDrawDelta=$draw;totalTriangleDeltaPercent=$tri}
        $pixels+=@{preset=$preset;camera=$id;highVsBaseline=(Difference "$high/$id.png" "$baseline/$id.png");highVsCandidate=(Difference "$high/$id.png" "$candidate/$id.png")}
        if($Native){$pixels[-1].hdrVsBaseline=Difference "$hdr/$id.png" "$baseline/$id.png";$pixels[-1].hdrVsCandidate=Difference "$hdr/$id.png" "$candidate/$id.png";$pixels[-1].hdrVsLegacy=Difference "$hdr/$id.png" "$high/$id.png"}
        $cube+=@{preset=$preset;camera=$id;difference=(Difference "$baseline/${id}_envcube.png" "$candidate/${id}_envcube.png")}
        $variants=@(@{name='High legacy';path=$high},@{name='Low baseline';path=$baseline},@{name='Low LUT32';path=$candidate});if($Native){$variants=@(@{name='High HDR';path=$hdr})+$variants}
        foreach($variant in $variants){
            $thumb="$out/thumbs/$preset-$id-$($variant.name.Replace(' ','-')).jpg"
            & magick @limits "$($variant.path)/$id.png" -resize '780x360!' -background '#dddddd' -fill black -gravity south -splice 0x24 -pointsize 16 -annotate +0+3 "$id | $($variant.name)" -quality 94 $thumb
            if($LASTEXITCODE){throw 'Thumbnail failed'}
            $thumbs+=$thumb
        }
    }
    for($i=0;$i -lt 4;$i++){
        $sheet="$out/$preset-$($i+1).jpg"
        $columns=if($Native){4}else{3};$perSheet=$columns*3
        & magick montage @limits $thumbs[($i*$perSheet)..($i*$perSheet+$perSheet-1)] -tile "${columns}x3" -geometry +2+2 -background '#dddddd' $sheet
        if($LASTEXITCODE){throw 'Montage failed'}
        $sheets+=@{preset=$preset;sheet=$sheet;cameras=$ids[($i*3)..($i*3+2)]}
    }
    Write-Output "Compared ${preset}:12 camera triples and12 cube pairs"
}
@{scope='Low baseline versus LowLUT32, rounded CPU estimates before SRP, instances separately; no GPU claim';entries=$budget}|ConvertTo-Json -Depth 8|Set-Content "$root/budget-comparison.json" -Encoding utf8
@{scope='Whole-frame RGB code differences to High, affected by different tier geometry, shadows, render scale and alpha; not a photometric fit or acceptance gate';entries=$pixels}|ConvertTo-Json -Depth 8|Set-Content "$root/high-comparison.json" -Encoding utf8
@{scope='Static mip0 vehicle capture strips, Low before/after only';entries=$cube}|ConvertTo-Json -Depth 8|Set-Content "$root/capture-comparison.json" -Encoding utf8
$sheets|ConvertTo-Json -Depth 5|Set-Content "$out/index.json" -Encoding utf8
if(@($budget|Where-Object {$_.totalDrawDelta -gt 0 -or $_.totalTriangleDeltaPercent -gt 2}).Count){throw 'Budget regression'}
$budget|Group-Object totalDrawDelta,totalTriangleDeltaPercent|Select-Object Count,Name
$cube|ForEach-Object {$_.difference}|Measure-Object mean,max -Maximum


